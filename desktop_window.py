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
