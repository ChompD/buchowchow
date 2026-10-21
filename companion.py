"""Companion mode: a small, borderless, always-on-top pet that lives on your desktop.

- The pet keeps itself busy (see wander.py): it walks and runs along the top of the
  taskbar, sits, lies down, looks around, tilts its head, and sometimes barks
  (or meows, or thumps) when your cursor comes close.
- "Stay here" (menu or S) keeps it in one spot: it still does everything except walk
  and run. "Walk around" lets it roam again.
- Ghost mode (menu or G) fades the pet and lets every click pass through it.
  Hold Ctrl and point at the pet to make it solid and clickable again.
- Drag the pet to move it. While walking is on it drops back down to the taskbar;
  in Stay mode it stays where you put it, snapping to the taskbar or a screen side if close.
- Click the pet to give it a pat. Hover over it to see its stats.
- Right-click the pet for a menu (Feed, Play, Sound, Stay/Walk, Ghost mode, Wardrobe,
  Big window, Hide, Quit).
- Keyboard shortcuts F, P, M, S, G, C and W work while the pet's window is focused.
"""

import pygame

import desktop_window
import ui
from screens import PetScreen
from wander import Wanderer

SIZE = (240, 280)
DRAG_THRESHOLD = 4   # pixels the mouse must move before a click becomes a drag
GRAVITY = 1800       # how fast a dropped pet falls, in pixels per second per second
AREA_REFRESH = 5.0   # re-check where the taskbar is every few seconds
NOTICE_DISTANCE = 200  # the pet notices the cursor when it comes this close (pixels)
CURSOR_SOUNDS = {"dog": "bark", "cat": "meow", "bunny": "thump"}

MENU_ITEM_HEIGHT = 28
MENU_MIN_WIDTH = 150
MENU_PADDING = 6
MENU_CLOSE_DELAY = 0.6  # the menu closes once the cursor has been away from it this long (seconds)
MENU_NEAR = 12          # how close (pixels) counts as still "at" the menu


class CompanionScreen(PetScreen):
    PET_GROUND = (SIZE[0] // 2, 228)
    FEET_Y = PET_GROUND[1] + 4   # the bottom of the paws, inside the window
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

        self.wanderer = Wanderer()
        self.facing = -1        # -1 = left, 1 = right
        self.pos = None         # exact window position (floats), set on the first update
        self.fall_speed = 0.0
        self.area = None
        self.area_timer = 0.0
        self.cursor_near = False
        self.ghost_state = None  # (click_through, alpha) last applied to the window

    # ---- Input ----

    def handle_event(self, event):
        if event.type == pygame.WINDOWFOCUSLOST:
            self.menu = None  # you clicked on another app: close the menu
            return
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
            if event.key == pygame.K_s:
                self.toggle_walking()
            elif event.key == pygame.K_g:
                self.toggle_ghost()
            else:
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
            ("walk", "Stay here  (S)" if self.app.walking else "Walk around  (S)"),
            ("ghost", "Leave ghost mode  (G)" if self.app.ghost else "Ghost mode  (G)"),
            ("wardrobe", "Wardrobe  (W)"),
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
        elif choice == "walk":
            self.toggle_walking()
        elif choice == "ghost":
            self.toggle_ghost()
        elif choice == "wardrobe":
            self.app.open_wardrobe()
        elif choice == "big":
            self.app.toggle_companion()
        elif choice == "hide":
            self.app.window.minimize()  # click its taskbar button to bring it back
        elif choice == "quit":
            self.app.quit()

    def toggle_walking(self):
        self.app.walking = not self.app.walking
        self.say(self.pet.say("walk_on" if self.app.walking else "stay"))
        self.fall_speed = 0.0
        if not self.app.walking and self.wanderer.walking:
            self.wanderer.timer = 0  # stop and pick something calm to do
        self.app.sounds.play("click")
        self.app.save()

    def toggle_ghost(self):
        if not self.app.see_through:
            self.say("Ghost mode only works on Windows.")
            return
        self.app.ghost = not self.app.ghost
        self.say(self.pet.say("ghost_on" if self.app.ghost else "ghost_off"))
        self.app.sounds.play("click")
        self.app.save()

    def apply_ghost(self, over_pet):
        """Make the window click-through and faded (or solid again) when that changes."""
        ghost = self.app.ghost and self.menu is None  # pause ghost mode while the menu is open
        ctrl = ghost and desktop_window.ctrl_held()  # only ask Windows when it matters
        state = desktop_window.ghost_style(ghost, ctrl, over_pet)
        if state != self.ghost_state and self.app.see_through:
            click_through, alpha = state
            handle = self.app.window.handle
            desktop_window.set_click_through(handle, click_through)
            desktop_window.set_see_through(handle, desktop_window.KEY_COLOR, alpha)
            self.ghost_state = state
        return state[0]

    def end_drag(self):
        if self.dragging:
            window = self.app.window
            if not self.app.walking:
                # Staying put: tidy it up against the taskbar or a screen side if it's close.
                window.position = desktop_window.snap_position(
                    window.position, SIZE[0], self.pet_half_width(), self.FEET_Y, self.work_area())
            self.pos = [float(v) for v in window.position]  # if walking, it falls from here
            self.fall_speed = 0.0
            self.app.companion_pos = window.position
            self.app.save()
        self.press = None
        self.dragging = False

    # ---- Layout helpers ----

    def pet_half_width(self):
        """About half the pet's width, including ears and tail."""
        return ui.PetRenderer.BODY_W * self.scale * 0.56

    def work_area(self):
        if self.area is None:
            self.area = desktop_window.work_area(self.app.desktop_size())
        return self.area

    def can_act(self):
        """Do its own thing only when nobody is interacting with the pet."""
        return not (self.hovered or self.menu or self.press or self.action)

    def shown_activity(self):
        """What to draw: the current activity, unless it has been paused mid-walk."""
        if self.fall_speed or (self.wanderer.walking and not (self.can_act() and self.app.walking)):
            return None
        return self.wanderer.activity

    # ---- Update ----

    def update(self, dt):
        super().update(dt)
        window = self.app.window
        if self.pos is None:
            self.pos = [float(v) for v in window.position]
        self.area_timer -= dt
        if self.area_timer <= 0:  # the taskbar can move or auto-hide
            self.area, self.area_timer = None, AREA_REFRESH

        mouse = desktop_mouse()
        if self.press:
            self.drag(mouse)
        else:
            self.live(dt)

        # Work out hover from the desktop mouse position, because the window
        # gets no mouse events at all while the cursor is over see-through parts.
        window_x, window_y = window.position
        local = (mouse[0] - window_x, mouse[1] - window_y)
        over_pet = self.over_pet(local)
        if self.menu and not self.menu.keep_open(local, over_pet, dt):
            self.menu = None  # the cursor wandered off
        ghosted = self.apply_ghost(over_pet)
        # A ghost can't be touched, so pointing at it doesn't count as hovering.
        self.hovered = not ghosted and (over_pet or (self.hovered and self.stats_rect.collidepoint(local)))
        want_hand = self.hovered and not self.menu
        if want_hand != self.hand_cursor:
            self.hand_cursor = want_hand
            ui.set_hand_cursor(want_hand)
        self.watch_cursor(local)

    def watch_cursor(self, local):
        """Notice the cursor coming close: face it, and sometimes bark at it."""
        center_x, center_y = self.pet_center()
        dx, dy = local[0] - center_x, local[1] - center_y
        near = (abs(dx) < NOTICE_DISTANCE and abs(dy) < NOTICE_DISTANCE
                and not self.hovered and self.can_act() and not self.fall_speed)
        quiet = self.app.ghost  # a ghost stays out of your way: it watches, but doesn't bark
        if near and not self.cursor_near and not quiet and self.wanderer.notice_cursor(dx):
            self.facing = 1 if dx > 0 else -1
            self.say(self.pet.say("cursor"))
            self.app.sounds.play(CURSOR_SOUNDS.get(self.pet.species, "bark"))
        if near and not self.wanderer.walking:
            self.facing = 1 if dx > 0 else -1  # keep watching it
        self.cursor_near = near

    def drag(self, mouse):
        """Move the window by however far the mouse moved since the press."""
        if not pygame.mouse.get_pressed()[0]:
            self.end_drag()  # the button was released outside the window
            return
        (start_x, start_y), (win_x, win_y) = self.press
        dx, dy = mouse[0] - start_x, mouse[1] - start_y
        if abs(dx) > DRAG_THRESHOLD or abs(dy) > DRAG_THRESHOLD:
            self.dragging = True
        if self.dragging:
            self.app.window.position = (win_x + dx, win_y + dy)
            self.pos = [float(win_x + dx), float(win_y + dy)]

    def live(self, dt):
        """Do its own thing: fall down to the taskbar if needed (when walking is on),
        then walk, run, sit, lie down, look around or tilt its head."""
        x, y = self.pos
        if self.app.walking:
            area = self.work_area()
            floor = desktop_window.ground_y(area, self.FEET_Y)
            low, high = desktop_window.walk_bounds(area, SIZE[0], self.pet_half_width())
            if y < floor - 0.5:  # in the air: fall
                self.fall_speed += GRAVITY * dt
                y = min(floor, y + self.fall_speed * dt)
                if y >= floor:
                    self.fall_speed = 0.0
                    self.start_action("land")
                    self.app.sounds.play("click")
            else:
                y = floor  # also pops it back up if it was dragged into the taskbar
                if self.can_act():
                    x = self.wanderer.update(dt, x, low, high, self.pet.mood)
        elif self.can_act():
            self.wanderer.update(dt, x, x, x, self.pet.mood, can_move=False)  # Stay: never moves

        if self.wanderer.walking:
            self.facing = self.wanderer.direction
        self.pos = [x, y]
        target = (round(x), round(y))
        if self.app.window.position != target:
            self.app.window.position = target

    # ---- Draw ----

    def draw(self, surface):
        see_through = self.app.see_through
        if see_through:
            surface.fill(desktop_window.KEY_COLOR)
        else:
            surface.blit(self.app.background, (0, 0))

        gaze = -1 if self.cursor_near and not self.wanderer.walking else None  # look at the cursor
        self.draw_pet(surface, shadow=not see_through, activity=self.shown_activity(),
                      activity_progress=self.wanderer.progress, facing=self.facing, gaze=gaze)
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
    """A small right-click menu that stays inside the window.

    It closes itself once the cursor has wandered away from it (see keep_open),
    because clicks outside the pet go to other apps, not to us.
    """

    def __init__(self, items, pos, window_size, font):
        self.items = items
        self.font = font
        height = len(items) * MENU_ITEM_HEIGHT + 2 * MENU_PADDING
        widest = max(font.size(label)[0] for _, label in items) if font else 0
        width = min(window_size[0], max(MENU_MIN_WIDTH, widest + 2 * MENU_PADDING + 20))
        self.rect = pygame.Rect(pos[0], pos[1], width, height)
        self.rect.clamp_ip(pygame.Rect((0, 0), window_size))
        self.hovered = None
        self.away_time = 0.0

    def keep_open(self, pos, near_pet, dt):
        """Call every frame. Returns False once the cursor has been away from the menu
        (and the pet) for MENU_CLOSE_DELAY seconds; a short wobble outside is fine."""
        if near_pet or self.rect.inflate(2 * MENU_NEAR, 2 * MENU_NEAR).collidepoint(pos):
            self.away_time = 0.0
        else:
            self.away_time += dt
        return self.away_time < MENU_CLOSE_DELAY

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
