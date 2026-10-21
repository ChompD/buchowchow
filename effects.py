"""Short-lived visual effects: particles, floating text, a level-up banner and flash.

Every effect has `update(dt)`, `draw(surface)` and an `alive` flag. The
Effects class keeps a list of them and removes the ones that have finished.
"""

import math
import random

import pygame

import ui


def ease_out(p):
    return 1 - (1 - p) ** 2


def draw_heart(surface, color, center, size):
    x, y = center
    r = size / 2
    pygame.draw.circle(surface, color, (x - r * 0.5, y - r * 0.25), r * 0.6)
    pygame.draw.circle(surface, color, (x + r * 0.5, y - r * 0.25), r * 0.6)
    pygame.draw.polygon(surface, color, [(x - r * 1.08, y - r * 0.05), (x + r * 1.08, y - r * 0.05),
                                         (x, y + r * 1.15)])


def draw_star(surface, color, center, size, angle):
    x, y = center
    points = []
    for i in range(10):
        radius = size if i % 2 == 0 else size * 0.45
        a = angle + i * math.pi / 5 - math.pi / 2
        points.append((x + radius * math.cos(a), y + radius * math.sin(a)))
    pygame.draw.polygon(surface, color, points)


class Particle:
    """A heart, star or dot that flies outward, then shrinks away."""

    def __init__(self, kind, pos, velocity, color, size, life, gravity=0.0, spin=0.0):
        self.kind = kind
        self.x, self.y = pos
        self.vx, self.vy = velocity
        self.color = color
        self.size = size
        self.life = life
        self.gravity = gravity
        self.spin = spin
        self.angle = 0.0
        self.age = 0.0

    @property
    def alive(self):
        return self.age < self.life

    def update(self, dt):
        self.age += dt
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= 1 - min(1.0, dt * 1.5)  # a little air resistance
        self.angle += self.spin * dt

    def draw(self, surface):
        size = self.size * (1 - self.age / self.life) ** 0.5
        if size < 0.5:
            return
        if self.kind == "heart":
            draw_heart(surface, self.color, (self.x, self.y), size)
        elif self.kind == "star":
            draw_star(surface, self.color, (self.x, self.y), size, self.angle)
        else:
            pygame.draw.circle(surface, self.color, (self.x, self.y), size)


class FloatingText:
    """Text such as "+10 XP" that drifts upward and fades out."""

    def __init__(self, text, font, color, pos, life=1.2, rise=45):
        self.image = font.render(text, True, color)
        self.x, self.y = pos
        self.life = life
        self.rise = rise
        self.age = 0.0

    @property
    def alive(self):
        return self.age < self.life

    def update(self, dt):
        self.age += dt

    def draw(self, surface):
        p = self.age / self.life
        self.image.set_alpha(round(255 * min(1.0, (1 - p) * 2)))
        surface.blit(self.image, self.image.get_rect(center=(self.x, self.y - self.rise * ease_out(p))))


class Banner:
    """A big "LEVEL UP!" badge that pops in, holds, then fades out."""

    def __init__(self, text, font, pos, life=1.8):
        label = font.render(text, True, ui.WHITE)
        rect = label.get_rect().inflate(44, 18)
        self.image = pygame.Surface((rect.width, rect.height + 5), pygame.SRCALPHA)
        pill = pygame.Rect(0, 0, rect.width, rect.height)
        pygame.draw.rect(self.image, ui.mix(ui.XP_COLOR, (0, 0, 0), 0.2), pill.move(0, 5),
                         border_radius=rect.height // 2)
        pygame.draw.rect(self.image, ui.XP_COLOR, pill, border_radius=rect.height // 2)
        self.image.blit(label, label.get_rect(center=pill.center))
        self.pos = pos
        self.life = life
        self.age = 0.0

    @property
    def alive(self):
        return self.age < self.life

    def update(self, dt):
        self.age += dt

    def draw(self, surface):
        p = self.age / self.life
        if p < 0.12:
            scale = 0.4 + 0.8 * (p / 0.12)          # grow past full size...
        elif p < 0.22:
            scale = 1.2 - 0.2 * ((p - 0.12) / 0.1)  # ...then settle back
        else:
            scale = 1.0
        image = pygame.transform.rotozoom(self.image, 0, scale)
        image.set_alpha(round(255 * min(1.0, (1 - p) / 0.25)))
        surface.blit(image, image.get_rect(center=self.pos))


class Effects:
    """Keeps track of all running effects."""

    FLASH_SECONDS = 0.45

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.items = []     # particles and floating text (drawn over the pet)
        self.overlays = []  # banners (drawn on top of everything)
        self.flash_age = self.FLASH_SECONDS

    def update(self, dt):
        for item in self.items + self.overlays:
            item.update(dt)
        self.items = [item for item in self.items if item.alive]
        self.overlays = [item for item in self.overlays if item.alive]
        self.flash_age += dt

    def draw(self, surface):
        for item in self.items:
            item.draw(surface)

    def draw_overlay(self, surface):
        if self.flash_age < self.FLASH_SECONDS:
            flash = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            flash.fill((255, 255, 255, round(170 * (1 - self.flash_age / self.FLASH_SECONDS))))
            surface.blit(flash, (0, 0))
        for item in self.overlays:
            item.draw(surface)

    # ---- Ready-made effects ----

    def burst(self, kind, pos, count, colors, speed=(60, 160), size=(5, 9), life=(0.6, 1.1),
              gravity=0.0, lift=0.0, spin=0.0):
        rng = self.rng
        for _ in range(count):
            angle = rng.uniform(0, 2 * math.pi)
            power = rng.uniform(*speed)
            velocity = (math.cos(angle) * power, math.sin(angle) * power - lift)
            self.items.append(Particle(kind, pos, velocity, rng.choice(colors), rng.uniform(*size),
                                       rng.uniform(*life), gravity, rng.uniform(-spin, spin)))

    def hearts(self, pos):
        self.burst("heart", pos, 6, [ui.HAPPY_COLOR, (255, 110, 150)], speed=(20, 70),
                   size=(9, 14), life=(0.8, 1.3), gravity=-40, lift=50)

    def crumbs(self, pos):
        self.burst("dot", pos, 5, [ui.COOKIE, ui.COOKIE_DARK], speed=(40, 110), size=(2, 4),
                   life=(0.4, 0.7), gravity=500, lift=60)

    def sparkles(self, pos, count=8):
        self.burst("star", pos, count, [ui.XP_COLOR, ui.GOLD], speed=(30, 100), size=(4, 7),
                   life=(0.4, 0.8), spin=4)

    def floating_text(self, text, font, color, pos):
        self.items.append(FloatingText(text, font, color, pos))

    def level_up(self, pet_pos, banner_font, banner_pos, text="LEVEL UP!", stars=28, flash=True):
        if flash:
            self.flash_age = 0.0
        self.burst("star", pet_pos, stars, [ui.GOLD, ui.XP_COLOR, ui.HAPPY_COLOR, ui.ENERGY_COLOR],
                   speed=(140, 320), size=(6, 11), life=(0.8, 1.4), gravity=260, lift=80, spin=5)
        self.overlays.append(Banner(text, banner_font, banner_pos))
