"""Core pet logic: stats, actions, experience, levels and personality.

This module has no Pygame imports on purpose. Keeping the game rules separate
from the drawing code means they can be unit-tested without opening a window.
"""

import math
import random
from dataclasses import dataclass

from messages import PERSONALITIES, SPECIES, SPECIES_NAMES, pick
from wardrobe import Outfit, unlocked_between

STAT_MIN = 0
STAT_MAX = 100

DEFAULT_NAME = "Mochi"
MAX_NAME_LENGTH = 12
DEFAULT_SPECIES = "dog"  # also used for saves from before species existed

# Passive changes per second while the app is open.
HUNGER_RATE = 1 / 6        # +1 hunger every 6 seconds
HAPPINESS_RATE = 1 / 8     # -1 happiness every 8 seconds
ENERGY_RATE = 1 / 5        # +1 energy every 5 seconds (resting)

# Feeding
FEED_HUNGER = 30           # hunger removed per meal
FEED_HAPPINESS = 5
FEED_XP = 10
FULL_THRESHOLD = 10        # hunger at or below this means "too full to eat"

# Playing
PLAY_HAPPINESS = 20
PLAY_ENERGY_COST = 15
PLAY_HUNGER = 10           # playing works up an appetite
PLAY_XP = 15

# Petting (clicking the pet). No XP, and a cooldown so it can't be spammed.
CUDDLE_HAPPINESS = 3
CUDDLE_COOLDOWN = 4.0      # seconds

# Time away: while the game is closed, time passes 80x slower for the pet,
# and at most 8 hours count. A full night away adds about 60 hunger, so the
# pet is hungry but not miserable, and a weekend away is no worse than a night.
OFFLINE_RATE = 1 / 80
MAX_OFFLINE_SECONDS = 8 * 60 * 60

# Evolution stages: (level reached, stage name)
EVOLUTION_STAGES = [
    (1, "Baby"),
    (3, "Junior"),
    (6, "Adult"),
    (10, "Royal"),
]

# Mood thresholds (checked in priority order in Pet.mood)
HUNGRY_AT = 70             # hunger >= 70
TIRED_AT = 20              # energy <= 20
SAD_AT = 30                # happiness <= 30
HAPPY_AT = 70              # happiness >= 70

MOOD_TEXT = {
    "hungry": "{name}'s tummy is rumbling...",
    "tired": "{name} is getting sleepy.",
    "sad": "{name} feels a bit lonely.",
    "happy": "{name} is feeling great!",
    "content": "{name} is doing okay.",
}


def clamp(value, low=STAT_MIN, high=STAT_MAX):
    """Keep a number inside [low, high]."""
    return max(low, min(high, value))


def xp_for_next_level(level):
    """XP needed to go from `level` to `level + 1`. Grows a little each level."""
    return 50 + (level - 1) * 25


def clean_name(name):
    """Tidy whitespace, cap the length, and fall back to a default name."""
    name = " ".join(str(name).split())[:MAX_NAME_LENGTH].strip()
    return name or DEFAULT_NAME


@dataclass
class ActionResult:
    """What happened when the user interacted with the pet.

    `kind` is one of: fed, too_full, played, too_tired, petted.
    """

    kind: str
    message: str
    xp_gained: int = 0
    levels_gained: int = 0
    evolved: bool = False
    unlocked: tuple = ()  # names of wardrobe items unlocked by this level up


class Pet:
    """A virtual pet with stats that change over time and through interaction.

    Stats run from 0 to 100:
      hunger    - higher means hungrier
      happiness - higher means happier
      energy    - higher means more rested

    `rng` lets tests pass a seeded random generator so results are repeatable.
    """

    def __init__(self, name, hunger=30, happiness=70, energy=80, xp=0, level=1,
                 personality=None, rng=None, species=DEFAULT_SPECIES):
        self.rng = rng or random.Random()
        self.name = clean_name(name)
        self.hunger = clamp(hunger)
        self.happiness = clamp(happiness)
        self.energy = clamp(energy)
        self.level = max(1, int(level))
        self.xp = max(0, int(xp))
        self._apply_level_ups()  # in case we were given more XP than the level holds
        if personality not in PERSONALITIES:
            personality = self.rng.choice(PERSONALITIES)
        self.personality = personality
        self.species = species if species in SPECIES else DEFAULT_SPECIES
        self.outfit = Outfit()
        self.cuddle_cooldown = 0.0

    # ---- Time ----

    def update(self, dt):
        """Advance the pet's stats by `dt` seconds."""
        if dt <= 0:
            return
        self.hunger = clamp(self.hunger + HUNGER_RATE * dt)
        self.happiness = clamp(self.happiness - HAPPINESS_RATE * dt)
        self.energy = clamp(self.energy + ENERGY_RATE * dt)
        self.cuddle_cooldown = max(0.0, self.cuddle_cooldown - dt)

    def pass_time_offline(self, seconds):
        """Catch up on time that passed while the game was closed."""
        seconds = min(max(0.0, seconds), MAX_OFFLINE_SECONDS)
        self.update(seconds * OFFLINE_RATE)

    # ---- Actions ----

    def feed(self):
        if self.hunger <= FULL_THRESHOLD:
            return ActionResult("too_full", self.say("too_full"))
        self.hunger = clamp(self.hunger - FEED_HUNGER)
        self.happiness = clamp(self.happiness + FEED_HAPPINESS)
        return self._reward("fed", FEED_XP)

    def play(self):
        if self.energy < PLAY_ENERGY_COST:
            return ActionResult("too_tired", self.say("too_tired"))
        self.happiness = clamp(self.happiness + PLAY_HAPPINESS)
        self.energy = clamp(self.energy - PLAY_ENERGY_COST)
        self.hunger = clamp(self.hunger + PLAY_HUNGER)
        return self._reward("played", PLAY_XP)

    def cuddle(self):
        """The user clicked (petted) the pet."""
        if self.cuddle_cooldown <= 0:
            self.happiness = clamp(self.happiness + CUDDLE_HAPPINESS)
            self.cuddle_cooldown = CUDDLE_COOLDOWN
        return ActionResult("petted", self.say("petted"))

    # ---- Experience ----

    def add_xp(self, amount):
        """Add XP and return how many levels were gained."""
        if amount <= 0:
            return 0
        self.xp += int(amount)
        return self._apply_level_ups()

    def _apply_level_ups(self):
        levels = 0
        while self.xp >= xp_for_next_level(self.level):
            self.xp -= xp_for_next_level(self.level)
            self.level += 1
            levels += 1
        return levels

    def _reward(self, kind, xp):
        stage_before, level_before = self.stage, self.level
        levels = self.add_xp(xp)
        evolved = self.stage > stage_before
        unlocked = tuple(item.name for item in unlocked_between(level_before, self.level))
        if evolved:
            message = self.say("evolved")
        elif levels:
            message = self.say("level_up")
        else:
            message = self.say(kind)
        return ActionResult(kind, message, xp_gained=xp, levels_gained=levels, evolved=evolved,
                            unlocked=unlocked)

    @property
    def xp_needed(self):
        return xp_for_next_level(self.level)

    @property
    def xp_progress(self):
        """Progress toward the next level, from 0.0 to 1.0."""
        return self.xp / self.xp_needed

    # ---- Evolution ----

    @property
    def stage(self):
        """Evolution stage index: 0 = Baby, up to len(EVOLUTION_STAGES) - 1."""
        return sum(1 for level, _ in EVOLUTION_STAGES[1:] if self.level >= level)

    @property
    def stage_name(self):
        return EVOLUTION_STAGES[self.stage][1]

    @property
    def next_stage_level(self):
        """Level of the next evolution, or None when fully evolved."""
        if self.stage + 1 < len(EVOLUTION_STAGES):
            return EVOLUTION_STAGES[self.stage + 1][0]
        return None

    # ---- Saving ----

    def to_dict(self):
        """Everything needed to bring this pet back later (JSON-friendly)."""
        return {
            "name": self.name,
            "species": self.species,
            "personality": self.personality,
            "hunger": round(self.hunger, 2),
            "happiness": round(self.happiness, 2),
            "energy": round(self.energy, 2),
            "xp": self.xp,
            "level": self.level,
            "outfit": self.outfit.to_dict(),
        }

    @classmethod
    def from_dict(cls, data, rng=None):
        """Rebuild a pet from `to_dict()` data. Raises ValueError if it is unusable.

        Missing stats fall back to defaults and out-of-range numbers are clamped,
        but values of the wrong type are rejected.
        """
        if not isinstance(data, dict):
            raise ValueError("pet data must be a JSON object")
        name = data.get("name")
        if not isinstance(name, str):
            raise ValueError("pet name must be text")
        numbers = {}
        for key in ("hunger", "happiness", "energy", "xp", "level"):
            if key not in data:
                continue
            value = data[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{key} must be a number")
            numbers[key] = value
        pet = cls(name, personality=data.get("personality"), species=data.get("species"),
                  rng=rng, **numbers)
        if "outfit" in data:
            pet.outfit = Outfit.from_dict(data["outfit"], pet.level)
        else:
            # Saved before the wardrobe existed: keep the accessories it used to get automatically.
            pet.outfit = Outfit.for_stage(pet.stage, pet.level)
        return pet

    # ---- Mood and talking ----

    @property
    def mood(self):
        """One of: hungry, tired, sad, happy, content (most urgent first)."""
        if self.hunger >= HUNGRY_AT:
            return "hungry"
        if self.energy <= TIRED_AT:
            return "tired"
        if self.happiness <= SAD_AT:
            return "sad"
        if self.happiness >= HAPPY_AT:
            return "happy"
        return "content"

    def mood_text(self):
        return MOOD_TEXT[self.mood].format(name=self.name)

    def say(self, kind):
        """A random line for this situation, flavoured by personality."""
        return pick(kind, self.personality, self.rng, species=self.species,
                    name=self.name, level=self.level, stage=self.stage_name)

    @property
    def species_name(self):
        return SPECIES_NAMES[self.species]

    def idle_message(self):
        """Something the pet says on its own, based on how it feels."""
        return self.say(f"idle_{self.mood}")
