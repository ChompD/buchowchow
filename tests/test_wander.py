"""Tests for the companion's wandering (pure logic, no windows)."""

import random

import pytest

from wander import REST_SECONDS, WALK_SECONDS, Wanderer

LEFT, RIGHT = 0.0, 1000.0
DT = 1 / 60


def simulate(mood, seconds, seed=1, x=500.0):
    """Run a wanderer for a while and record every position and walking flag."""
    wanderer = Wanderer(random.Random(seed))
    positions, walking = [], []
    for _ in range(int(seconds / DT)):
        x = wanderer.update(DT, x, LEFT, RIGHT, mood)
        positions.append(x)
        walking.append(wanderer.walking)
    return positions, walking


@pytest.mark.parametrize("mood", ["happy", "content", "hungry", "sad"])
def test_awake_pets_go_for_walks(mood):
    positions, walking = simulate(mood, 60)
    assert any(walking)
    assert max(positions) - min(positions) > 50


def test_tired_pets_stay_put():
    positions, walking = simulate("tired", 60)
    assert not any(walking)
    assert set(positions) == {500.0}


@pytest.mark.parametrize("seed", range(5))
def test_never_leaves_the_allowed_area(seed):
    positions, _ = simulate("happy", 300, seed=seed)
    assert all(LEFT <= x <= RIGHT for x in positions)


def test_turns_around_at_an_edge():
    wanderer = Wanderer(random.Random(0))
    wanderer.walking, wanderer.direction, wanderer.timer = True, 1, 10.0
    x = RIGHT - 1
    for _ in range(30):
        x = wanderer.update(DT, x, LEFT, RIGHT, "happy")
    assert wanderer.direction == -1
    assert x < RIGHT


def test_heads_away_from_a_nearby_edge():
    wanderer = Wanderer(random.Random(0))
    wanderer.timer = 0.0
    wanderer.update(DT, LEFT + 5, LEFT, RIGHT, "content")
    assert wanderer.walking and wanderer.direction == 1


def test_mostly_resting_so_it_stays_calm():
    _, walking = simulate("happy", 600)
    assert sum(walking) / len(walking) < 0.5
    assert max(WALK_SECONDS) <= min(REST_SECONDS)


def test_happy_pets_walk_faster_than_sad_ones():
    def distance(mood):
        wanderer = Wanderer(random.Random(3))
        wanderer.walking, wanderer.direction, wanderer.timer = True, 1, 10.0
        return wanderer.update(1.0, 100.0, LEFT, RIGHT, mood) - 100.0

    assert distance("happy") > distance("content") > distance("sad") > 0


def test_no_room_means_no_walking():
    wanderer = Wanderer(random.Random(0))
    wanderer.timer = 0.0
    assert wanderer.update(DT, 50, 100, 100, "happy") == 100
    assert not wanderer.walking
