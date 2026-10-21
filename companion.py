"""Companion mode: a small, borderless, always-on-top pet that lives on your desktop.

- Drag the pet to move it.
- Click the pet to give it a pat.
- Hover over the pet to see its stats.
- Right-click the pet for a menu (Feed, Play, Sound, Big window, Hide, Quit).
- Keyboard shortcuts F, P, M and C work while the pet's window is focused.
"""

import pygame

import desktop_window
import ui
from screens import PetScreen

SIZE = (240, 280)
DRAG_THRESHOLD = 4  # pixels the mouse must move before a click becomes a drag

MENU_ITEM_HEIGHT = 28
MENU_WIDTH = 150
MENU_PADDING = 6


class CompanionScreen(PetScreen):
    PET_GROUND = (SIZE[0] // 2, 228)
    ZOOM = 0.6
    FLASH = False  # a full-window flash would show as a coloured box on the desktop

    def __init__(self, app, pet, greeting=None, seconds_away=None):
        super().__init__(app, pet, greeting, seconds_away)
        self.hovered = False
        self.hand_cursor = False
        self.press = None       # (mouse position, window position) when the button went down
        self.dragging = False
        self.menu = None        # Menu while open
        self.stats_rect = pygame.Rect(20, 240, SIZE[0] - 40, 32)

    # ---- Input ----

    def handle_event(self, event):
        if self.menu:
            self.handle_menu_event(event)
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.over_pet(event.pos):
                self.press = (desktop_mouse(), self.app.window.position)
                self.dragging = False
            elif event.button == 3:
                self.menu = Menu(self.menu_items(), event.pos, SIZE, self.app.fonts.small)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.press:
            if not self.dragging and self.over_pet(event.pos):
                self.react(self.pet.cuddle(), at=event.pos)
            self.end_drag()
        elif event.type == pygame.KEYDOWN:
            self.handle_shortcut(event.key)

    def handle_menu_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.menu.hover(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            choice = self.menu.item_at(event.pos) if event.button == 1 else None
            self.menu = None
            if choice:
                self.choose(choice)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.menu = None

    def menu_items(self):
        return [
            ("feed", "Feed  (F)"),
            ("play", "Play  (P)"),
            ("sound", "Sound: off  (M)" if self.app.sounds.muted else "Sound: on  (M)"),
            ("big", "Big window  (C)"),
            ("hide", "Hide"),
            ("quit", "Quit"),
        ]

    def choose(self, choice):
        if choice == "feed":
            self.react(self.pet.feed())
        elif choice == "play":
            self.react(self.pet.play())
        elif choice == "sound":
            self.toggle_sound()
        elif choice == "big":
            self.app.toggle_companion()
        elif choice == "hide":
            self.app.window.minimize()  # click its taskbar button to bring it back
        elif choice == "quit":
            self.app.quit()

    def end_drag(self):
        if self.dragging:
            self.app.companion_pos = self.app.window.position
            self.app.save()
        self.press = None
        self.dragging = False

    # ---- Update ----

    def update(self, dt):
        super().update(dt)
        mouse = desktop_mouse()
        window_x, window_y = self.app.window.position

        # Dragging: move the window by however far the mouse moved since the press.
        if self.press:
            if not pygame.mouse.get_pressed()[0]:
                self.end_drag()  # the button was released outside the window
            else:
                (start_x, start_y), (win_x, win_y) = self.press
                dx, dy = mouse[0] - start_x, mouse[1] - start_y
                if abs(dx) > DRAG_THRESHOLD or abs(dy) > DRAG_THRESHOLD:
                    self.dragging = True
                if self.dragging:
                    self.app.window.position = (win_x + dx, win_y + dy)

        # Work out hover from the desktop mouse position, because the window
        # gets no mouse events at all while the cursor is over see-through parts.
        local = (mouse[0] - window_x, mouse[1] - window_y)
        self.hovered = self.over_pet(local) or (self.hovered and self.stats_rect.collidepoint(local))
        want_hand = self.hovered and not self.menu
        if want_hand != self.hand_cursor:
            self.hand_cursor = want_hand
            ui.set_hand_cursor(want_hand)

    # ---- Draw ----

    def draw(self, surface):
        see_through = self.app.see_through
        if see_through:
            surface.fill(desktop_window.KEY_COLOR)
        else:
            surface.blit(self.app.background, (0, 0))

        self.draw_pet(surface, shadow=not see_through)
        self.effects.draw(surface)
        if self.message:
            # No fade-out here: half-transparent pixels would mix with the key colour.
            ui.draw_speech_bubble(surface, self.app.fonts.small, self.message, (SIZE[0] // 2, 96),
                                  max_width=SIZE[0] - 30)
        if (self.hovered or self.dragging) and not self.menu:
            self.draw_stats(surface)
        if self.menu:
            self.menu.draw(surface)
        self.effects.draw_overlay(surface)

    def draw_stats(self, surface):
        """A small panel with the level and three mini bars (hunger, happiness, energy)."""
        rect = self.stats_rect
        ui.draw_panel(surface, rect, radius=rect.height // 2)
        level = self.app.fonts.badge.render(f"Lv {self.pet.level}", True, ui.XP_COLOR)
        surface.blit(level, level.get_rect(midleft=(rect.x + 14, rect.centery)))
        stats = [(self.pet.hunger, ui.HUNGER_COLOR), (self.pet.happiness, ui.HAPPY_COLOR),
                 (self.pet.energy, ui.ENERGY_COLOR)]
        bar_w, gap = 38, 8
        x = rect.right - 14 - 3 * bar_w - 2 * gap
        for value, color in stats:
            bar = pygame.Rect(x, rect.centery - 4, bar_w, 8)
            pygame.draw.rect(surface, ui.BAR_BG, bar, border_radius=4)
            fill = round(bar_w * value / 100)
            if fill > 0:
                pygame.draw.rect(surface, color, (bar.x, bar.y, max(fill, 8), bar.h), border_radius=4)
            x += bar_w + gap


class Menu:
    """A small right-click menu that stays inside the window."""

    def __init__(self, items, pos, window_size, font):
        self.items = items
        self.font = font
        height = len(items) * MENU_ITEM_HEIGHT + 2 * MENU_PADDING
        self.rect = pygame.Rect(pos[0], pos[1], MENU_WIDTH, height)
        self.rect.clamp_ip(pygame.Rect((0, 0), window_size))
        self.hovered = None

    def item_rect(self, index):
        return pygame.Rect(self.rect.x + MENU_PADDING, self.rect.y + MENU_PADDING + index * MENU_ITEM_HEIGHT,
                           self.rect.width - 2 * MENU_PADDING, MENU_ITEM_HEIGHT)

    def item_at(self, pos):
        for index, (key, _) in enumerate(self.items):
            if self.item_rect(index).collidepoint(pos):
                return key
        return None

    def hover(self, pos):
        self.hovered = self.item_at(pos)

    def draw(self, surface):
        ui.draw_panel(surface, self.rect, radius=12)
        for index, (key, label) in enumerate(self.items):
            row = self.item_rect(index)
            if key == self.hovered:
                pygame.draw.rect(surface, ui.BAR_BG, row, border_radius=8)
            color = ui.COLLAR if key == "quit" else ui.TEXT
            text = self.font.render(label, True, color)
            surface.blit(text, text.get_rect(midleft=(row.x + 10, row.centery)))


def desktop_mouse():
    """Mouse position on the whole desktop (not just inside our window)."""
    return pygame.mouse.get_pos(desktop=True)
