"""Drawing helpers: colours, fonts, buttons, stat bars, speech bubbles and the pet.

Nothing in here changes game state. It only draws what it is given.
"""

import math

import pygame

# ---- Palette (soft pastels) ----
BG_TOP = (255, 236, 242)
BG_BOTTOM = (226, 236, 255)
WHITE = (255, 255, 255)
PANEL_SHADOW = (234, 220, 238)
TEXT = (92, 74, 104)
TEXT_SOFT = (160, 142, 170)
BAR_BG = (243, 234, 246)

HUNGER_COLOR = (255, 176, 120)
HAPPY_COLOR = (255, 138, 178)
ENERGY_COLOR = (118, 196, 232)
XP_COLOR = (168, 136, 240)

FEED_COLOR = (255, 158, 112)
PLAY_COLOR = (132, 164, 248)

PET_BODY = (255, 230, 200)
PET_BELLY = (255, 243, 226)
PET_OUTLINE = (112, 84, 96)
PET_INNER_EAR = (255, 182, 196)
PET_BLUSH = (255, 190, 200)
PET_FEATURE = (70, 52, 64)
PET_MOUTH = (182, 72, 98)
PET_TONGUE = (255, 150, 170)
PET_DROOL = (160, 205, 240)
GROUND_SHADOW = (228, 214, 234)

FONT_NAMES = "segoeui,verdana,arial"


class Fonts:
    """All fonts, loaded once at startup (loading fonts every frame is slow)."""

    def __init__(self):
        self.title = pygame.font.SysFont(FONT_NAMES, 28, bold=True)
        self.button = pygame.font.SysFont(FONT_NAMES, 22, bold=True)
        self.body = pygame.font.SysFont(FONT_NAMES, 18)
        self.badge = pygame.font.SysFont(FONT_NAMES, 16, bold=True)
        self.small = pygame.font.SysFont(FONT_NAMES, 15)


# ---- Small helpers ----

def mix(a, b, t):
    """Blend colour `a` toward colour `b` by `t` (0..1)."""
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def make_gradient(size, top, bottom):
    """Build a vertical gradient surface once, to reuse as the background."""
    width, height = size
    surface = pygame.Surface(size)
    for y in range(height):
        pygame.draw.line(surface, mix(top, bottom, y / max(1, height - 1)), (0, y), (width, y))
    return surface


def wrap_text(font, text, max_width):
    """Split text into lines that fit inside `max_width` pixels."""
    lines, current = [], ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if font.size(trial)[0] <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_curve(surface, color, center, radii, start, end, width, steps=24):
    """Draw a smooth, round-capped arc by stamping small circles along it.

    Angles are in radians on screen: 0..pi is the lower half, pi..2pi the upper.
    """
    cx, cy = center
    rx, ry = radii
    for i in range(steps + 1):
        a = start + (end - start) * i / steps
        pygame.draw.circle(surface, color, (cx + rx * math.cos(a), cy + ry * math.sin(a)), width / 2)


# ---- Widgets ----

class Button:
    """A rounded button with hover and press feedback."""

    def __init__(self, rect, label, color, font):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.color = color
        self.font = font
        self.hovered = False
        self.pressed = False

    def handle_event(self, event):
        """Return True when the button is clicked (pressed and released on it)."""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            clicked = self.pressed and self.rect.collidepoint(event.pos)
            self.pressed = False
            return clicked
        return False

    def draw(self, surface):
        radius = self.rect.height // 2
        pygame.draw.rect(surface, mix(self.color, (0, 0, 0), 0.18), self.rect.move(0, 4), border_radius=radius)
        body = self.rect.move(0, 3 if self.pressed else 0)
        color = mix(self.color, WHITE, 0.15) if self.hovered else self.color
        pygame.draw.rect(surface, color, body, border_radius=radius)
        label = self.font.render(self.label, True, WHITE)
        surface.blit(label, label.get_rect(center=body.center))


def draw_panel(surface, rect, radius=18):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, PANEL_SHADOW, rect.move(0, 4), border_radius=radius)
    pygame.draw.rect(surface, WHITE, rect, border_radius=radius)


def draw_pill(surface, font, text, color, topright):
    """A small rounded badge, e.g. the level indicator."""
    label = font.render(text, True, WHITE)
    rect = label.get_rect().inflate(26, 10)
    rect.topright = topright
    pygame.draw.rect(surface, color, rect, border_radius=rect.height // 2)
    surface.blit(label, label.get_rect(center=rect.center))


def draw_stat(surface, font, pos, width, label, fraction, value_text, color):
    """A labelled progress bar. `fraction` is 0.0 (empty) to 1.0 (full)."""
    x, y = pos
    surface.blit(font.render(label, True, TEXT), (x, y))
    value = font.render(value_text, True, TEXT_SOFT)
    surface.blit(value, value.get_rect(topright=(x + width, y)))

    bar = pygame.Rect(x, y + font.get_linesize() + 2, width, 12)
    pygame.draw.rect(surface, BAR_BG, bar, border_radius=6)
    fill = round(bar.width * max(0.0, min(1.0, fraction)))
    if fill > 0:
        # Never draw narrower than the bar is tall, so the rounded ends look right.
        pygame.draw.rect(surface, color, (bar.x, bar.y, max(fill, bar.height), bar.height), border_radius=6)


def draw_speech_bubble(surface, font, text, anchor, alpha=255, max_width=300):
    """Draw a speech bubble whose tail points at `anchor` (x, y)."""
    lines = wrap_text(font, text, max_width)
    if not lines:
        return
    line_h = font.get_linesize()
    pad_x, pad_y, tail = 16, 10, 12
    width = max(font.size(line)[0] for line in lines) + pad_x * 2
    height = line_h * len(lines) + pad_y * 2

    bubble = pygame.Surface((width, height + tail + 4), pygame.SRCALPHA)
    body = pygame.Rect(0, 0, width, height)
    mid = width // 2
    pygame.draw.rect(bubble, PANEL_SHADOW, body.move(0, 3), border_radius=14)
    pygame.draw.rect(bubble, WHITE, body, border_radius=14)
    pygame.draw.polygon(bubble, WHITE, [(mid - 9, height - 2), (mid + 9, height - 2), (mid, height + tail)])
    for i, line in enumerate(lines):
        img = font.render(line, True, TEXT)
        bubble.blit(img, img.get_rect(midtop=(mid, pad_y + i * line_h)))

    bubble.set_alpha(alpha)
    surface.blit(bubble, bubble.get_rect(midbottom=anchor))


# ---- The pet ----

# (bob speed, bob height in px) for each mood
MOTION = {
    "happy": (6.0, 12),
    "content": (2.4, 5),
    "hungry": (3.2, 4),
    "sad": (1.4, 3),
    "tired": (1.0, 3),
}


class PetRenderer:
    """Draws the placeholder pet using simple shapes.

    Want custom pixel art later? Replace `draw` with code that picks an image
    from assets/sprites based on `mood` and blits it at `center`. The rest of
    the game only calls `draw(...)`, so nothing else needs to change.
    """

    BODY_W = 190
    BODY_H = 160

    def __init__(self, z_font):
        self.z_font = z_font

    def draw(self, surface, mood, center, t, scale=1.0):
        cx, cy = center
        s = scale
        speed, height = MOTION.get(mood, MOTION["content"])
        wave = math.sin(t * speed)
        # Happy pets hop; everyone else gently breathes up and down.
        lift = abs(wave) * height if mood == "happy" else (wave + 1) / 2 * height
        squash = 0.035 * wave
        w = self.BODY_W * s * (1 + squash)
        h = self.BODY_H * s * (1 - squash)
        bx, by = cx, cy - lift

        # Ground shadow shrinks as the pet lifts off the ground.
        shadow = pygame.Rect(0, 0, self.BODY_W * s * 0.8 * (1 - lift / 80), 18 * s)
        shadow.center = (cx, cy + self.BODY_H * s / 2 + 6 * s)
        pygame.draw.ellipse(surface, GROUND_SHADOW, shadow)

        self._draw_ears(surface, bx, by, w, h)

        body = pygame.Rect(0, 0, w, h)
        body.center = (bx, by)
        pygame.draw.ellipse(surface, PET_OUTLINE, body.inflate(6, 6))
        pygame.draw.ellipse(surface, PET_BODY, body)

        belly = pygame.Rect(0, 0, w * 0.5, h * 0.34)
        belly.center = (bx, by + h * 0.24)
        pygame.draw.ellipse(surface, PET_BELLY, belly)

        for side in (-1, 1):
            paw = pygame.Rect(0, 0, 40 * s, 20 * s)
            paw.center = (bx + side * w * 0.22, by + h * 0.44)
            pygame.draw.ellipse(surface, PET_OUTLINE, paw.inflate(6, 6))
            pygame.draw.ellipse(surface, PET_BODY, paw)

        self._draw_face(surface, mood, bx, by, w, h, t, s)

    def _draw_ears(self, surface, bx, by, w, h):
        for side in (-1, 1):
            points = [
                (bx + side * w * 0.45, by - h * 0.18),  # outer base (hidden in the head)
                (bx + side * w * 0.33, by - h * 0.70),  # tip
                (bx + side * w * 0.08, by - h * 0.44),  # inner base (hidden in the head)
            ]
            pygame.draw.polygon(surface, PET_BODY, points)
            pygame.draw.polygon(surface, PET_OUTLINE, points, width=3)
            mx = sum(p[0] for p in points) / 3
            my = sum(p[1] for p in points) / 3
            inner = [(x + (mx - x) * 0.45, y + (my - y) * 0.45) for x, y in points]
            pygame.draw.polygon(surface, PET_INNER_EAR, inner)

    def _draw_face(self, surface, mood, bx, by, w, h, t, s):
        eye_y = by - h * 0.08
        blink = mood not in ("happy", "tired") and (t % 3.7) < 0.13

        for side in (-1, 1):
            blush = pygame.Rect(0, 0, 26 * s, 12 * s)
            blush.center = (bx + side * w * 0.31, eye_y + 20 * s)
            pygame.draw.ellipse(surface, PET_BLUSH, blush)
            self._draw_eye(surface, mood, bx + side * w * 0.19, eye_y, side, blink, s)

        self._draw_mouth(surface, mood, bx, eye_y + 22 * s, s)

        if mood == "tired":
            for i in range(3):
                phase = (t * 0.5 + i / 3) % 1
                z = self.z_font.render("z", True, TEXT_SOFT)
                z.set_alpha(round(255 * (1 - phase)))
                surface.blit(z, z.get_rect(center=(bx + w * 0.42 + phase * 24 * s, by - h * 0.45 - phase * 46 * s)))

    def _draw_eye(self, surface, mood, ex, ey, side, blink, s):
        if mood == "happy":
            # Closed, smiling eyes: ^ ^
            draw_curve(surface, PET_FEATURE, (ex, ey + 4 * s), (10 * s, 9 * s), math.pi, 2 * math.pi, 4 * s)
        elif mood == "tired" or blink:
            y = ey + (3 * s if mood == "tired" else 0)
            pygame.draw.line(surface, PET_FEATURE, (ex - 10 * s, y), (ex + 10 * s, y), max(2, round(4 * s)))
        else:
            eye = pygame.Rect(0, 0, 16 * s, 22 * s)
            eye.center = (ex, ey)
            pygame.draw.ellipse(surface, PET_FEATURE, eye)
            pygame.draw.circle(surface, WHITE, (ex + 3 * s, ey - 5 * s), 3.5 * s)
            if mood == "sad":
                # Brows tilt up toward the middle of the face.
                pygame.draw.line(surface, PET_FEATURE, (ex + side * 12 * s, ey - 16 * s),
                                 (ex - side * 6 * s, ey - 22 * s), max(2, round(3 * s)))

    def _draw_mouth(self, surface, mood, mx, my, s):
        if mood == "happy":
            points = [(mx + 13 * s * math.cos(a), my - 2 * s + 12 * s * math.sin(a))
                      for a in (math.pi * i / 16 for i in range(17))]
            pygame.draw.polygon(surface, PET_MOUTH, points)
            tongue = pygame.Rect(0, 0, 12 * s, 6 * s)
            tongue.center = (mx, my + 5 * s)
            pygame.draw.ellipse(surface, PET_TONGUE, tongue)
        elif mood == "hungry":
            mouth = pygame.Rect(0, 0, 14 * s, 16 * s)
            mouth.center = (mx, my + 2 * s)
            pygame.draw.ellipse(surface, PET_MOUTH, mouth)
            drool = pygame.Rect(0, 0, 6 * s, 9 * s)
            drool.center = (mx + 8 * s, my + 12 * s)
            pygame.draw.ellipse(surface, PET_DROOL, drool)
        elif mood == "sad":
            draw_curve(surface, PET_FEATURE, (mx, my + 7 * s), (9 * s, 6 * s), math.pi, 2 * math.pi, 3 * s)
        elif mood == "tired":
            draw_curve(surface, PET_FEATURE, (mx, my), (5 * s, 3 * s), 0, math.pi, 3 * s)
        else:
            # Content: a little "w" cat mouth.
            for dx in (-6, 6):
                draw_curve(surface, PET_FEATURE, (mx + dx * s, my), (6 * s, 5 * s), 0, math.pi, 3 * s)
