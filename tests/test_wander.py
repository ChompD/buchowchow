"""Tests for the companion's own behaviour (pure logic, no windows)."""

import random
from collections import Counter

import pytest

from wander import BARK_COOLDOWN, CHOICES, DURATIONS, MOVING, SPEEDS, Wanderer

LEFT, RIGHT = 0.0, 1000.0
DT = 1 / 60


def simulate(mood, seconds, seed=1, x=500.0, can_move=True):
    """Run a wanderer for a while; record positions and how long each activity lasted."""
    wanderer = Wanderer(random.Random(seed))
    positions, time_in = [], Counter()
    for _ in range(int(seconds / DT)):
        x = wanderer.update(DT, x, LEFT, RIGHT, mood, can_move)
        positions.append(x)
        time_in[wanderer.activity] += DT
    return wanderer, positions, time_in


# ---- Doing things ----

def test_every_activity_has_a_duration():
    for options in CHOICES.values():
        assert set(options) <= set(DURATIONS)
    assert "bark" in DURATIONS


@pytest.mark.parametrize("mood", ["happy", "content", "hungry", "sad"])
def test_awake_pets_go_for_walks(mood):
    _, positions, time_in = simulate(mood, 120)
    assert time_in["walk"] > 0
    assert max(positions) - min(positions) > 50


def test_happy_pets_try_everything():
    _, _, time_in = simulate("happy", 900)
    for activity in ("walk", "run", "sit", "lie", "look", "tilt"):
        assert time_in[activity] > 0, activity


def test_tired_pets_only_sit_and_lie():
    _, positions, time_in = simulate("tired", 300)
    assert set(time_in) <= {"sit", "lie"}
    assert time_in["lie"] > 0
    assert set(positions) == {500.0}


def test_sad_pets_lie_down_more_than_happy_ones():
    _, _, sad = simulate("sad", 900, seed=2)
    _, _, happy = simulate("happy", 900, seed=2)
    assert sad["lie"] / 900 > happy["lie"] / 900


@pytest.mark.parametrize("seed", range(5))
def test_never_leaves_the_allowed_area(seed):
    _, positions, _ = simulate("happy", 300, seed=seed)
    assert all(LEFT <= x <= RIGHT for x in positions)


def test_always_does_something_calm_after_moving():
    wanderer = Wanderer(random.Random(0))
    x, previous = 500.0, wanderer.activity
    for _ in range(int(900 / DT)):
        x = wanderer.update(DT, x, LEFT, RIGHT, "happy")
        if wanderer.activity != previous:
            if previous in MOVING:
                assert wanderer.activity not in MOVING
            previous = wanderer.activity


def test_mostly_calm():
    _, _, time_in = simulate("happy", 900)
    moving = sum(time_in[a] for a in MOVING)
    assert moving / sum(time_in.values()) < 0.5


# ---- Moving ----

def test_turns_around_at_an_edge():
    wanderer = Wanderer(random.Random(0))
    wanderer._start("walk")
    wanderer.direction, wanderer.timer = 1, 10.0
    x = RIGHT - 1
    for _ in range(30):
        x = wanderer.update(DT, x, LEFT, RIGHT, "happy")
    assert wanderer.direction == -1
    assert x < RIGHT


def test_running_is_faster_than_walking():
    def distance(activity, mood="content"):
        wanderer = Wanderer(random.Random(3))
        wanderer._start(activity)
        wanderer.direction, wanderer.timer = 1, 10.0
        return wanderer.update(1.0, 100.0, LEFT, RIGHT, mood) - 100.0

    assert distance("run") > distance("walk") > 0
    assert distance("walk", "happy") > distance("walk", "sad") > 0


def test_stay_mode_never_moves():
    wanderer, positions, time_in = simulate("happy", 600, can_move=False)
    assert set(positions) == {500.0}
    assert not any(time_in[a] for a in MOVING)
    assert time_in["sit"] > 0 and time_in["look"] > 0


def test_switching_to_stay_stops_a_walk():
    wanderer = Wanderer(random.Random(0))
    wanderer._start("walk")
    wanderer.update(DT, 500, LEFT, RIGHT, "happy", can_move=False)
    assert not wanderer.walking


def test_progress_goes_from_0_to_1():
    wanderer = Wanderer(random.Random(0))
    wanderer._start("tilt")
    assert wanderer.progress == pytest.approx(0.0)
    wanderer.update(wanderer.duration / 2, 500, LEFT, RIGHT, "content", can_move=False)
    assert wanderer.progress == pytest.approx(0.5, abs=0.01)


# ---- Noticing the cursor ----

class AlwaysBark(random.Random):
    def random(self):
        return 0.0


class NeverBark(random.Random):
    def random(self):
        return 0.99


def test_barks_and_faces_the_cursor():
    wanderer = Wanderer(AlwaysBark(0))
    assert wanderer.notice_cursor(+120)
    assert wanderer.activity == "bark"
    assert wanderer.direction == 1


def test_bark_has_a_cooldown():
    wanderer = Wanderer(AlwaysBark(0))
    wanderer.notice_cursor(-50)
    x = 500.0
    for _ in range(int((BARK_COOLDOWN - 1) / DT)):
        x = wanderer.update(DT, x, LEFT, RIGHT, "content")
    assert not wanderer.notice_cursor(-50)
    for _ in range(int(2 / DT)):
        x = wanderer.update(DT, x, LEFT, RIGHT, "content")
    assert wanderer.notice_cursor(-50)


def test_sometimes_just_ignores_the_cursor():
    wanderer = Wanderer(NeverBark(0))
    assert not wanderer.notice_cursor(80)
    assert wanderer.activity != "bark"
    assert not wanderer.notice_cursor(80)  # and doesn't re-decide every frame


def test_tired_pets_never_walk_even_when_asked():
    assert SPEEDS["tired"] == 0
    assert not set(CHOICES["tired"]) & set(MOVING)
