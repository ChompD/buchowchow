"""Tests for the companion window's placement helpers."""

import pytest

from desktop_window import default_position, fits_on_screen

DESKTOP = (1920, 1080)
WINDOW = (240, 280)


def test_default_position_is_bottom_right_and_fully_visible():
    x, y = default_position(WINDOW, DESKTOP)
    assert x > DESKTOP[0] / 2 and y > DESKTOP[1] / 2
    assert x + WINDOW[0] <= DESKTOP[0] and y + WINDOW[1] <= DESKTOP[1]


@pytest.mark.parametrize("pos", [(0, 0), (100, 200), (1680, 800), (-150, 500), (1850, 1000)])
def test_positions_partly_on_screen_are_kept(pos):
    assert fits_on_screen(pos, WINDOW, DESKTOP)


@pytest.mark.parametrize("pos", [(-500, 0), (3000, 500), (100, -400), (100, 1200), (-2000, -2000)])
def test_positions_off_screen_are_rejected(pos):
    assert not fits_on_screen(pos, WINDOW, DESKTOP)
