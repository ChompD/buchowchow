"""Tests for the pet's lines of dialogue."""

import random

import pytest

from messages import (
    BY_PERSONALITY,
    BY_SPECIES,
    COMMON,
    PERSONALITIES,
    SPECIES,
    SPECIES_NAMES,
    format_duration,
    pick,
)

KINDS = list(COMMON)
VALUES = {"name": "Bean", "level": 2, "stage": "Junior"}


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("personality", PERSONALITIES)
@pytest.mark.parametrize("species", SPECIES)
def test_every_situation_has_lines(kind, personality, species):
    assert pick(kind, personality, random.Random(1), species=species, **VALUES)


def test_every_line_formats_without_errors():
    extras = list(BY_PERSONALITY.values()) + list(BY_SPECIES.values())
    pools = list(COMMON.values()) + [lines for extra in extras for lines in extra.values()]
    for lines in pools:
        for line in lines:
            assert "{" not in line.format_map(VALUES)


def test_personality_lines_only_use_known_situations():
    assert set(BY_PERSONALITY) <= set(PERSONALITIES)
    for extra in BY_PERSONALITY.values():
        assert set(extra) <= set(COMMON)


def test_species_lines_only_use_known_situations():
    assert set(BY_SPECIES) <= set(SPECIES)
    assert set(SPECIES_NAMES) == set(SPECIES)
    for extra in BY_SPECIES.values():
        assert set(extra) <= set(COMMON)


def test_species_lines_can_be_picked():
    lines = {pick("petted", None, random.Random(seed), species="dog", **VALUES) for seed in range(50)}
    assert lines & set(BY_SPECIES["dog"]["petted"])


def test_names_are_filled_in():
    line = pick("level_up", None, random.Random(0), name="Bean", level=7)
    assert "7" in line


def test_unknown_situation_gives_empty_string():
    assert pick("dancing", "shy", random.Random(0), name="Bean", level=1) == ""


@pytest.mark.parametrize("seconds, text", [
    (0, "0s"), (45, "45s"), (60, "1m"), (59 * 60, "59m"), (3600, "1h"),
    (2 * 3600 + 5 * 60, "2h 5m"), (86400, "1d"), (3 * 86400 + 4 * 3600, "3d 4h"), (-10, "0s"),
])
def test_format_duration(seconds, text):
    assert format_duration(seconds) == text


def test_ghost_tip_is_always_the_line_shown():
    # Turning ghost mode on must always explain how to reach the pet again.
    for personality in PERSONALITIES:
        for species in SPECIES:
            for seed in range(5):
                line = pick("ghost_on", personality, random.Random(seed), species=species, **VALUES)
                assert "Ctrl" in line
