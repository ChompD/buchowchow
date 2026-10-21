"""Tests for the wardrobe: items, unlocking, wearing, colours and saving outfits."""

import pytest

from pet import Pet, xp_for_next_level
from wardrobe import COLORS, ITEMS, SLOTS, Outfit, items_for, unlocked_between


# ---- The item list ----

def test_every_item_has_a_valid_slot_and_colour():
    for item in ITEMS.values():
        assert item.slot in SLOTS
        assert item.default_color in COLORS
        assert item.unlock_level >= 1


def test_every_slot_has_something_to_wear_at_level_1():
    for slot in SLOTS:
        assert any(item.unlock_level == 1 for item in items_for(slot))


def test_unlocked_between_finds_new_items():
    names = {item.key for item in unlocked_between(9, 10)}
    assert "crown" in names
    assert unlocked_between(10, 10) == []


# ---- Wearing things ----

def test_new_outfit_is_empty():
    outfit = Outfit()
    assert outfit.worn() == []
    assert all(outfit.item(slot) is None for slot in SLOTS)


def test_wear_puts_item_in_its_slot_with_default_colour():
    outfit = Outfit()
    assert outfit.wear("bow", level=1)
    assert outfit.item("head").key == "bow"
    assert outfit.color("head") == ITEMS["bow"].default_color


def test_one_item_per_slot():
    outfit = Outfit()
    outfit.wear("bow", 1)
    outfit.wear("flower", 1)
    assert outfit.item("head").key == "flower"
    assert not outfit.is_wearing("bow")


def test_slots_are_independent():
    outfit = Outfit()
    for key in ("bow", "glasses", "bell_collar", "sweater"):
        outfit.wear(key, 1)
    assert [slot for slot, _, _ in outfit.worn()] == list(SLOTS)


def test_locked_items_cannot_be_worn():
    outfit = Outfit()
    assert not outfit.wear("crown", level=9)
    assert outfit.item("head") is None
    assert outfit.wear("crown", level=10)


def test_unknown_items_are_refused():
    assert not Outfit().wear("jetpack", 99)


def test_take_off_empties_the_slot():
    outfit = Outfit()
    outfit.wear("bow", 1)
    outfit.take_off("head")
    outfit.take_off("face")  # nothing there: no error
    assert outfit.item("head") is None


# ---- Colours ----

def test_set_color():
    outfit = Outfit()
    outfit.wear("sweater", 1)
    assert outfit.set_color("body", "green")
    assert outfit.color("body") == "green"


def test_bad_colours_and_empty_slots_are_refused():
    outfit = Outfit()
    assert not outfit.set_color("body", "green")  # nothing worn
    outfit.wear("sweater", 1)
    assert not outfit.set_color("body", "plaid")
    assert outfit.color("body") == ITEMS["sweater"].default_color


def test_single_colour_items_cannot_be_recoloured():
    outfit = Outfit()
    outfit.wear("crown", 10, color="green")
    assert outfit.color("head") == ITEMS["crown"].default_color
    assert not outfit.set_color("head", "blue")


def test_swapping_items_keeps_the_colour():
    outfit = Outfit()
    outfit.wear("beanie", 3, color="green")
    outfit.wear("party_hat", 3)
    assert outfit.color("head") == "green"


# ---- Saving ----

def test_outfit_round_trip():
    outfit = Outfit()
    outfit.wear("party_hat", 5, "purple")
    outfit.wear("heart_shades", 6, "red")
    outfit.wear("scarf", 5, "blue")
    copy = Outfit.from_dict(outfit.to_dict(), level=6)
    assert copy.to_dict() == outfit.to_dict()


@pytest.mark.parametrize("data", [None, "bow", [], {"head": "bow"}, {"head": {"item": 42}},
                                  {"head": {"item": "sweater"}},  # wrong slot
                                  {"hat": {"item": "bow"}}])
def test_damaged_outfits_load_as_empty(data):
    assert Outfit.from_dict(data, level=10).worn() == []


def test_loading_skips_items_that_are_still_locked():
    outfit = Outfit.from_dict({"head": {"item": "crown"}, "face": {"item": "glasses"}}, level=1)
    assert outfit.item("head") is None
    assert outfit.item("face").key == "glasses"


def test_loading_fixes_bad_colours():
    outfit = Outfit.from_dict({"body": {"item": "sweater", "color": "plaid"}}, level=1)
    assert outfit.color("body") == ITEMS["sweater"].default_color


@pytest.mark.parametrize("stage, expected", [
    (0, set()), (1, {"bow"}), (2, {"bow", "bell_collar"}), (3, {"bell_collar", "crown"}),
])
def test_old_evolution_accessories(stage, expected):
    level = {0: 1, 1: 3, 2: 6, 3: 10}[stage]
    outfit = Outfit.for_stage(stage, level)
    assert {key for _, key, _ in outfit.worn()} == expected


# ---- With the pet ----

def test_new_pet_wears_nothing():
    assert Pet("Bean").outfit.worn() == []


def test_pet_outfit_is_saved_and_loaded():
    pet = Pet("Bean", level=4)
    pet.outfit.wear("sunglasses", pet.level)
    pet.outfit.wear("raincoat", pet.level, "green")
    copy = Pet.from_dict(pet.to_dict())
    assert copy.outfit.to_dict() == pet.outfit.to_dict()


def test_saves_from_before_the_wardrobe_keep_their_accessories():
    pet = Pet.from_dict({"name": "Chowchow", "level": 4})  # a Junior, which used to wear a bow
    assert pet.outfit.item("head").key == "bow"


def test_saves_with_an_empty_outfit_stay_empty():
    pet = Pet.from_dict({"name": "Chowchow", "level": 4, "outfit": {}})
    assert pet.outfit.worn() == []


def test_level_up_reports_unlocked_items():
    pet = Pet("Bean", level=1, hunger=80, xp=xp_for_next_level(1) - 1)
    result = pet.feed()
    assert pet.level == 2
    assert "Party hat" in result.unlocked
    assert "Bandana" in result.unlocked


def test_normal_actions_unlock_nothing():
    assert Pet("Bean", hunger=80).feed().unlocked == ()
