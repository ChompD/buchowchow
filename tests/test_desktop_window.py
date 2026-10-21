"""Tests for the companion window's placement helpers."""

import pytest

from desktop_window import (
    GHOST_ALPHA,
    ctrl_held,
    default_position,
    fits_on_screen,
    ghost_style,
    ground_y,
    set_click_through,
    snap_position,
    walk_bounds,
    work_area,
)

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


# ---- Taskbar and edges ----

AREA = (0, 0, 1920, 1032)   # a screen with a 48 px taskbar at the bottom
FEET_Y = 232                # where the paws are inside the companion window
HALF = 64                   # about half the pet's width


def test_work_area_is_a_sensible_rectangle():
    left, top, right, bottom = work_area((1920, 1080))
    assert right > left and bottom > top
    assert bottom <= 1080


def test_ground_puts_the_feet_on_the_taskbar():
    assert ground_y(AREA, FEET_Y) + FEET_Y == AREA[3]


def test_walk_bounds_keep_the_pet_on_screen():
    low, high = walk_bounds(AREA, WINDOW[0], HALF)
    assert low + WINDOW[0] / 2 - HALF == AREA[0]
    assert high + WINDOW[0] / 2 + HALF == AREA[2]


def test_dropping_near_the_taskbar_snaps_onto_it():
    floor = ground_y(AREA, FEET_Y)
    assert snap_position((800, floor - 30), WINDOW[0], HALF, FEET_Y, AREA) == (800, floor)


def test_dropping_near_a_side_snaps_against_it():
    low, high = walk_bounds(AREA, WINDOW[0], HALF)
    assert snap_position((low + 20, 300), WINDOW[0], HALF, FEET_Y, AREA)[0] == round(low)
    assert snap_position((high - 20, 300), WINDOW[0], HALF, FEET_Y, AREA)[0] == round(high)


def test_dropping_in_the_middle_stays_put():
    assert snap_position((800, 300), WINDOW[0], HALF, FEET_Y, AREA) == (800, 300)


# ---- Ghost mode ----

def test_normal_pet_is_solid_and_clickable():
    assert ghost_style(False, ctrl=False, over_pet=True) == (False, 255)
    assert ghost_style(False, ctrl=True, over_pet=True) == (False, 255)


@pytest.mark.parametrize("ctrl, over_pet", [(False, False), (False, True), (True, False)])
def test_ghost_is_faded_and_click_through(ctrl, over_pet):
    click_through, alpha = ghost_style(True, ctrl, over_pet)
    assert click_through
    assert 0 < alpha == GHOST_ALPHA < 255


def test_ctrl_over_a_ghost_makes_it_reachable():
    assert ghost_style(True, ctrl=True, over_pet=True) == (False, 255)


def test_window_helpers_ignore_a_missing_window():
    assert set_click_through(0, True) is False
    assert isinstance(ctrl_held(), bool)
