"""Tests for the pet's game rules (no window needed)."""

import pytest

import random

from messages import PERSONALITIES
from pet import (
    CUDDLE_COOLDOWN,
    CUDDLE_HAPPINESS,
    DEFAULT_NAME,
    FEED_XP,
    MAX_NAME_LENGTH,
    PLAY_ENERGY_COST,
    PLAY_XP,
    Pet,
    xp_for_next_level,
)


# ---- Creating a pet ----

def test_new_pet_has_sensible_defaults():
    pet = Pet("Bean")
    assert pet.name == "Bean"
    assert pet.level == 1
    assert pet.xp == 0
    for stat in (pet.hunger, pet.happiness, pet.energy):
        assert 0 <= stat <= 100


@pytest.mark.parametrize("raw, expected", [
    ("", DEFAULT_NAME),
    ("   ", DEFAULT_NAME),
    ("  Bean  ", "Bean"),
    ("Mr   Whiskers", "Mr Whiskers"),
    ("A" * 30, "A" * MAX_NAME_LENGTH),
])
def test_names_are_cleaned(raw, expected):
    assert Pet(raw).name == expected


def test_stats_are_clamped_on_creation():
    pet = Pet("Bean", hunger=-50, happiness=500, energy=101)
    assert pet.hunger == 0
    assert pet.happiness == 100
    assert pet.energy == 100


def test_extra_starting_xp_becomes_levels():
    pet = Pet("Bean", xp=xp_for_next_level(1) + 5)
    assert pet.level == 2
    assert pet.xp == 5


# ---- Feeding ----

def test_feed_reduces_hunger_and_gives_xp():
    pet = Pet("Bean", hunger=60)
    result = pet.feed()
    assert pet.hunger < 60
    assert result.xp_gained == FEED_XP
    assert pet.xp == FEED_XP


def test_feeding_a_full_pet_does_nothing():
    pet = Pet("Bean", hunger=5, happiness=50)
    result = pet.feed()
    assert result.xp_gained == 0
    assert pet.xp == 0
    assert pet.hunger == 5
    assert result.kind == "too_full"
    assert result.message


def test_hunger_never_goes_below_zero():
    pet = Pet("Bean", hunger=15)
    pet.feed()
    assert pet.hunger == 0


# ---- Playing ----

def test_play_raises_happiness_and_costs_energy():
    pet = Pet("Bean", happiness=40, energy=80, hunger=20)
    result = pet.play()
    assert pet.happiness > 40
    assert pet.energy == 80 - PLAY_ENERGY_COST
    assert pet.hunger > 20
    assert result.xp_gained == PLAY_XP


def test_tired_pet_refuses_to_play():
    pet = Pet("Bean", happiness=40, energy=PLAY_ENERGY_COST - 1)
    result = pet.play()
    assert result.xp_gained == 0
    assert pet.happiness == 40
    assert result.kind == "too_tired"
    assert result.message


def test_happiness_never_goes_above_100():
    pet = Pet("Bean", happiness=95, energy=100)
    pet.play()
    assert pet.happiness == 100


# ---- XP and levels ----

def test_xp_requirement_grows_each_level():
    assert xp_for_next_level(2) > xp_for_next_level(1)


def test_level_up_carries_over_extra_xp():
    pet = Pet("Bean")
    needed = pet.xp_needed
    gained = pet.add_xp(needed + 3)
    assert gained == 1
    assert pet.level == 2
    assert pet.xp == 3


def test_big_xp_gain_can_level_up_several_times():
    pet = Pet("Bean")
    total = xp_for_next_level(1) + xp_for_next_level(2) + xp_for_next_level(3)
    assert pet.add_xp(total) == 3
    assert pet.level == 4
    assert pet.xp == 0


def test_negative_or_zero_xp_is_ignored():
    pet = Pet("Bean")
    assert pet.add_xp(-10) == 0
    assert pet.add_xp(0) == 0
    assert pet.xp == 0


def test_action_reports_level_up():
    pet = Pet("Bean", hunger=80, xp=xp_for_next_level(1) - 1)
    result = pet.feed()
    assert result.levels_gained == 1
    assert result.kind == "fed"
    assert str(pet.level) in result.message


def test_xp_progress_is_a_fraction():
    pet = Pet("Bean", xp=xp_for_next_level(1) // 2)
    assert 0 <= pet.xp_progress < 1


# ---- Time passing ----

def test_update_changes_stats_over_time():
    pet = Pet("Bean", hunger=50, happiness=50, energy=50)
    pet.update(60)
    assert pet.hunger > 50
    assert pet.happiness < 50
    assert pet.energy > 50


def test_update_keeps_stats_in_range():
    pet = Pet("Bean")
    pet.update(100_000)
    assert pet.hunger == 100
    assert pet.happiness == 0
    assert pet.energy == 100


def test_negative_time_is_ignored():
    pet = Pet("Bean", hunger=50)
    pet.update(-5)
    assert pet.hunger == 50


# ---- Mood ----

@pytest.mark.parametrize("stats, mood", [
    (dict(hunger=80, happiness=90, energy=90), "hungry"),   # hunger wins over everything
    (dict(hunger=20, happiness=90, energy=10), "tired"),
    (dict(hunger=20, happiness=10, energy=90), "sad"),
    (dict(hunger=20, happiness=90, energy=90), "happy"),
    (dict(hunger=20, happiness=50, energy=90), "content"),
])
def test_mood_follows_stats(stats, mood):
    pet = Pet("Bean", **stats)
    assert pet.mood == mood
    assert pet.name in pet.mood_text()


# ---- Personality ----

def test_new_pet_gets_a_valid_personality():
    assert Pet("Bean").personality in PERSONALITIES


def test_chosen_personality_is_kept():
    assert Pet("Bean", personality="foodie").personality == "foodie"


def test_unknown_personality_is_replaced_with_a_valid_one():
    assert Pet("Bean", personality="grumpy").personality in PERSONALITIES


def test_seeded_pets_are_repeatable():
    a = Pet("Bean", rng=random.Random(7))
    b = Pet("Bean", rng=random.Random(7))
    assert a.personality == b.personality
    assert a.feed().message == b.feed().message


@pytest.mark.parametrize("personality", PERSONALITIES)
@pytest.mark.parametrize("stats", [
    dict(hunger=80), dict(hunger=20, energy=10), dict(hunger=20, happiness=10),
    dict(hunger=20, happiness=90), dict(hunger=20, happiness=50),
])
def test_pet_always_has_something_to_say(personality, stats):
    pet = Pet("Bean", personality=personality, **stats)
    assert pet.idle_message()


# ---- Petting ----

def test_petting_raises_happiness_without_xp():
    pet = Pet("Bean", happiness=50)
    result = pet.cuddle()
    assert result.kind == "petted"
    assert result.xp_gained == 0
    assert pet.happiness == 50 + CUDDLE_HAPPINESS


def test_petting_has_a_cooldown():
    pet = Pet("Bean", happiness=50)
    pet.cuddle()
    pet.cuddle()  # too soon: still reacts, but no extra happiness
    assert pet.happiness == 50 + CUDDLE_HAPPINESS


def test_petting_works_again_after_cooldown():
    pet = Pet("Bean", happiness=50)
    pet.cuddle()
    pet.update(CUDDLE_COOLDOWN)
    before = pet.happiness
    pet.cuddle()
    assert pet.happiness > before
