"""Tests for the companion's right-click menu (no window needed)."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402
import pytest  # noqa: E402

from companion import MENU_CLOSE_DELAY, MENU_MIN_WIDTH, SIZE, Menu  # noqa: E402

ITEMS = [("feed", "Feed  (F)"), ("ghost", "Leave ghost mode  (G)"), ("quit", "Quit")]
DT = 1 / 60


@pytest.fixture(scope="module")
def font():
    pygame.font.init()
    return pygame.font.SysFont("segoeui,verdana,arial", 15)


def stay_for(menu, pos, seconds, near_pet=False):
    """Keep the cursor at `pos` for a while; return whether the menu is still open."""
    open_ = True
    for _ in range(round(seconds / DT)):
        open_ = menu.keep_open(pos, near_pet, DT)
        if not open_:
            break
    return open_


def test_menu_is_wide_enough_for_every_label(font):
    menu = Menu(ITEMS, (10, 10), SIZE, font)
    widest = max(font.size(label)[0] for _, label in ITEMS)
    for index in range(len(ITEMS)):
        assert menu.item_rect(index).width - 10 >= widest  # labels start 10 px in
    assert menu.rect.width >= MENU_MIN_WIDTH


def test_menu_stays_inside_the_window(font):
    menu = Menu(ITEMS, (SIZE[0] - 5, SIZE[1] - 5), SIZE, font)
    assert pygame.Rect((0, 0), SIZE).contains(menu.rect)


def test_stays_open_while_the_cursor_is_on_it(font):
    menu = Menu(ITEMS, (20, 20), SIZE, font)
    assert stay_for(menu, menu.rect.center, 5)


def test_stays_open_while_the_cursor_is_on_the_pet(font):
    menu = Menu(ITEMS, (20, 20), SIZE, font)
    assert stay_for(menu, (-500, -500), 5, near_pet=True)


def test_closes_once_the_cursor_leaves(font):
    menu = Menu(ITEMS, (20, 20), SIZE, font)
    assert not stay_for(menu, (-500, -500), MENU_CLOSE_DELAY + 0.1)


def test_a_quick_wobble_outside_does_not_close_it(font):
    menu = Menu(ITEMS, (20, 20), SIZE, font)
    assert stay_for(menu, (-500, -500), MENU_CLOSE_DELAY / 2)
    assert stay_for(menu, menu.rect.center, 0.1)        # back on the menu: timer resets
    assert stay_for(menu, (-500, -500), MENU_CLOSE_DELAY / 2)


def test_just_outside_the_edge_still_counts(font):
    menu = Menu(ITEMS, (20, 20), SIZE, font)
    assert stay_for(menu, (menu.rect.right + 5, menu.rect.centery), 5)
