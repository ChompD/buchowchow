"""Core pet logic: stats, actions, experience, levels and personality.

This module has no Pygame imports on purpose. Keeping the game rules separate
from the drawing code means they can be unit-tested without opening a window.
"""

import random
from dataclasses import dataclass

from messages import PERSONALITIES, pick

STAT_MIN = 0
STAT_MAX = 100

DEFAULT_NAME = "Mochi"
MAX_NAME_LENGTH = 12

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


class Pet:
    """A virtual pet with stats that change over time and through interaction.

    Stats run from 0 to 100:
      hunger    - higher means hungrier
      happiness - higher means happier
      energy    - higher means more rested

    `rng` lets tests pass a seeded random generator so results are repeatable.
    """

    def __init__(self, name, hunger=30, happiness=70, energy=80, xp=0, level=1,
                 personality=None, rng=None):
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
        levels = self.add_xp(xp)
        message = self.say("level_up") if levels else self.say(kind)
        return ActionResult(kind, message, xp_gained=xp, levels_gained=levels)

    @property
    def xp_needed(self):
        return xp_for_next_level(self.level)

    @property
    def xp_progress(self):
        """Progress toward the next level, from 0.0 to 1.0."""
        return self.xp / self.xp_needed

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
        return pick(kind, self.personality, self.rng, name=self.name, level=self.level)

    def idle_message(self):
        """Something the pet says on its own, based on how it feels."""
        return self.say(f"idle_{self.mood}")
