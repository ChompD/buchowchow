"""Decides when the companion pet walks, rests and turns around.

This is pure logic with no Pygame or windows involved: give it the pet's x
position, the space it may use, and its mood, and it returns where the pet
should be next. That makes it easy to test.

Walks are short and rests are long, so a wandering pet stays gentle and
doesn't pull your attention away from what you're doing.
"""

import random

# How fast each mood walks, in pixels per second. 0 means it doesn't walk at all.
SPEEDS = {
    "happy": 70,
    "content": 50,
    "hungry": 35,
    "sad": 28,
    "tired": 0,
}
WALK_SECONDS = (2.0, 5.0)
REST_SECONDS = (5.0, 12.0)
FIRST_REST_SECONDS = (1.5, 4.0)  # don't make people wait long for the first stroll


class Wanderer:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.walking = False
        self.direction = self.rng.choice((-1, 1))  # -1 = left, 1 = right
        self.timer = self.rng.uniform(*FIRST_REST_SECONDS)

    def update(self, dt, x, left, right, mood):
        """Advance by `dt` seconds and return the new x (always within [left, right])."""
        speed = SPEEDS.get(mood, SPEEDS["content"])
        if speed == 0 or right <= left:
            self.walking = False  # too tired to walk (or nowhere to go)
            return min(max(x, left), right)

        self.timer -= dt
        if self.walking:
            x += self.direction * speed * dt
            if x <= left:
                x, self.direction = left, 1    # bump into the edge: turn around
            elif x >= right:
                x, self.direction = right, -1
            if self.timer <= 0:
                self._rest()
        elif self.timer <= 0:
            self._walk(x, left, right)
        return min(max(x, left), right)

    def _rest(self):
        self.walking = False
        self.timer = self.rng.uniform(*REST_SECONDS)

    def _walk(self, x, left, right):
        self.walking = True
        self.timer = self.rng.uniform(*WALK_SECONDS)
        # Head away from a nearby edge, otherwise pick a direction at random.
        margin = (right - left) * 0.15
        if x - left < margin:
            self.direction = 1
        elif right - x < margin:
            self.direction = -1
        else:
            self.direction = self.rng.choice((-1, 1))
