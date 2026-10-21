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


class IconButton(Button):
    """A small round button with a drawn icon: "sound", "muted" or "paw"."""

    def __init__(self, rect, icon):
        super().__init__(rect, "", WHITE, None)
        self.icon = icon

    def draw(self, surface):
        radius = self.rect.width // 2
        center = (self.rect.centerx, self.rect.centery + (2 if self.pressed else 0))
        pygame.draw.circle(surface, PANEL_SHADOW, (self.rect.centerx, self.rect.centery + 3), radius)
        pygame.draw.circle(surface, mix(WHITE, BAR_BG, 0.8) if self.hovered else WHITE, center, radius)
        draw_icon(surface, self.icon, center)


def draw_icon(surface, icon, center, color=TEXT):
    """Small hand-drawn icons, about 20 px across."""
    cx, cy = center
    if icon in ("sound", "muted"):
        x, y = cx - 6, cy
        pygame.draw.polygon(surface, color, [(x - 5, y - 4), (x - 1, y - 4), (x + 4, y - 8),
                                             (x + 4, y + 8), (x - 1, y + 4), (x - 5, y + 4)])
        if icon == "muted":
            pygame.draw.line(surface, color, (x + 8, y - 4), (x + 15, y + 4), 2)
            pygame.draw.line(surface, color, (x + 8, y + 4), (x + 15, y - 4), 2)
        else:
            draw_curve(surface, color, (x + 5, y), (5, 5), -math.pi / 3, math.pi / 3, 2, steps=10)
            draw_curve(surface, color, (x + 5, y), (10, 10), -math.pi / 3, math.pi / 3, 2, steps=14)
    elif icon == "hanger":
        draw_curve(surface, color, (cx + 1, cy - 8), (3.5, 3.5), math.pi * 0.9, math.pi * 2.4, 2, steps=10)
        pygame.draw.lines(surface, color, True, [(cx, cy - 4), (cx - 10, cy + 6), (cx + 10, cy + 6)], 2)
    elif icon == "paw":
        pygame.draw.ellipse(surface, color, (cx - 6, cy - 1, 12, 9))
        for dx, dy in ((-7, -4), (-2.5, -8), (2.5, -8), (7, -4)):
            pygame.draw.circle(surface, color, (cx + dx, cy + dy), 2.6)


def draw_panel(surface, rect, radius=18):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, PANEL_SHADOW, rect.move(0, 4), border_radius=radius)
    pygame.draw.rect(surface, WHITE, rect, border_radius=radius)


def draw_pill(surface, font, text, color, topright):
    """A small rounded badge, e.g. the level indicator. Returns where it was drawn."""
    label = font.render(text, True, WHITE)
    rect = label.get_rect().inflate(26, 10)
    rect.topright = topright
    pygame.draw.rect(surface, color, rect, border_radius=rect.height // 2)
    surface.blit(label, label.get_rect(center=rect.center))
    return rect


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

# How big the pet is at each evolution stage (index = Pet.stage).
# Accessories are chosen in the wardrobe, not by stage.
STAGE_LOOKS = [
    {"scale": 0.8},    # Baby
    {"scale": 0.9},    # Junior
    {"scale": 1.0},    # Adult
    {"scale": 1.06},   # Royal
]

# The colours wardrobe items can come in (names match wardrobe.COLORS).
OUTFIT_RGB = {
    "pink": (255, 138, 178),
    "red": (232, 86, 96),
    "orange": (255, 160, 90),
    "yellow": (255, 206, 92),
    "green": (120, 200, 140),
    "blue": (110, 160, 240),
    "purple": (168, 136, 240),
}


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




# What each kind of pet looks like. Colours are (red, green, blue).
SPECIES_LOOKS = {
    # A fluffy tan pup: floppy dark-tipped ears, topknot, cream muzzle, wagging tail.
    "dog": {
        "body": (232, 196, 150), "belly": (248, 236, 214), "outline": PET_OUTLINE,
        "ears": "floppy", "ear_tip": (104, 76, 60), "fluff": True,
        "muzzle": (240, 222, 198), "nose": (48, 38, 40), "nose_shape": "button",
        "tail": "fluffy", "blush_x": 0.26, "mouth_drop": 5,
    },
    # A soft gray cat: pointy ears, forehead stripes, pink nose, whiskers, curvy tail.
    "cat": {
        "body": (182, 184, 196), "belly": (226, 227, 234), "outline": (92, 86, 104),
        "ears": "pointy", "inner_ear": PET_INNER_EAR, "stripes": (142, 144, 160),
        "nose": (240, 150, 170), "nose_shape": "triangle", "whiskers": (118, 116, 132),
        "tail": "thin", "blush_x": 0.31, "mouth_drop": 0,
    },
    # A white bunny: tall ears, pink nose, little teeth, cotton tail.
    "bunny": {
        "body": (250, 246, 240), "belly": WHITE, "outline": PET_OUTLINE,
        "ears": "long", "inner_ear": PET_INNER_EAR,
        "nose": (244, 150, 170), "nose_shape": "oval", "teeth": True,
        "tail": "puff", "blush_x": 0.31, "mouth_drop": 3,
    },
}


def species_look(species):
    return SPECIES_LOOKS.get(species, SPECIES_LOOKS["dog"])


class PetRenderer:
    """Draws the pet using simple shapes.

    Want custom pixel art later? Replace `draw` with code that picks an image
    from assets/sprites based on `species`, `mood`, `action` and `stage`, and
    blits it standing at `ground`. The rest of the game only calls `draw(...)`
    and `contains(...)`, so nothing else needs to change.
    """

    BODY_W = 190
    BODY_H = 160

    def __init__(self, z_font):
        self.z_font = z_font

    def draw(self, surface, mood, ground, t, stage=0, action=None, progress=0.0, zoom=1.0,
             shadow=True, species="dog", outfit=None):
        """Draw the pet with its feet at `ground` (x, y).

        `zoom` shrinks or grows the whole pet (the companion window uses a small
        pet). `shadow=False` skips the ground shadow. `outfit` is a
        wardrobe.Outfit (or None for no clothes).
        """
        pose = action_pose(action, progress) if action else idle_pose(mood, t)
        look = stage_look(stage)
        kind = species_look(species)
        s = look["scale"] * zoom
        cx, ground_y = ground
        w = self.BODY_W * s * pose.sx
        h = self.BODY_H * s * pose.sy
        lift = pose.lift * s
        dx = pose.dx * s

        if shadow:
            # Ground shadow shrinks as the pet lifts off the ground.
            shade = pygame.Rect(0, 0, self.BODY_W * s * 0.8 * max(0.35, 1 - lift / 110), 18 * s)
            shade.center = (cx, ground_y + 6 * s)
            pygame.draw.ellipse(surface, GROUND_SHADOW, shade)

        # Draw the pet on its own transparent canvas so the whole thing can rotate.
        # (Tall enough for bunny ears and a crown.)
        size = round(380 * s)
        canvas = pygame.Surface((size, size), pygame.SRCALPHA)
        worn = {slot: (key, color) for slot, key, color in outfit.worn()} if outfit else {}
        self._draw_pet(canvas, pose, kind, worn, size / 2, size / 2, w, h, t, s)
        if pose.angle:
            canvas = pygame.transform.rotozoom(canvas, pose.angle, 1.0)

        # Keep the feet on the ground when squashed: move the centre down.
        body_y = ground_y - h / 2 - lift
        surface.blit(canvas, canvas.get_rect(center=(cx + dx, body_y)))

        if pose.zs:
            for i in range(3):
                phase = (t * 0.5 + i / 3) % 1
                z = self.z_font.render("z", True, TEXT_SOFT)
                z.set_alpha(round(255 * (1 - phase)))
                surface.blit(z, z.get_rect(center=(cx + w * 0.42 + phase * 24 * s,
                                                  body_y - h * 0.45 - phase * 46 * s)))

    def contains(self, ground, pos, stage=0, zoom=1.0):
        """True if screen position `pos` is on the pet (for click detection)."""
        s = stage_look(stage)["scale"] * zoom
        cx, ground_y = ground
        rx = self.BODY_W * s / 2 + 6
        ry = self.BODY_H * s / 2 + 14 * s  # a little extra on top for the ears
        dx, dy = pos[0] - cx, pos[1] - (ground_y - self.BODY_H * s / 2 - 8 * s)
        return (dx / rx) ** 2 + (dy / ry) ** 2 <= 1

    def mouth_position(self, ground, stage=0, zoom=1.0):
        """Roughly where the mouth is, for crumbs while eating."""
        s = stage_look(stage)["scale"] * zoom
        return (ground[0] + 20 * s, ground[1] - self.BODY_H * s / 2 + 12 * s)

    # ---- Body parts ----

    def _draw_pet(self, canvas, pose, kind, worn, bx, by, w, h, t, s):
        outline, body_color = kind["outline"], kind["body"]
        body_geom = Body(bx, by, w, h, s, outline)

        def wear(slot):
            if slot in worn:
                key, color = worn[slot]
                draw_outfit_item(canvas, key, OUTFIT_RGB.get(color, OUTFIT_RGB["pink"]), body_geom)

        # Things behind the head first; the body is drawn over their bases.
        self._draw_tail(canvas, kind, pose, bx, by, w, h, t, s)
        if kind["ears"] == "pointy":
            self._draw_pointy_ears(canvas, kind, bx, by, w, h)
        elif kind["ears"] == "long":
            self._draw_long_ears(canvas, kind, bx, by, w, h)
        if kind.get("fluff"):
            self._draw_topknot(canvas, kind, bx, by, w, h, s)

        body = pygame.Rect(0, 0, w, h)
        body.center = (bx, by)
        pygame.draw.ellipse(canvas, outline, body.inflate(6, 6))
        pygame.draw.ellipse(canvas, body_color, body)

        belly = pygame.Rect(0, 0, w * 0.5, h * 0.34)
        belly.center = (bx, by + h * 0.24)
        pygame.draw.ellipse(canvas, kind["belly"], belly)
        wear("body")

        for side in (-1, 1):
            paw = pygame.Rect(0, 0, 40 * s, 20 * s)
            paw.center = (bx + side * w * 0.22, by + h * 0.44)
            pygame.draw.ellipse(canvas, outline, paw.inflate(6, 6))
            pygame.draw.ellipse(canvas, body_color, paw)

        wear("neck")
        if kind["ears"] == "floppy":
            self._draw_floppy_ears(canvas, kind, bx, by, w, h)
        if kind.get("stripes"):
            for offset in (-0.07, 0, 0.07):
                x = bx + w * offset
                pygame.draw.line(canvas, kind["stripes"], (x, by - h * 0.42), (x, by - h * 0.32),
                                 max(2, round(4 * s)))
        self._draw_face(canvas, pose, kind, bx, by, w, h, t, s)
        wear("face")
        wear("head")

    def _draw_pointy_ears(self, canvas, kind, bx, by, w, h):
        for side in (-1, 1):
            points = [
                (bx + side * w * 0.45, by - h * 0.18),  # outer base (hidden in the head)
                (bx + side * w * 0.33, by - h * 0.70),  # tip
                (bx + side * w * 0.08, by - h * 0.44),  # inner base (hidden in the head)
            ]
            pygame.draw.polygon(canvas, kind["body"], points)
            pygame.draw.polygon(canvas, kind["outline"], points, width=3)
            mx = sum(p[0] for p in points) / 3
            my = sum(p[1] for p in points) / 3
            inner = [(x + (mx - x) * 0.45, y + (my - y) * 0.45) for x, y in points]
            pygame.draw.polygon(canvas, kind["inner_ear"], inner)

    def _draw_long_ears(self, canvas, kind, bx, by, w, h):
        for side in (-1, 1):
            ear = pygame.Rect(0, 0, w * 0.2, h * 0.72)
            ear.center = (bx + side * w * 0.18, by - h * 0.64)
            pygame.draw.ellipse(canvas, kind["outline"], ear.inflate(6, 6))
            pygame.draw.ellipse(canvas, kind["body"], ear)
            inner = pygame.Rect(0, 0, w * 0.09, h * 0.5)
            inner.center = (ear.centerx, ear.centery - h * 0.02)
            pygame.draw.ellipse(canvas, kind["inner_ear"], inner)

    def _draw_floppy_ears(self, canvas, kind, bx, by, w, h):
        """Long, fluffy ears hanging down the sides of the head, darker at the tips."""
        for side in (-1, 1):
            ear = pygame.Rect(0, 0, w * 0.2, h * 0.5)
            ear.center = (bx + side * w * 0.43, by - h * 0.02)
            pygame.draw.ellipse(canvas, kind["outline"], ear.inflate(6, 6))
            pygame.draw.ellipse(canvas, kind["ear_tip"], ear)
            upper = pygame.Rect(ear.x, ear.y, ear.width, h * 0.38)
            pygame.draw.ellipse(canvas, kind["body"], upper)

    def _draw_topknot(self, canvas, kind, bx, by, w, h, s):
        """A few fluffy tufts on top of the head."""
        tufts = [(-0.2, 0.43, 0.085), (-0.07, 0.48, 0.1), (0.07, 0.48, 0.1), (0.2, 0.43, 0.085)]
        for ox, oy, r in tufts:
            pygame.draw.circle(canvas, kind["outline"], (bx + w * ox, by - h * oy), w * r + 3)
        for ox, oy, r in tufts:
            pygame.draw.circle(canvas, kind["body"], (bx + w * ox, by - h * oy), w * r)

    def _draw_tail(self, canvas, kind, pose, bx, by, w, h, t, s):
        happy = pose.eyes == "happy"
        wag = math.sin(t * (14 if happy else 3)) * (1.0 if happy else 0.3)
        outline, color = kind["outline"], kind["body"]
        if kind["tail"] == "fluffy":
            puffs = [(0.43, 0.22, 0.075), (0.52, 0.08, 0.085), (0.56 + 0.04 * wag, -0.08, 0.075)]
            for ox, oy, r in puffs:
                pygame.draw.circle(canvas, outline, (bx + w * ox, by + h * oy), w * r + 3)
            for ox, oy, r in puffs:
                pygame.draw.circle(canvas, color, (bx + w * ox, by + h * oy), w * r)
        elif kind["tail"] == "thin":
            center = (bx + w * (0.46 + 0.03 * wag), by + h * 0.04)
            radii = (w * 0.13, h * 0.32)
            draw_curve(canvas, outline, center, radii, -math.pi * 0.45, math.pi * 0.5, 15 * s)
            draw_curve(canvas, color, center, radii, -math.pi * 0.45, math.pi * 0.5, 9 * s)
        elif kind["tail"] == "puff":
            center = (bx + w * 0.47, by + h * 0.26)
            pygame.draw.circle(canvas, outline, center, w * 0.09 + 3)
            pygame.draw.circle(canvas, WHITE, center, w * 0.09)

    # ---- Face ----

    def _draw_face(self, canvas, pose, kind, bx, by, w, h, t, s):
        eye_y = by - h * 0.08
        mouth_y = eye_y + (22 + kind["mouth_drop"]) * s
        eyes = pose.eyes
        if eyes in ("open", "sad") and (t % 3.7) < 0.13:
            eyes = "closed"  # blink

        if kind.get("muzzle"):
            muzzle = pygame.Rect(0, 0, w * 0.32, h * 0.26)
            muzzle.center = (bx, eye_y + 24 * s)
            pygame.draw.ellipse(canvas, kind["muzzle"], muzzle)

        for side in (-1, 1):
            blush = pygame.Rect(0, 0, 26 * s * pose.blush, 12 * s * pose.blush)
            blush.center = (bx + side * w * kind["blush_x"], eye_y + 20 * s)
            pygame.draw.ellipse(canvas, PET_BLUSH, blush)
            self._draw_eye(canvas, eyes, bx + side * w * 0.19, eye_y, side, pose.look, s)

        self._draw_mouth(canvas, pose.mouth, bx, mouth_y, s)
        if kind.get("teeth") and pose.mouth in ("w", "smile"):
            top = mouth_y + (3 if pose.mouth == "w" else -2) * s
            teeth = pygame.Rect(bx - 4 * s, top, 8 * s, 6 * s)
            pygame.draw.rect(canvas, WHITE, teeth, border_radius=max(1, round(s)))
            pygame.draw.rect(canvas, kind["outline"], teeth, width=1, border_radius=max(1, round(s)))
            pygame.draw.line(canvas, kind["outline"], (bx, top), (bx, top + 6 * s), 1)
        self._draw_nose(canvas, kind, bx, eye_y + 13 * s, s)

        if kind.get("whiskers"):
            for side in (-1, 1):
                start = (bx + side * w * 0.22, mouth_y - 2 * s)
                for lift in (-7, 2):
                    pygame.draw.line(canvas, kind["whiskers"], start,
                                     (bx + side * w * 0.43, mouth_y + lift * s), max(1, round(2 * s)))

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

    def _draw_nose(self, canvas, kind, x, y, s):
        shape, color = kind["nose_shape"], kind["nose"]
        if shape == "button":  # a shiny dog nose
            nose = pygame.Rect(0, 0, 18 * s, 12 * s)
            nose.center = (x, y)
            pygame.draw.ellipse(canvas, color, nose)
            pygame.draw.ellipse(canvas, WHITE, (x - 5 * s, y - 4 * s, 5 * s, 3 * s))
        elif shape == "triangle":  # a little cat nose
            pygame.draw.polygon(canvas, color, [(x - 5 * s, y - 2 * s), (x + 5 * s, y - 2 * s), (x, y + 3 * s)])
        else:
            nose = pygame.Rect(0, 0, 10 * s, 7 * s)
            nose.center = (x, y)
            pygame.draw.ellipse(canvas, color, nose)

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
            # "w": a little animal mouth.
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


# ---- Wardrobe items ----

@dataclass
class Body:
    """The measurements every item is placed against (canvas coordinates)."""

    bx: float       # centre of the body
    by: float
    w: float        # body width and height
    h: float
    s: float        # overall scale
    outline: tuple  # the pet's outline colour

    @property
    def eye_y(self):
        return self.by - self.h * 0.08


def draw_heart(surface, color, center, size):
    x, y = center
    r = size / 2
    pygame.draw.circle(surface, color, (x - r * 0.5, y - r * 0.25), r * 0.6)
    pygame.draw.circle(surface, color, (x + r * 0.5, y - r * 0.25), r * 0.6)
    pygame.draw.polygon(surface, color, [(x - r * 1.08, y - r * 0.05), (x + r * 1.08, y - r * 0.05),
                                         (x, y + r * 1.15)])


def draw_outfit_item(canvas, key, color, b):
    """Draw one wardrobe item (see wardrobe.ITEMS) on the pet's canvas."""
    painter = ITEM_PAINTERS.get(key)
    if painter:
        painter(canvas, color, b)


def _outlined_polygon(canvas, color, outline, points, width=2):
    pygame.draw.polygon(canvas, color, points)
    pygame.draw.polygon(canvas, outline, points, width=width)


def _outlined_circle(canvas, color, outline, center, radius, width=2):
    pygame.draw.circle(canvas, outline, center, radius + width)
    pygame.draw.circle(canvas, color, center, radius)


# Head

def _paint_bow(canvas, color, b):
    x, y, s = b.bx + b.w * 0.30, b.by - b.h * 0.43, b.s
    for side in (-1, 1):
        _outlined_polygon(canvas, color, b.outline,
                          [(x, y), (x + side * 16 * s, y - 10 * s), (x + side * 16 * s, y + 10 * s)])
    _outlined_circle(canvas, color, b.outline, (x, y), 4.5 * s)


def _paint_flower(canvas, color, b):
    x, y, s = b.bx - b.w * 0.28, b.by - b.h * 0.40, b.s
    petals = [(x + 8 * s * math.cos(a), y + 8 * s * math.sin(a))
              for a in (i * 2 * math.pi / 5 - math.pi / 2 for i in range(5))]
    for p in petals:
        pygame.draw.circle(canvas, b.outline, p, 7 * s + 2)
    for p in petals:
        pygame.draw.circle(canvas, color, p, 7 * s)
    middle = OUTFIT_RGB["orange"] if color == OUTFIT_RGB["yellow"] else GOLD
    pygame.draw.circle(canvas, middle, (x, y), 5 * s)


def _paint_party_hat(canvas, color, b):
    s, base = b.s, b.by - b.h * 0.45
    tip = (b.bx + 8 * s, base - 48 * s)
    _outlined_polygon(canvas, color, b.outline, [(b.bx - 20 * s, base), (b.bx + 20 * s, base), tip])
    for t in (0.3, 0.55, 0.78):  # polka dots up the middle
        x = b.bx + (tip[0] - b.bx) * t
        y = base + (tip[1] - base) * t
        pygame.draw.circle(canvas, WHITE, (x, y), 3.5 * s * (1.2 - t * 0.5))
    _outlined_circle(canvas, WHITE, b.outline, tip, 6 * s)


def _paint_beanie(canvas, color, b):
    s, cy = b.s, b.by - b.h * 0.42
    rx, ry = b.w * 0.33, b.h * 0.26
    dome = [(b.bx + rx * math.cos(a), cy + ry * math.sin(a))
            for a in (math.pi + math.pi * i / 20 for i in range(21))]
    _outlined_polygon(canvas, color, b.outline, dome)
    band = pygame.Rect(0, 0, b.w * 0.74, 13 * s)
    band.center = (b.bx, cy)
    pygame.draw.rect(canvas, mix(color, (0, 0, 0), 0.18), band, border_radius=round(6 * s))
    pygame.draw.rect(canvas, b.outline, band, width=2, border_radius=round(6 * s))
    _outlined_circle(canvas, mix(color, WHITE, 0.45), b.outline, (b.bx, cy - ry - 4 * s), 9 * s)


def _paint_crown(canvas, color, b):
    x, base_y, s = b.bx, b.by - b.h * 0.47, b.s
    half, tall = 26 * s, 26 * s
    points = [(x - half, base_y), (x - half, base_y - tall * 0.75), (x - half * 0.5, base_y - tall * 0.4),
              (x, base_y - tall), (x + half * 0.5, base_y - tall * 0.4), (x + half, base_y - tall * 0.75),
              (x + half, base_y)]
    pygame.draw.polygon(canvas, GOLD, points)
    pygame.draw.polygon(canvas, GOLD_DARK, points, width=2)
    pygame.draw.circle(canvas, GEM, (x, base_y - tall * 0.35), 4 * s)
    for side in (-1, 1):
        pygame.draw.circle(canvas, HAPPY_COLOR, (x + side * half * 0.62, base_y - tall * 0.22), 3 * s)


# Face

def _eye_centers(b):
    return [(b.bx + side * b.w * 0.19, b.eye_y) for side in (-1, 1)]


def _paint_temples(canvas, color, b, inner_gap):
    """The bridge between the lenses and the arms going back to the ears."""
    s = b.s
    (lx, y), (rx, _) = _eye_centers(b)
    draw_curve(canvas, color, ((lx + rx) / 2, y + 2 * s), ((rx - lx) / 2 - inner_gap, 5 * s),
               math.pi * 1.15, math.pi * 1.85, 3 * s, steps=12)
    for x, side in ((lx, -1), (rx, 1)):
        pygame.draw.line(canvas, color, (x + side * inner_gap, y - 2 * s),
                         (b.bx + side * b.w * 0.44, y - 6 * s), max(2, round(3 * s)))


def _paint_glasses(canvas, color, b):
    s = b.s
    for x, y in _eye_centers(b):
        pygame.draw.circle(canvas, color, (x, y), 15 * s, max(2, round(3 * s)))
        draw_curve(canvas, WHITE, (x, y), (10 * s, 10 * s), math.pi * 1.15, math.pi * 1.45, 2 * s, steps=6)
    _paint_temples(canvas, color, b, 15 * s)


def _paint_sunglasses(canvas, color, b):
    s, dark = b.s, (44, 38, 52)
    for x, y in _eye_centers(b):
        lens = pygame.Rect(0, 0, 34 * s, 24 * s)
        lens.center = (x, y)
        pygame.draw.rect(canvas, dark, lens, border_radius=round(9 * s))
        pygame.draw.line(canvas, WHITE, (x - 9 * s, y - 2 * s), (x - 3 * s, y - 8 * s), max(1, round(2 * s)))
    _paint_temples(canvas, dark, b, 17 * s)


def _paint_heart_shades(canvas, color, b):
    s = b.s
    for x, y in _eye_centers(b):
        draw_heart(canvas, b.outline, (x, y), 36 * s)
        draw_heart(canvas, color, (x, y), 31 * s)
        pygame.draw.circle(canvas, WHITE, (x - 6 * s, y - 5 * s), 2.5 * s)
    _paint_temples(canvas, b.outline, b, 16 * s)


# Neck

def _collar_curve(canvas, color, b, width, spread=0.2):
    center, radii = (b.bx, b.by + b.h * 0.02), (b.w * 0.27, b.h * 0.2)
    start, end = math.pi * spread, math.pi * (1 - spread)
    draw_curve(canvas, b.outline, center, radii, start, end, width + 3 * b.s)
    draw_curve(canvas, color, center, radii, start, end, width)


def _paint_bell_collar(canvas, color, b):
    s = b.s
    _collar_curve(canvas, color, b, 7 * s)
    bell = (b.bx, b.by + b.h * 0.22 + 6 * s)
    pygame.draw.circle(canvas, GOLD_DARK, bell, 9 * s)
    pygame.draw.circle(canvas, GOLD, bell, 7.5 * s)
    pygame.draw.line(canvas, GOLD_DARK, (bell[0], bell[1] + 1 * s), (bell[0], bell[1] + 7 * s), 2)


def _paint_bandana(canvas, color, b):
    s = b.s
    top = b.by + b.h * 0.17
    _outlined_polygon(canvas, color, b.outline,
                      [(b.bx - b.w * 0.18, top), (b.bx + b.w * 0.18, top), (b.bx, b.by + b.h * 0.40)])
    for dx, dy in ((-0.07, 0.24), (0.07, 0.24), (0, 0.32)):
        pygame.draw.circle(canvas, WHITE, (b.bx + b.w * dx, b.by + b.h * dy), 2.5 * s)
    _collar_curve(canvas, color, b, 7 * s)


def _paint_bow_tie(canvas, color, b):
    s = b.s
    x, y = b.bx, b.by + b.h * 0.22
    for side in (-1, 1):
        _outlined_polygon(canvas, color, b.outline,
                          [(x, y), (x + side * 22 * s, y - 12 * s), (x + side * 22 * s, y + 12 * s)])
    knot = pygame.Rect(0, 0, 10 * s, 12 * s)
    knot.center = (x, y)
    pygame.draw.rect(canvas, mix(color, (0, 0, 0), 0.15), knot, border_radius=round(3 * s))
    pygame.draw.rect(canvas, b.outline, knot, width=2, border_radius=round(3 * s))


def _paint_scarf(canvas, color, b):
    s = b.s
    tail = pygame.Rect(b.bx + b.w * 0.08, b.by + b.h * 0.16, 17 * s, 42 * s)
    pygame.draw.rect(canvas, color, tail, border_radius=round(4 * s))
    pygame.draw.rect(canvas, b.outline, tail, width=2, border_radius=round(4 * s))
    for i in range(3):  # fringe
        x = tail.x + (i + 1) * tail.width / 4
        pygame.draw.line(canvas, b.outline, (x, tail.bottom), (x, tail.bottom + 5 * s), 2)
    pygame.draw.line(canvas, mix(color, WHITE, 0.4), (tail.x + 3 * s, tail.y + 14 * s),
                     (tail.right - 3 * s, tail.y + 14 * s), max(2, round(4 * s)))
    _collar_curve(canvas, color, b, 15 * s, spread=0.12)


# Body (clothes are clipped to the body's shape)

def _paint_clothes(canvas, color, b, neckline, decorate):
    """Fill the body below a curved neckline with `color`, add details, and trim to the body."""
    size = canvas.get_size()
    layer = pygame.Surface(size, pygame.SRCALPHA)
    top = b.by + b.h * neckline
    dip = b.h * 0.07
    curve = [(b.bx + dx, top + dip * (1 - min(1.0, (dx / (b.w * 0.5)) ** 2)))
             for dx in (b.w * (i / 10 - 1) for i in range(21))]
    pygame.draw.polygon(layer, color, curve + [(b.bx + b.w, b.by + b.h), (b.bx - b.w, b.by + b.h)])
    decorate(layer, color, b, top + dip)
    pygame.draw.lines(layer, b.outline, False, curve, max(2, round(3 * b.s)))

    # Keep only the part inside the body ellipse.
    mask = pygame.Surface(size, pygame.SRCALPHA)
    body = pygame.Rect(0, 0, b.w, b.h)
    body.center = (b.bx, b.by)
    pygame.draw.ellipse(mask, (255, 255, 255, 255), body)
    layer.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    canvas.blit(layer, (0, 0))


def _sweater_details(layer, color, b, neck_y):
    light = mix(color, WHITE, 0.45)
    for offset in (0.3, 0.4):
        stripe = pygame.Rect(b.bx - b.w, b.by + b.h * offset, b.w * 2, b.h * 0.04)
        pygame.draw.rect(layer, light, stripe)


def _tshirt_details(layer, color, b, neck_y):
    draw_heart(layer, WHITE, (b.bx, b.by + b.h * 0.33), 20 * b.s)


def _raincoat_details(layer, color, b, neck_y):
    s = b.s
    dark = mix(color, (0, 0, 0), 0.25)
    pygame.draw.line(layer, dark, (b.bx, neck_y), (b.bx, b.by + b.h), max(2, round(3 * s)))
    for i in range(3):
        pygame.draw.circle(layer, dark, (b.bx + 7 * s, neck_y + (8 + i * 11) * s), 3 * s)


def _paint_sweater(canvas, color, b):
    _paint_clothes(canvas, color, b, 0.14, _sweater_details)


def _paint_tshirt(canvas, color, b):
    _paint_clothes(canvas, color, b, 0.17, _tshirt_details)


def _paint_raincoat(canvas, color, b):
    _paint_clothes(canvas, color, b, 0.11, _raincoat_details)


ITEM_PAINTERS = {
    "bow": _paint_bow,
    "flower": _paint_flower,
    "party_hat": _paint_party_hat,
    "beanie": _paint_beanie,
    "crown": _paint_crown,
    "glasses": _paint_glasses,
    "sunglasses": _paint_sunglasses,
    "heart_shades": _paint_heart_shades,
    "bell_collar": _paint_bell_collar,
    "bandana": _paint_bandana,
    "bow_tie": _paint_bow_tie,
    "scarf": _paint_scarf,
    "sweater": _paint_sweater,
    "tshirt": _paint_tshirt,
    "raincoat": _paint_raincoat,
}
