"""Drawing helpers: colours, fonts, buttons, stat bars, speech bubbles and the pet.

Nothing in here changes game state. It only draws what it is given.
"""

import math
from dataclasses import dataclass

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
GOLD = (255, 206, 92)

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

COOKIE = (222, 166, 104)
COOKIE_DARK = (150, 96, 60)
COOKIE_CHIP = (98, 62, 48)

BOW = (255, 112, 150)
COLLAR = (226, 84, 108)
GOLD_DARK = (214, 158, 46)
GEM = (132, 164, 248)

FONT_NAMES = "segoeui,verdana,arial"


class Fonts:
    """All fonts, loaded once at startup (loading fonts every frame is slow)."""

    def __init__(self):
        self.banner = pygame.font.SysFont(FONT_NAMES, 30, bold=True)
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


def set_hand_cursor(on):
    """Show a pointing-hand cursor over clickable things."""
    try:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if on else pygame.SYSTEM_CURSOR_ARROW)
    except pygame.error:
        pass  # some systems don't support system cursors; not important


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


class SoundButton(Button):
    """A small round button with a speaker icon that toggles sound."""

    def __init__(self, rect):
        super().__init__(rect, "", WHITE, None)
        self.muted = False

    def draw(self, surface):
        radius = self.rect.width // 2
        center = (self.rect.centerx, self.rect.centery + (2 if self.pressed else 0))
        pygame.draw.circle(surface, PANEL_SHADOW, (self.rect.centerx, self.rect.centery + 3), radius)
        pygame.draw.circle(surface, mix(WHITE, BAR_BG, 0.8) if self.hovered else WHITE, center, radius)

        x, y = center[0] - 6, center[1]
        pygame.draw.polygon(surface, TEXT, [(x - 5, y - 4), (x - 1, y - 4), (x + 4, y - 8),
                                            (x + 4, y + 8), (x - 1, y + 4), (x - 5, y + 4)])
        if self.muted:
            pygame.draw.line(surface, TEXT, (x + 8, y - 4), (x + 15, y + 4), 2)
            pygame.draw.line(surface, TEXT, (x + 8, y + 4), (x + 15, y - 4), 2)
        else:
            draw_curve(surface, TEXT, (x + 5, y), (5, 5), -math.pi / 3, math.pi / 3, 2, steps=10)
            draw_curve(surface, TEXT, (x + 5, y), (10, 10), -math.pi / 3, math.pi / 3, 2, steps=14)


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

# What each evolution stage looks like (index = Pet.stage).
STAGE_LOOKS = [
    {"scale": 0.8},                                         # Baby
    {"scale": 0.9, "bow": True},                            # Junior
    {"scale": 1.0, "bow": True, "bell": True},              # Adult
    {"scale": 1.06, "bell": True, "crown": True},           # Royal
]


def stage_look(stage):
    return STAGE_LOOKS[max(0, min(stage, len(STAGE_LOOKS) - 1))]


# How long each one-off animation lasts, in seconds.
ACTION_DURATIONS = {
    "eating": 1.2,
    "playing": 1.3,
    "petted": 0.9,
    "refuse": 0.6,
}


@dataclass
class Pose:
    """How the pet looks in one frame. Animations are just poses that change over time."""

    lift: float = 0.0       # pixels above the ground
    sx: float = 1.0         # horizontal stretch (squash and stretch)
    sy: float = 1.0         # vertical stretch
    angle: float = 0.0      # rotation in degrees (counter-clockwise)
    dx: float = 0.0         # sideways shake
    eyes: str = "open"      # open, happy, closed, sad
    mouth: str = "w"        # w, smile, chomp, open, frown, small
    look: float = 0.0       # where the eyes look: -1 left .. 1 right
    blush: float = 1.0      # blush size
    drool: bool = False
    tear: float = -1.0      # 0..1 while a tear is falling, otherwise negative
    zs: bool = False        # floating "z z z"
    food: float = 0.0       # how much cookie is left (0 = no cookie)


def idle_pose(mood, t):
    """The looping animation for each mood. `t` is time in seconds."""
    breathe = math.sin(t * 2.4)
    if mood == "happy":
        hop = math.sin(t * 6.0)
        return Pose(lift=abs(hop) * 12, sx=1 + 0.035 * hop, sy=1 - 0.035 * hop,
                    eyes="happy", mouth="smile")
    if mood == "hungry":
        rumbling = (t % 4.0) < 0.5  # tummy rumble every few seconds
        return Pose(lift=(breathe + 1) * 1.5, sx=1 + 0.02 * breathe, sy=1 - 0.02 * breathe,
                    dx=math.sin(t * 50) * 2.5 if rumbling else 0.0, mouth="open", drool=True)
    if mood == "tired":
        slow = math.sin(t * 1.0)
        return Pose(lift=(slow + 1) * 1.5, sx=1 + 0.03 * slow, sy=1 - 0.03 * slow,
                    angle=math.sin(t * 0.5) * 4, eyes="closed", mouth="small", zs=True)
    if mood == "sad":
        slow = math.sin(t * 1.4)
        tear = (t % 5.0) / 3.0  # a tear rolls down for 3 of every 5 seconds
        return Pose(lift=(slow + 1) * 1.5, sx=1.02 + 0.02 * slow, sy=0.97 - 0.02 * slow,
                    eyes="sad", mouth="frown", tear=tear if tear <= 1 else -1.0)
    # content: gentle breathing, glancing around now and then
    return Pose(lift=(breathe + 1) * 2.5, sx=1 + 0.035 * breathe, sy=1 - 0.035 * breathe,
                look=math.sin(t * 0.5) ** 5)


def action_pose(action, p):
    """One-off animations. `p` is progress from 0.0 to 1.0."""
    if action == "eating":
        bite = int(p * 6)
        chewing = bite % 2 == 1
        return Pose(sx=1.04 if chewing else 1.0, sy=0.95 if chewing else 1.0, eyes="happy",
                    mouth="w" if chewing else "chomp", food=max(0.0, 1 - bite / 5))
    if action == "playing":
        if p < 0.1:  # crouch before jumping
            return Pose(sx=1.08, sy=0.9, eyes="happy", mouth="smile")
        q = (p - 0.1) / 0.9
        spin = q * q * (3 - 2 * q)  # ease in and out
        landing = q > 0.88
        return Pose(lift=math.sin(math.pi * q) * 55, angle=-360 * spin,
                    sx=1.08 if landing else 0.96, sy=0.9 if landing else 1.06,
                    eyes="happy", mouth="smile")
    if action == "petted":
        wobble = math.sin(p * math.pi * 5) * (1 - p) * 0.08
        return Pose(sx=1 + wobble, sy=1 - wobble, eyes="happy", mouth="smile", blush=1.5)
    if action == "refuse":
        return Pose(dx=math.sin(p * math.pi * 6) * 7 * (1 - p), eyes="closed", mouth="frown")
    return Pose()


class PetRenderer:
    """Draws the placeholder pet using simple shapes.

    Want custom pixel art later? Replace `draw` with code that picks an image
    from assets/sprites based on `mood`, `action` and `stage`, and blits it
    standing at `ground`. The rest of the game only calls `draw(...)` and
    `contains(...)`, so nothing else needs to change.
    """

    BODY_W = 190
    BODY_H = 160

    def __init__(self, z_font):
        self.z_font = z_font

    def draw(self, surface, mood, ground, t, stage=0, action=None, progress=0.0):
        """Draw the pet with its feet at `ground` (x, y)."""
        pose = action_pose(action, progress) if action else idle_pose(mood, t)
        look = stage_look(stage)
        s = look["scale"]
        cx, ground_y = ground
        w = self.BODY_W * s * pose.sx
        h = self.BODY_H * s * pose.sy

        # Ground shadow shrinks as the pet lifts off the ground.
        shadow = pygame.Rect(0, 0, self.BODY_W * s * 0.8 * max(0.35, 1 - pose.lift / 110), 18 * s)
        shadow.center = (cx, ground_y + 6 * s)
        pygame.draw.ellipse(surface, GROUND_SHADOW, shadow)

        # Draw the pet on its own transparent canvas so the whole thing can rotate.
        size = round(300 * s)
        canvas = pygame.Surface((size, size), pygame.SRCALPHA)
        self._draw_pet(canvas, pose, look, size / 2, size / 2, w, h, t, s)
        if pose.angle:
            canvas = pygame.transform.rotozoom(canvas, pose.angle, 1.0)

        # Keep the feet on the ground when squashed: move the centre down.
        body_y = ground_y - h / 2 - pose.lift
        surface.blit(canvas, canvas.get_rect(center=(cx + pose.dx, body_y)))

        if pose.zs:
            for i in range(3):
                phase = (t * 0.5 + i / 3) % 1
                z = self.z_font.render("z", True, TEXT_SOFT)
                z.set_alpha(round(255 * (1 - phase)))
                surface.blit(z, z.get_rect(center=(cx + w * 0.42 + phase * 24 * s,
                                                  body_y - h * 0.45 - phase * 46 * s)))

    def contains(self, ground, pos, stage=0):
        """True if screen position `pos` is on the pet (for click detection)."""
        s = stage_look(stage)["scale"]
        cx, ground_y = ground
        rx = self.BODY_W * s / 2 + 6
        ry = self.BODY_H * s / 2 + 14  # a little extra on top for the ears
        dx, dy = pos[0] - cx, pos[1] - (ground_y - self.BODY_H * s / 2 - 8 * s)
        return (dx / rx) ** 2 + (dy / ry) ** 2 <= 1

    def mouth_position(self, ground, stage=0):
        """Roughly where the mouth is, for crumbs while eating."""
        s = stage_look(stage)["scale"]
        return (ground[0] + 20 * s, ground[1] - self.BODY_H * s / 2 + 12 * s)

    # ---- Body parts ----

    def _draw_pet(self, canvas, pose, look, bx, by, w, h, t, s):
        self._draw_ears(canvas, bx, by, w, h)

        body = pygame.Rect(0, 0, w, h)
        body.center = (bx, by)
        pygame.draw.ellipse(canvas, PET_OUTLINE, body.inflate(6, 6))
        pygame.draw.ellipse(canvas, PET_BODY, body)

        belly = pygame.Rect(0, 0, w * 0.5, h * 0.34)
        belly.center = (bx, by + h * 0.24)
        pygame.draw.ellipse(canvas, PET_BELLY, belly)

        for side in (-1, 1):
            paw = pygame.Rect(0, 0, 40 * s, 20 * s)
            paw.center = (bx + side * w * 0.22, by + h * 0.44)
            pygame.draw.ellipse(canvas, PET_OUTLINE, paw.inflate(6, 6))
            pygame.draw.ellipse(canvas, PET_BODY, paw)

        if look.get("bell"):
            self._draw_bell_collar(canvas, bx, by, w, h, s)
        self._draw_face(canvas, pose, bx, by, w, h, t, s)
        if look.get("crown"):
            self._draw_crown(canvas, bx, by - h * 0.47, s)
        if look.get("bow"):
            self._draw_bow(canvas, bx + w * 0.30, by - h * 0.43, s)

    # ---- Accessories (unlocked by evolving) ----

    def _draw_bow(self, canvas, x, y, s):
        for side in (-1, 1):
            loop = [(x, y), (x + side * 16 * s, y - 10 * s), (x + side * 16 * s, y + 10 * s)]
            pygame.draw.polygon(canvas, BOW, loop)
            pygame.draw.polygon(canvas, PET_OUTLINE, loop, width=2)
        pygame.draw.circle(canvas, PET_OUTLINE, (x, y), 6 * s)
        pygame.draw.circle(canvas, BOW, (x, y), 4.5 * s)

    def _draw_bell_collar(self, canvas, bx, by, w, h, s):
        center, radii = (bx, by + h * 0.02), (w * 0.27, h * 0.2)
        draw_curve(canvas, PET_OUTLINE, center, radii, math.pi * 0.2, math.pi * 0.8, 10 * s)
        draw_curve(canvas, COLLAR, center, radii, math.pi * 0.2, math.pi * 0.8, 7 * s)
        bell = (bx, by + h * 0.22 + 6 * s)
        pygame.draw.circle(canvas, GOLD_DARK, bell, 9 * s)
        pygame.draw.circle(canvas, GOLD, bell, 7.5 * s)
        pygame.draw.line(canvas, GOLD_DARK, (bell[0], bell[1] + 1 * s), (bell[0], bell[1] + 7 * s), 2)

    def _draw_crown(self, canvas, x, base_y, s):
        half, tall = 26 * s, 26 * s
        points = [(x - half, base_y), (x - half, base_y - tall * 0.75), (x - half * 0.5, base_y - tall * 0.4),
                  (x, base_y - tall), (x + half * 0.5, base_y - tall * 0.4), (x + half, base_y - tall * 0.75),
                  (x + half, base_y)]
        pygame.draw.polygon(canvas, GOLD, points)
        pygame.draw.polygon(canvas, GOLD_DARK, points, width=2)
        pygame.draw.circle(canvas, GEM, (x, base_y - tall * 0.35), 4 * s)
        for side in (-1, 1):
            pygame.draw.circle(canvas, HAPPY_COLOR, (x + side * half * 0.62, base_y - tall * 0.22), 3 * s)

    def _draw_ears(self, canvas, bx, by, w, h):
        for side in (-1, 1):
            points = [
                (bx + side * w * 0.45, by - h * 0.18),  # outer base (hidden in the head)
                (bx + side * w * 0.33, by - h * 0.70),  # tip
                (bx + side * w * 0.08, by - h * 0.44),  # inner base (hidden in the head)
            ]
            pygame.draw.polygon(canvas, PET_BODY, points)
            pygame.draw.polygon(canvas, PET_OUTLINE, points, width=3)
            mx = sum(p[0] for p in points) / 3
            my = sum(p[1] for p in points) / 3
            inner = [(x + (mx - x) * 0.45, y + (my - y) * 0.45) for x, y in points]
            pygame.draw.polygon(canvas, PET_INNER_EAR, inner)

    def _draw_face(self, canvas, pose, bx, by, w, h, t, s):
        eye_y = by - h * 0.08
        eyes = pose.eyes
        if eyes in ("open", "sad") and (t % 3.7) < 0.13:
            eyes = "closed"  # blink

        for side in (-1, 1):
            blush = pygame.Rect(0, 0, 26 * s * pose.blush, 12 * s * pose.blush)
            blush.center = (bx + side * w * 0.31, eye_y + 20 * s)
            pygame.draw.ellipse(canvas, PET_BLUSH, blush)
            self._draw_eye(canvas, eyes, bx + side * w * 0.19, eye_y, side, pose.look, s)

        mouth_y = eye_y + 22 * s
        self._draw_mouth(canvas, pose.mouth, bx, mouth_y, s)

        if pose.drool:
            drool = pygame.Rect(0, 0, 6 * s, 9 * s)
            drool.center = (bx + 8 * s, mouth_y + 12 * s)
            pygame.draw.ellipse(canvas, PET_DROOL, drool)
        if 0 <= pose.tear <= 1:
            size = 7 * s * (1 - pose.tear * 0.4)
            tear = pygame.Rect(0, 0, size, size * 1.4)
            tear.center = (bx - w * 0.21, eye_y + 12 * s + pose.tear * 34 * s)
            pygame.draw.ellipse(canvas, PET_DROOL, tear)
        if pose.food > 0:
            self._draw_cookie(canvas, bx + 24 * s, mouth_y + 8 * s, pose.food, s)

    def _draw_eye(self, canvas, eyes, ex, ey, side, look, s):
        if eyes == "happy":
            # Closed, smiling eyes: ^ ^
            draw_curve(canvas, PET_FEATURE, (ex, ey + 4 * s), (10 * s, 9 * s), math.pi, 2 * math.pi, 4 * s)
        elif eyes == "closed":
            pygame.draw.line(canvas, PET_FEATURE, (ex - 10 * s, ey + 2 * s), (ex + 10 * s, ey + 2 * s),
                             max(2, round(4 * s)))
        else:
            ex += look * 4 * s
            eye = pygame.Rect(0, 0, 16 * s, 22 * s)
            eye.center = (ex, ey)
            pygame.draw.ellipse(canvas, PET_FEATURE, eye)
            pygame.draw.circle(canvas, WHITE, (ex + 3 * s, ey - 5 * s), 3.5 * s)
            if eyes == "sad":
                # Brows tilt up toward the middle of the face.
                pygame.draw.line(canvas, PET_FEATURE, (ex + side * 12 * s, ey - 16 * s),
                                 (ex - side * 6 * s, ey - 22 * s), max(2, round(3 * s)))

    def _draw_mouth(self, canvas, mouth, mx, my, s):
        if mouth in ("smile", "chomp"):
            depth = 12 if mouth == "smile" else 17
            points = [(mx + 13 * s * math.cos(a), my - 2 * s + depth * s * math.sin(a))
                      for a in (math.pi * i / 16 for i in range(17))]
            pygame.draw.polygon(canvas, PET_MOUTH, points)
            tongue = pygame.Rect(0, 0, 12 * s, 6 * s)
            tongue.center = (mx, my + (depth - 7) * s)
            pygame.draw.ellipse(canvas, PET_TONGUE, tongue)
        elif mouth == "open":
            hole = pygame.Rect(0, 0, 14 * s, 16 * s)
            hole.center = (mx, my + 2 * s)
            pygame.draw.ellipse(canvas, PET_MOUTH, hole)
        elif mouth == "frown":
            draw_curve(canvas, PET_FEATURE, (mx, my + 7 * s), (9 * s, 6 * s), math.pi, 2 * math.pi, 3 * s)
        elif mouth == "small":
            draw_curve(canvas, PET_FEATURE, (mx, my), (5 * s, 3 * s), 0, math.pi, 3 * s)
        else:
            # "w": a little cat mouth.
            for dx in (-6, 6):
                draw_curve(canvas, PET_FEATURE, (mx + dx * s, my), (6 * s, 5 * s), 0, math.pi, 3 * s)

    def _draw_cookie(self, canvas, x, y, amount, s):
        r = 15 * s * math.sqrt(amount)
        if r < 2:
            return
        pygame.draw.circle(canvas, COOKIE_DARK, (x, y), r + 2)
        pygame.draw.circle(canvas, COOKIE, (x, y), r)
        for ox, oy in ((-0.4, -0.3), (0.35, -0.1), (-0.05, 0.4)):
            pygame.draw.circle(canvas, COOKIE_CHIP, (x + ox * r, y + oy * r), max(1.0, r * 0.16))
