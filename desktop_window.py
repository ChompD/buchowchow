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
"""

import sys

KEY_COLOR = (110, 82, 94)  # not used anywhere else in the palette


def supports_transparency():
    return sys.platform == "win32"


def _user32():
    """Windows' user32 library with the few functions we need, or None."""
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
    return user32


GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
LWA_COLORKEY = 0x00000001


def set_see_through(hwnd, color=KEY_COLOR):
    """Make `color` invisible and click-through in the window. Returns True if it worked."""
    user32 = _user32()
    if user32 is None or not hwnd:
        return False
    try:
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED)
        r, g, b = color
        colorref = r | (g << 8) | (b << 16)  # Windows stores colours as 0x00BBGGRR
        return bool(user32.SetLayeredWindowAttributes(hwnd, colorref, 0, LWA_COLORKEY))
    except OSError:
        return False


def clear_see_through(hwnd):
    """Turn the window back into a normal, solid window."""
    user32 = _user32()
    if user32 is None or not hwnd:
        return
    try:
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style & ~WS_EX_LAYERED)
    except OSError:
        pass


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
