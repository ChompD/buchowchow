"""Saving and loading the pet as a JSON file.

The save file looks like this:

    {
      "version": 1,
      "saved_at": 1761100000.0,     <- Unix time, used for offline time
      "pet": { "name": "Biscuit", "level": 3, ... },
      "settings": { "companion": true, "companion_pos": [1600, 700] }
    }

"settings" is optional; a save without it (or with a broken one) still loads.

Saving never crashes the game: problems are reported and the game carries on.
A save file that can't be read is renamed to a backup (so nothing is lost)
and a new pet is started.
"""

import json
import math
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from pet import Pet

SAVE_VERSION = 1
DEFAULT_SAVE_PATH = Path(__file__).parent / "save.json"


@dataclass
class LoadResult:
    """What happened when we tried to load.

    status is "new" (no save yet), "loaded", or "corrupt" (unreadable file).
    """

    status: str
    pet: Optional[Pet] = None
    seconds_away: float = 0.0
    backup_path: Optional[Path] = None
    settings: dict = field(default_factory=dict)


class SaveManager:
    """Reads and writes one save file.

    `clock` returns the current Unix time. Tests pass a fake clock to
    simulate time passing.
    """

    def __init__(self, path=DEFAULT_SAVE_PATH, clock=time.time):
        self.path = Path(path)
        self.clock = clock

    def save(self, pet, settings=None):
        """Write the pet (and optional app settings) to disk. Returns True on success."""
        data = {"version": SAVE_VERSION, "saved_at": self.clock(), "pet": pet.to_dict(),
                "settings": settings or {}}
        temp_path = self.path.with_name(self.path.name + ".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)
            # Swap the finished file into place in one step, so a crash halfway
            # through saving can never leave a half-written save behind.
            os.replace(temp_path, self.path)
            return True
        except OSError as error:
            print(f"Could not save the pet: {error}", file=sys.stderr)
            return False

    def load(self):
        """Load the pet and apply the time that passed since it was saved."""
        if not self.path.exists():
            return LoadResult("new")
        try:
            with open(self.path, encoding="utf-8") as file:
                data = json.load(file)
            saved_at, pet = self._parse(data)
        except (OSError, ValueError) as error:  # JSON errors are ValueErrors too
            print(f"Could not read the save file: {error}", file=sys.stderr)
            return LoadResult("corrupt", backup_path=self._back_up())

        seconds_away = max(0.0, self.clock() - saved_at)  # ignore clocks that went backwards
        pet.pass_time_offline(seconds_away)
        settings = data.get("settings")
        if not isinstance(settings, dict):
            settings = {}  # settings are a nice-to-have: never reject a save over them
        return LoadResult("loaded", pet, seconds_away, settings=settings)

    @staticmethod
    def _parse(data):
        if not isinstance(data, dict):
            raise ValueError("save file must contain a JSON object")
        version = data.get("version")
        if version != SAVE_VERSION:
            raise ValueError(f"unsupported save version: {version!r}")
        saved_at = data.get("saved_at")
        if isinstance(saved_at, bool) or not isinstance(saved_at, (int, float)) or not math.isfinite(saved_at):
            raise ValueError("saved_at must be a number")
        return saved_at, Pet.from_dict(data.get("pet"))

    def _back_up(self):
        """Move an unreadable save aside, e.g. save.corrupt-20261022-153000.json."""
        stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(self.clock()))
        backup = self.path.with_name(f"{self.path.stem}.corrupt-{stamp}{self.path.suffix}")
        try:
            os.replace(self.path, backup)
            return backup
        except OSError as error:
            print(f"Could not back up the save file: {error}", file=sys.stderr)
            return None
