"""Decides what the companion pet does on its own: walk, run, sit, lie down,
look around, tilt its head, or bark at your cursor.

This is pure logic with no Pygame or windows involved: give it the pet's x
position, the space it may use, and its mood, and it returns where the pet
should be next. `activity` says what it's doing, for drawing.

After every walk or run the pet does something calm, so it stays gentle and
doesn't pull your attention away from what you're doing.
"""

import random

MOVING = ("walk", "run")

# How fast each mood walks, in pixels per second. 0 means it doesn't walk at all.
SPEEDS = {
    "happy": 70,
    "content": 50,
    "hungry": 35,
    "sad": 28,
    "tired": 0,
}
RUN_FACTOR = 2.4  # running is this much faster than walking

# How long each activity lasts, in seconds (min, max).
DURATIONS = {
    "walk": (2.0, 5.0),
    "run": (1.2, 2.5),
    "sit": (4.0, 10.0),
    "lie": (6.0, 14.0),
    "look": (3.0, 6.0),
    "tilt": (1.4, 2.4),
    "bark": (1.1, 1.1),
}
FIRST_PAUSE = (1.5, 4.0)  # don't make people wait long for the first thing to happen

# How likely each activity is, per mood (bigger number = more likely).
CHOICES = {
    "happy": {"walk": 30, "run": 20, "sit": 15, "look": 15, "tilt": 10, "lie": 10},
    "content": {"walk": 30, "run": 8, "sit": 25, "look": 20, "tilt": 10, "lie": 7},
    "hungry": {"walk": 25, "sit": 30, "look": 25, "tilt": 10, "lie": 10},
    "sad": {"walk": 15, "sit": 30, "look": 20, "lie": 35},
    "tired": {"sit": 30, "lie": 70},
}

# Barking at the cursor
BARK_CHANCE = 0.6       # chance to bark when the cursor comes close
BARK_COOLDOWN = 20.0    # seconds before it can bark again
NOTICE_RETRY = 5.0      # if it decided not to bark, wait this long before maybe barking


class Wanderer:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.activity = "sit"
        self.direction = self.rng.choice((-1, 1))  # -1 = left, 1 = right
        self.duration = self.timer = self.rng.uniform(*FIRST_PAUSE)
        self.bark_cooldown = 0.0

    @property
    def walking(self):
        """True while walking or running (moving along the taskbar)."""
        return self.activity in MOVING

    @property
    def progress(self):
        """How far through the current activity, from 0.0 to 1.0."""
        return 1 - self.timer / self.duration if self.duration > 0 else 1.0

    def update(self, dt, x, left, right, mood, can_move=True):
        """Advance by `dt` seconds and return the new x (always within [left, right]).

        `can_move=False` (Stay mode) keeps the pet in place: it still sits, lies,
        looks around and so on, but never walks or runs.
        """
        self.bark_cooldown = max(0.0, self.bark_cooldown - dt)
        self.timer -= dt
        if self.walking:
            if can_move and right > left:
                speed = self.speed(mood)
                x += self.direction * speed * dt
                if x <= left:
                    x, self.direction = left, 1    # bump into the edge: turn around
                elif x >= right:
                    x, self.direction = right, -1
            else:
                self.timer = 0  # not allowed to move any more: pick something else
        if self.timer <= 0:
            self._next(x, left, right, mood, can_move and right > left)
        return min(max(x, left), right) if right >= left else x

    def speed(self, mood):
        walk = SPEEDS.get(mood, SPEEDS["content"])
        return walk * RUN_FACTOR if self.activity == "run" else walk

    def notice_cursor(self, direction):
        """The cursor just came close. Returns True if the pet barks at it (and faces it)."""
        if self.bark_cooldown > 0 or self.activity == "bark":
            return False
        if self.rng.random() >= BARK_CHANCE:
            self.bark_cooldown = NOTICE_RETRY
            return False
        self.bark_cooldown = BARK_COOLDOWN
        self.direction = 1 if direction > 0 else -1
        self._start("bark")
        return True

    def _next(self, x, left, right, mood, can_move):
        options = dict(CHOICES.get(mood, CHOICES["content"]))
        if self.walking or not can_move or SPEEDS.get(mood, 0) == 0:
            # Just finished moving (or can't move): do something calm next.
            for moving in MOVING:
                options.pop(moving, None)
        activities = list(options)
        choice = self.rng.choices(activities, weights=[options[a] for a in activities])[0]
        if choice in MOVING:
            # Head away from a nearby edge, otherwise pick a direction at random.
            margin = (right - left) * 0.15
            if x - left < margin:
                self.direction = 1
            elif right - x < margin:
                self.direction = -1
            else:
                self.direction = self.rng.choice((-1, 1))
        self._start(choice)

    def _start(self, activity):
        self.activity = activity
        self.duration = self.timer = self.rng.uniform(*DURATIONS[activity])
