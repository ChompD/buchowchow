"""The Wardrobe screen: dress up your pet.

- Tabs along the middle pick a slot (Head, Face, Neck, Outfit).
- Each card shows your pet wearing that item. Click one to put it on,
  or "None" to take the slot's item off. Locked items show the level they unlock at.
- The swatches at the bottom recolour the item in the current slot.
- Done (or Esc / Enter / W) goes back to the game.
"""

import pygame

import ui
import wardrobe
from screens import WIDTH

PREVIEW_GROUND = (WIDTH // 2, 306)
TABS_Y = 324
TAB_HEIGHT = 34
GRID_Y = 368
CARD_SIZE = (130, 94)
CARD_GAP = 10
LABEL_HEIGHT = 22
COLORS_Y = 602
SWATCH_RADIUS = 13
SWATCH_GAP = 38
MESSAGE_SECONDS = 2.5

# Where each slot sits on the pet (fraction of body height from its centre),
# and how far to zoom in, so each card shows the interesting part.
SLOT_VIEW = {
    "head": (-0.38, 0.72),
    "face": (-0.08, 1.05),
    "neck": (0.18, 0.95),
    "body": (0.26, 0.75),
}


class WardrobeScreen:
    def __init__(self, app, pet):
        self.app = app
        self.pet = pet
        self.time = 0.0
        self.slot = "head"
        self.message = None
        self.message_timer = 0.0
        self.action = None       # a little wobble whenever something changes
        self.action_time = 0.0
        self.changed = False
        self.hovered = None
        self.card_cache = {}     # card images, rebuilt only when the outfit or tab changes

        fonts = app.fonts
        self.done_button = ui.Button((WIDTH - 24 - 96, 18, 96, 38), "Done", ui.PLAY_COLOR, fonts.badge)
        tab_w = (WIDTH - 48 - 3 * 8) // 4
        self.tabs = {slot: pygame.Rect(24 + i * (tab_w + 8), TABS_Y, tab_w, TAB_HEIGHT)
                     for i, slot in enumerate(wardrobe.SLOTS)}
        swatches_w = (len(wardrobe.COLORS) - 1) * SWATCH_GAP
        first_x = WIDTH - 24 - SWATCH_RADIUS - swatches_w
        self.swatches = {color: (first_x + i * SWATCH_GAP, COLORS_Y) for i, color in enumerate(wardrobe.COLORS)}

    # ---- Layout ----

    def cards(self):
        """(item key or None, rect) for every card in the current slot. None means "take it off"."""
        keys = [None] + [item.key for item in wardrobe.items_for(self.slot)]
        rects = []
        for i, key in enumerate(keys):
            col, row = i % 3, i // 3
            rect = pygame.Rect(24 + col * (CARD_SIZE[0] + CARD_GAP), GRID_Y + row * (CARD_SIZE[1] + CARD_GAP),
                               *CARD_SIZE)
            rects.append((key, rect))
        return rects

    def swatch_at(self, pos):
        for color, center in self.swatches.items():
            if (pos[0] - center[0]) ** 2 + (pos[1] - center[1]) ** 2 <= (SWATCH_RADIUS + 3) ** 2:
                return color
        return None

    def thing_at(self, pos):
        """What the mouse is over: ("tab", slot), ("card", key), ("swatch", color) or None."""
        for slot, rect in self.tabs.items():
            if rect.collidepoint(pos):
                return ("tab", slot)
        for key, rect in self.cards():
            if rect.collidepoint(pos):
                return ("card", key)
        color = self.swatch_at(pos)
        if color and self.can_recolor():
            return ("swatch", color)
        return None

    def can_recolor(self):
        item = self.pet.outfit.item(self.slot)
        return item is not None and item.colorable

    # ---- Input ----

    def handle_event(self, event):
        if self.done_button.handle_event(event):
            self.app.close_wardrobe(self.changed)
            return
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.thing_at(event.pos)
            ui.set_hand_cursor(self.hovered is not None or self.done_button.hovered)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            target = self.thing_at(event.pos)
            if target:
                self.click(*target)
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_w):
                self.app.close_wardrobe(self.changed)
            elif event.key == pygame.K_TAB:
                index = wardrobe.SLOTS.index(self.slot)
                self.slot = wardrobe.SLOTS[(index + 1) % len(wardrobe.SLOTS)]

    def click(self, kind, value):
        outfit, sounds = self.pet.outfit, self.app.sounds
        if kind == "tab":
            if value != self.slot:
                self.slot = value
                sounds.play("click")
            return
        if kind == "card":
            if value is None:
                if outfit.item(self.slot) is None:
                    return
                outfit.take_off(self.slot)
            else:
                item = wardrobe.ITEMS[value]
                if self.pet.level < item.unlock_level:
                    sounds.play("refuse")
                    self.say(f"{item.name} unlocks at level {item.unlock_level}.")
                    return
                if outfit.is_wearing(value):
                    return
                outfit.wear(value, self.pet.level)
                self.say(self.pet.say("outfit"))
        elif kind == "swatch":
            if outfit.color(self.slot) == value:
                return
            outfit.set_color(self.slot, value)
        self.changed = True
        self.card_cache.clear()
        self.action, self.action_time = "petted", 0.0
        sounds.play("petted")

    def say(self, text):
        self.message = text
        self.message_timer = MESSAGE_SECONDS

    # ---- Update ----

    def update(self, dt):
        self.time += dt
        self.pet.update(dt)  # time keeps passing while you dress up
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = None
        if self.action:
            self.action_time += dt
            if self.action_time >= ui.ACTION_DURATIONS[self.action]:
                self.action = None

    # ---- Draw ----

    def draw(self, surface):
        fonts = self.app.fonts
        surface.blit(self.app.background, (0, 0))

        title = fonts.title.render("Wardrobe", True, ui.TEXT)
        surface.blit(title, (24, 16))
        self.done_button.draw(surface)

        progress = self.action_time / ui.ACTION_DURATIONS[self.action] if self.action else 0.0
        self.app.pet_renderer.draw(surface, "happy", PREVIEW_GROUND, self.time, stage=self.pet.stage,
                                   action=self.action, progress=min(1.0, progress),
                                   species=self.pet.species, outfit=self.pet.outfit)
        if self.message:
            ui.draw_speech_bubble(surface, fonts.body, self.message, (WIDTH // 2, 96))

        self.draw_tabs(surface)
        self.draw_cards(surface)
        self.draw_colors(surface)

    def draw_tabs(self, surface):
        font = self.app.fonts.badge
        for slot, rect in self.tabs.items():
            selected = slot == self.slot
            if selected:
                pygame.draw.rect(surface, ui.XP_COLOR, rect, border_radius=rect.height // 2)
            else:
                ui.draw_panel(surface, rect, radius=rect.height // 2)
                if self.hovered == ("tab", slot):
                    pygame.draw.rect(surface, ui.PANEL_SHADOW, rect, width=2, border_radius=rect.height // 2)
            label = font.render(wardrobe.SLOT_NAMES[slot], True, ui.WHITE if selected else ui.TEXT)
            surface.blit(label, label.get_rect(center=rect.center))

    def draw_cards(self, surface):
        font = self.app.fonts.small
        worn = self.pet.outfit.item(self.slot)
        for key, rect in self.cards():
            item = wardrobe.ITEMS.get(key)
            locked = item is not None and self.pet.level < item.unlock_level
            ui.draw_panel(surface, rect, radius=14)
            surface.blit(self.card_image(key, rect.size), rect.topleft)

            if locked:
                veil = pygame.Surface(rect.size, pygame.SRCALPHA)
                pygame.draw.rect(veil, (255, 255, 255, 170), veil.get_rect(), border_radius=14)
                surface.blit(veil, rect.topleft)
                draw_lock(surface, (rect.centerx, rect.centery - 8))

            is_worn = (item is None and worn is None) or (item is not None and worn is not None
                                                          and worn.key == key)
            name = "None" if item is None else item.name
            if locked:
                name = f"Lv {item.unlock_level}"
            strip = pygame.Rect(rect.x, rect.bottom - LABEL_HEIGHT, rect.width, LABEL_HEIGHT)
            pygame.draw.rect(surface, ui.WHITE, strip, border_bottom_left_radius=14, border_bottom_right_radius=14)
            label = font.render(name, True, ui.XP_COLOR if is_worn else ui.TEXT_SOFT if locked else ui.TEXT)
            surface.blit(label, label.get_rect(center=strip.center))

            if is_worn:
                pygame.draw.rect(surface, ui.XP_COLOR, rect, width=3, border_radius=14)
            elif self.hovered == ("card", key) and not locked:
                pygame.draw.rect(surface, ui.PANEL_SHADOW, rect, width=2, border_radius=14)

    def card_image(self, key, size):
        """The pet wearing `key` (or nothing in this slot), zoomed in on the slot."""
        cache_key = (self.slot, key)
        if cache_key in self.card_cache:
            return self.card_cache[cache_key]

        preview = wardrobe.Outfit.from_dict(self.pet.outfit.to_dict(), self.pet.level)
        if key is None:
            preview.take_off(self.slot)
        else:
            preview.wear(key, 99, self.pet.outfit.color(self.slot))  # show even locked items

        image = pygame.Surface(size, pygame.SRCALPHA)
        anchor, zoom = SLOT_VIEW[self.slot]
        s = ui.stage_look(self.pet.stage)["scale"] * zoom
        body_h = ui.PetRenderer.BODY_H * s
        centre_y = (size[1] - LABEL_HEIGHT) / 2 - anchor * body_h  # leave room for the label
        self.app.pet_renderer.draw(image, "content", (size[0] / 2, centre_y + body_h / 2), 1.0,
                                   stage=self.pet.stage, zoom=zoom, shadow=False,
                                   species=self.pet.species, outfit=preview)
        # Round the corners to match the card.
        mask = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=14)
        image.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        self.card_cache[cache_key] = image
        return image

    def draw_colors(self, surface):
        font = self.app.fonts.body
        item = self.pet.outfit.item(self.slot)
        label = font.render("Colour", True, ui.TEXT)
        surface.blit(label, label.get_rect(midleft=(24, COLORS_Y)))
        if item is None or not item.colorable:
            note = "Pick an item to colour it" if item is None else "This one comes in one colour"
            text = self.app.fonts.small.render(note, True, ui.TEXT_SOFT)
            surface.blit(text, text.get_rect(midright=(WIDTH - 24, COLORS_Y)))
            return
        current = self.pet.outfit.color(self.slot)
        for color, center in self.swatches.items():
            if color == current:
                pygame.draw.circle(surface, ui.TEXT, center, SWATCH_RADIUS + 4, 2)
            elif self.hovered == ("swatch", color):
                pygame.draw.circle(surface, ui.PANEL_SHADOW, center, SWATCH_RADIUS + 4, 2)
            pygame.draw.circle(surface, ui.OUTFIT_RGB[color], center, SWATCH_RADIUS)


def draw_lock(surface, center):
    x, y = center
    pygame.draw.circle(surface, ui.TEXT_SOFT, (x, y - 6), 8, 3)
    body = pygame.Rect(0, 0, 22, 17)
    body.midtop = (x, y - 3)
    pygame.draw.rect(surface, ui.TEXT_SOFT, body, border_radius=4)
    pygame.draw.circle(surface, ui.WHITE, (x, y + 4), 2.5)
