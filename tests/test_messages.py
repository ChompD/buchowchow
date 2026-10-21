"""Tests for the pet's lines of dialogue."""

import random

import pytest

from messages import BY_PERSONALITY, COMMON, PERSONALITIES, format_duration, pick

KINDS = list(COMMON)
VALUES = {"name": "Bean", "level": 2, "stage": "Junior"}


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("personality", PERSONALITIES)
def test_every_situation_has_lines(kind, personality):
    assert pick(kind, personality, random.Random(1), **VALUES)


def test_every_line_formats_without_errors():
    pools = list(COMMON.values()) + [lines for extra in BY_PERSONALITY.values() for lines in extra.values()]
    for lines in pools:
        for line in lines:
            assert "{" not in line.format_map(VALUES)


def test_personality_lines_only_use_known_situations():
    assert set(BY_PERSONALITY) <= set(PERSONALITIES)
    for extra in BY_PERSONALITY.values():
        assert set(extra) <= set(COMMON)


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
