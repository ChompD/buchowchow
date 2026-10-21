"""Window helpers for companion mode.

See-through background (Windows only)
-------------------------------------
Windows can make every pixel of one exact colour (the "colour key") invisible,
and mouse clicks on those pixels go to whatever is behind the window. We fill
the companion window with KEY_COLOR, so only the pet and its speech bubble show.

KEY_COLOR is close to the pet's dark outline on purpose: the softened edges of
rotated or fading things blend toward this colour, and against the pet that
looks like outline rather than a coloured fringe.

On other systems the companion window still works, with a plain background.

Ghost mode (Windows only)
-------------------------
A "transparent" window style makes *every* pixel click-through, including the
pet. The whole window is also faded a little so you can tell. Holding Ctrl
while pointing at the pet turns it solid again, so it can always be clicked.
"""

import functools
import sys

KEY_COLOR = (110, 82, 94)  # not used anywhere else in the palette
GHOST_ALPHA = 170          # how solid a ghost pet looks (0 = invisible, 255 = solid)


def supports_transparency():
    return sys.platform == "win32"


@functools.lru_cache(maxsize=1)
def _user32():
    """Windows' user32 library with the few functions we need, or None (loaded once)."""
    if not supports_transparency():
        return None
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongW.restype = wintypes.LONG
    user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LONG]
    user32.SetWindowLongW.restype = wintypes.LONG
    user32.SetLayeredWindowAttributes.argtypes = [wintypes.HWND, wintypes.DWORD, wintypes.BYTE, wintypes.DWORD]
    user32.SetLayeredWindowAttributes.restype = wintypes.BOOL
    user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
    user32.GetAsyncKeyState.restype = ctypes.c_short
    return user32


GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
LWA_COLORKEY = 0x00000001
LWA_ALPHA = 0x00000002
VK_CONTROL = 0x11


def _change_style(hwnd, add=0, remove=0):
    user32 = _user32()
    if user32 is None or not hwnd:
        return False
    try:
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, (style | add) & ~remove)
        return True
    except OSError:
        return False


def set_see_through(hwnd, color=KEY_COLOR, alpha=255):
    """Make `color` invisible and click-through, and fade the rest to `alpha`. Returns True if it worked."""
    user32 = _user32()
    if not _change_style(hwnd, add=WS_EX_LAYERED):
        return False
    try:
        r, g, b = color
        colorref = r | (g << 8) | (b << 16)  # Windows stores colours as 0x00BBGGRR
        return bool(user32.SetLayeredWindowAttributes(hwnd, colorref, alpha, LWA_COLORKEY | LWA_ALPHA))
    except OSError:
        return False


def set_click_through(hwnd, on):
    """Let every click pass through the window (ghost mode), or stop doing that."""
    if on:
        return _change_style(hwnd, add=WS_EX_TRANSPARENT | WS_EX_LAYERED)
    return _change_style(hwnd, remove=WS_EX_TRANSPARENT)


def clear_see_through(hwnd):
    """Turn the window back into a normal, solid, clickable window."""
    _change_style(hwnd, remove=WS_EX_LAYERED | WS_EX_TRANSPARENT)


def ctrl_held():
    """True while Ctrl is held down, even if our window isn't focused."""
    user32 = _user32()
    if user32 is None:
        return False
    try:
        return bool(user32.GetAsyncKeyState(VK_CONTROL) & 0x8000)
    except OSError:
        return False


def ghost_style(ghost_on, ctrl, over_pet):
    """How the window should behave: (click_through, alpha).

    A ghost pet lets every click through and looks faded, except while you hold
    Ctrl and point at it: then it turns solid and clickable, so you can always
    reach it (for example to turn ghost mode off).
    """
    if ghost_on and not (ctrl and over_pet):
        return True, GHOST_ALPHA
    return False, 255


TASKBAR_GUESS = 48  # used when we can't ask Windows where the taskbar is


def work_area(desktop_size):
    """(left, top, right, bottom) of the main screen, not counting the taskbar."""
    if supports_transparency():
        try:
            import ctypes
            from ctypes import wintypes

            rect = wintypes.RECT()
            SPI_GETWORKAREA = 0x0030
            if ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0):
                if rect.right > rect.left and rect.bottom > rect.top:
                    return (rect.left, rect.top, rect.right, rect.bottom)
        except (AttributeError, OSError):
            pass
    width, height = desktop_size
    return (0, 0, width, height - TASKBAR_GUESS)


def ground_y(area, feet_y):
    """Window y that puts the pet's feet (at `feet_y` inside the window) on top of the taskbar."""
    return area[3] - feet_y


def walk_bounds(area, window_width, pet_half_width):
    """Smallest and largest window x that keep the pet's body on screen."""
    middle = window_width / 2
    return (area[0] - middle + pet_half_width, area[2] - middle - pet_half_width)


def snap_position(position, window_width, pet_half_width, feet_y, area, distance=50):
    """Snap a dropped pet flush against the taskbar or a screen side if it's close to one."""
    x, y = position
    floor = ground_y(area, feet_y)
    if abs(y - floor) <= distance:
        y = floor
    low, high = walk_bounds(area, window_width, pet_half_width)
    if abs(x - low) <= distance:
        x = low
    elif abs(x - high) <= distance:
        x = high
    return (round(x), round(y))


def default_position(window_size, desktop_size, margin=(40, 90)):
    """Bottom-right corner of the screen, above the taskbar."""
    return (desktop_size[0] - window_size[0] - margin[0],
            desktop_size[1] - window_size[1] - margin[1])


def fits_on_screen(position, window_size, desktop_size, visible=60):
    """True if at least `visible` pixels of the window would be on screen.

    Used when restoring a saved position, e.g. after unplugging a monitor.
    """
    x, y = position
    w, h = window_size
    dw, dh = desktop_size
    return (x + w >= visible and x <= dw - visible and
            y + h >= visible and y <= dh - visible)
