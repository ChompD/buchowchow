"""Tests for saving and loading. Each test uses its own temporary folder."""

import json

import pytest

from pet import OFFLINE_RATE, Pet
from save_manager import SAVE_VERSION, SaveManager


class FakeClock:
    """A clock we can move forward by hand."""

    def __init__(self, now=1_000_000.0):
        self.now = now

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def manager(tmp_path, clock):
    return SaveManager(tmp_path / "save.json", clock=clock)


def test_no_save_file_means_new_game(manager):
    result = manager.load()
    assert result.status == "new"
    assert result.pet is None


def test_save_and_load_round_trip(manager):
    pet = Pet("Biscuit", hunger=40, happiness=60, energy=70, xp=12, level=5, personality="foodie")
    assert manager.save(pet)
    result = manager.load()
    assert result.status == "loaded"
    assert result.pet.to_dict() == pet.to_dict()
    assert result.seconds_away == 0


def test_save_file_is_readable_json(manager):
    manager.save(Pet("Biscuit"))
    data = json.loads(manager.path.read_text(encoding="utf-8"))
    assert data["version"] == SAVE_VERSION
    assert data["pet"]["name"] == "Biscuit"


def test_saving_leaves_no_temp_file(manager, tmp_path):
    manager.save(Pet("Biscuit"))
    manager.save(Pet("Biscuit"))
    assert [p.name for p in tmp_path.iterdir()] == ["save.json"]


def test_time_away_is_applied_on_load(manager, clock):
    manager.save(Pet("Biscuit", hunger=20, happiness=80, energy=30))
    clock.now += 3600  # one hour later
    result = manager.load()
    assert result.seconds_away == 3600
    expected = Pet("Biscuit", hunger=20, happiness=80, energy=30)
    expected.update(3600 * OFFLINE_RATE)
    assert result.pet.hunger == pytest.approx(expected.hunger)
    assert result.pet.energy == pytest.approx(expected.energy)


def test_clock_going_backwards_is_ignored(manager, clock):
    manager.save(Pet("Biscuit", hunger=20))
    clock.now -= 10_000
    result = manager.load()
    assert result.seconds_away == 0
    assert result.pet.hunger == 20


@pytest.mark.parametrize("contents", [
    "",                                                                   # empty file
    "{not json",                                                          # broken JSON
    "[1, 2, 3]",                                                          # wrong shape
    '{"version": 1, "saved_at": 5}',                                      # no pet
    '{"version": 99, "saved_at": 5, "pet": {"name": "Bean"}}',            # from the future
    '{"version": 1, "saved_at": "soon", "pet": {"name": "Bean"}}',        # bad time
    '{"version": 1, "saved_at": 5, "pet": {"name": "Bean", "xp": "x"}}',  # bad stat
    '{"version": 1, "saved_at": NaN, "pet": {"name": "Bean"}}',           # not a real number
])
def test_corrupt_save_is_backed_up_and_game_starts_fresh(manager, contents):
    manager.path.write_text(contents, encoding="utf-8")
    result = manager.load()
    assert result.status == "corrupt"
    assert result.pet is None
    assert not manager.path.exists()
    assert result.backup_path.exists()
    assert result.backup_path.read_text(encoding="utf-8") == contents  # nothing lost
    assert manager.load().status == "new"


def test_non_utf8_file_is_treated_as_corrupt(manager):
    manager.path.write_bytes(b"\xff\xfe\x00garbage")
    assert manager.load().status == "corrupt"


def test_save_failure_does_not_crash(tmp_path, clock):
    blocked = tmp_path / "save.json"
    blocked.mkdir()  # a folder where the file should go: writing must fail
    manager = SaveManager(blocked, clock=clock)
    assert manager.save(Pet("Biscuit")) is False


# ---- Settings (companion mode and position) ----

def test_settings_round_trip(manager):
    settings = {"companion": True, "companion_pos": [1500, 700]}
    manager.save(Pet("Biscuit"), settings)
    assert manager.load().settings == settings


def test_old_saves_without_settings_still_load(manager):
    data = {"version": SAVE_VERSION, "saved_at": manager.clock(), "pet": {"name": "Biscuit"}}
    manager.path.write_text(json.dumps(data), encoding="utf-8")
    result = manager.load()
    assert result.status == "loaded"
    assert result.settings == {}


def test_broken_settings_are_ignored_not_fatal(manager):
    data = {"version": SAVE_VERSION, "saved_at": manager.clock(), "pet": {"name": "Biscuit"},
            "settings": "oops"}
    manager.path.write_text(json.dumps(data), encoding="utf-8")
    result = manager.load()
    assert result.status == "loaded"
    assert result.settings == {}
