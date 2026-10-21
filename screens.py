"""The game's screens: naming a new pet, and the full-size pet screen.

`PetScreen` holds everything the full window and the companion window have in
common: talking, reacting, animations, effects and autosaving. Each subclass
only decides where things go and how the player interacts.
"""

import random

import pygame

import effects
import ui
from messages import SPECIES, SPECIES_NAMES, format_duration
from pet import DEFAULT_NAME, DEFAULT_SPECIES, MAX_NAME_LENGTH

WIDTH, HEIGHT = 460, 640
MESSAGE_SECONDS = 3.0
CHATTER_SECONDS = (12, 25)   # the pet says something on its own every 12-25 s
AUTOSAVE_SECONDS = 30
AWAY_NOTE_SECONDS = 6.0

# Which animation plays after a successful action.
ANIMATIONS = {"fed": "eating", "played": "playing", "petted": "petted"}


CARD_SIZE = (128, 200)
CARD_GAP = 12
CARD_TOP = 108


class NameScreen:
    """First screen: the player picks a kind of pet and types its name."""

    def __init__(self, app, notice=None):
        self.app = app
        self.notice = notice  # e.g. a warning that the old save couldn't be read
        self.text = ""
        self.time = 0.0
        self.species = DEFAULT_SPECIES
        total = len(SPECIES) * CARD_SIZE[0] + (len(SPECIES) - 1) * CARD_GAP
        left = (WIDTH - total) // 2
        self.cards = {kind: pygame.Rect(left + i * (CARD_SIZE[0] + CARD_GAP), CARD_TOP, *CARD_SIZE)
                      for i, kind in enumerate(SPECIES)}
        self.hovered_card = None
        self.input_rect = pygame.Rect(60, 396, WIDTH - 120, 50)
        self.start_button = ui.Button((WIDTH // 2 - 100, 474, 200, 54), "Start", ui.PLAY_COLOR, app.fonts.button)
        pygame.key.start_text_input()

    def card_at(self, pos):
        for kind, rect in self.cards.items():
            if rect.collidepoint(pos):
                return kind
        return None

    def choose(self, kind):
        if kind != self.species:
            self.species = kind
            self.app.sounds.play("click")

    def handle_event(self, event):
        if self.start_button.handle_event(event):
            self.confirm()
        elif event.type == pygame.MOUSEMOTION:
            self.hovered_card = self.card_at(event.pos)
            ui.set_hand_cursor(self.start_button.hovered or self.hovered_card is not None)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            kind = self.card_at(event.pos)
            if kind:
                self.choose(kind)
        elif event.type == pygame.TEXTINPUT:
            if event.text.isprintable():
                self.text = (self.text + event.text)[:MAX_NAME_LENGTH]
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.confirm()
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                step = 1 if event.key == pygame.K_RIGHT else -1
                index = (SPECIES.index(self.species) + step) % len(SPECIES)
                self.choose(SPECIES[index])

    def confirm(self):
        pygame.key.stop_text_input()
        ui.set_hand_cursor(False)
        self.app.sounds.play("click")
        self.app.start_game(self.text, self.species)

    def draw_cards(self, surface):
        fonts = self.app.fonts
        for kind, rect in self.cards.items():
            selected = kind == self.species
            card = rect.move(0, -4 if selected else 0)  # the chosen card lifts a little
            ui.draw_panel(surface, card, radius=16)
            if selected:
                pygame.draw.rect(surface, ui.XP_COLOR, card, width=3, border_radius=16)
            elif kind == self.hovered_card:
                pygame.draw.rect(surface, ui.PANEL_SHADOW, card, width=2, border_radius=16)
            mood = "happy" if selected else "content"
            self.app.pet_renderer.draw(surface, mood, (card.centerx, card.bottom - 46), self.time,
                                       zoom=0.66, species=kind)
            label = fonts.badge.render(SPECIES_NAMES[kind], True, ui.XP_COLOR if selected else ui.TEXT_SOFT)
            surface.blit(label, label.get_rect(midbottom=(card.centerx, card.bottom - 10)))

    def update(self, dt):
        self.time += dt

    def draw(self, surface):
        fonts = self.app.fonts
        surface.blit(self.app.background, (0, 0))

        title = fonts.title.render("Meet your new pet!", True, ui.TEXT)
        surface.blit(title, title.get_rect(midtop=(WIDTH // 2, 32)))
        if self.notice:
            for i, line in enumerate(ui.wrap_text(fonts.small, self.notice, WIDTH - 60)):
                img = fonts.small.render(line, True, ui.COLLAR)
                surface.blit(img, img.get_rect(midtop=(WIDTH // 2, 74 + i * fonts.small.get_linesize())))
        else:
            subtitle = fonts.small.render("Choose a pet and give them a name.", True, ui.TEXT_SOFT)
            surface.blit(subtitle, subtitle.get_rect(midtop=(WIDTH // 2, 76)))

        self.draw_cards(surface)

        label = fonts.body.render("Pet name", True, ui.TEXT)
        surface.blit(label, label.get_rect(midbottom=(WIDTH // 2, self.input_rect.top - 6)))

        ui.draw_panel(surface, self.input_rect, radius=14)
        pygame.draw.rect(surface, ui.XP_COLOR, self.input_rect, width=2, border_radius=14)
        text_x = self.input_rect.x + 16
        if self.text:
            text_img = fonts.body.render(self.text, True, ui.TEXT)
        else:
            text_img = fonts.body.render(DEFAULT_NAME, True, ui.TEXT_SOFT)  # placeholder
        surface.blit(text_img, text_img.get_rect(midleft=(text_x, self.input_rect.centery)))

        if (self.time % 1.0) < 0.5:  # blinking cursor
            cursor_x = text_x + (fonts.body.size(self.text)[0] if self.text else 0) + 1
            pygame.draw.line(surface, ui.TEXT, (cursor_x, self.input_rect.centery - 11),
                             (cursor_x, self.input_rect.centery + 11), 2)

        counter = fonts.small.render(f"{len(self.text)}/{MAX_NAME_LENGTH}", True, ui.TEXT_SOFT)
        surface.blit(counter, counter.get_rect(midright=(self.input_rect.right - 14, self.input_rect.centery)))

        self.start_button.draw(surface)
        hint = fonts.small.render("or press Enter", True, ui.TEXT_SOFT)
        surface.blit(hint, hint.get_rect(midtop=(WIDTH // 2, 540)))


class PetScreen:
    """Shared behaviour for any screen that shows the pet.

    Subclasses set PET_GROUND (where the pet's feet are) and ZOOM (pet size),
    and implement handle_event() and draw().
    """

    PET_GROUND = (0, 0)
    ZOOM = 1.0
    FLASH = True  # white flash on level up

    def __init__(self, app, pet, greeting=None, seconds_away=None):
        self.app = app
        self.pet = pet
        self.time = 0.0
        self.effects = effects.Effects()

        self.message = None
        self.message_timer = 0.0
        self.chatter_timer = random.uniform(*CHATTER_SECONDS)
        self.autosave_timer = AUTOSAVE_SECONDS
        self.last_mood = pet.mood

        # One-off animation currently playing (eating, playing, petted, refuse).
        self.action = None
        self.action_time = 0.0
        self.last_bite = -1

        # A returning pet greets you and says how long you were gone.
        self.away_note = None
        self.away_timer = 0.0
        if seconds_away is not None:
            self.say(pet.say("welcome_back"))
            if seconds_away >= 60:
                self.away_note = f"You were away for {format_duration(seconds_away)}"
                self.away_timer = AWAY_NOTE_SECONDS
        elif greeting:
            self.say(greeting)

    # ---- Layout helpers ----

    @property
    def scale(self):
        return ui.stage_look(self.pet.stage)["scale"] * self.ZOOM

    def pet_center(self):
        """Middle of the pet's body (it grows taller as it evolves)."""
        return (self.PET_GROUND[0], self.PET_GROUND[1] - ui.PetRenderer.BODY_H * self.scale / 2)

    def over_pet(self, pos):
        return self.app.pet_renderer.contains(self.PET_GROUND, pos, self.pet.stage, self.ZOOM)

    def xp_bar_tip(self):
        """Where XP sparkles appear. Screens with an XP bar override this."""
        center = self.pet_center()
        return (center[0], center[1] - 60 * self.scale)

    # ---- Shared input ----

    def handle_shortcut(self, key):
        """Keyboard shortcuts that work on every pet screen."""
        if key == pygame.K_f:
            self.react(self.pet.feed())
        elif key == pygame.K_p:
            self.react(self.pet.play())
        elif key == pygame.K_m:
            self.toggle_sound()
        elif key == pygame.K_c:
            self.app.toggle_companion()
        elif key == pygame.K_w:
            self.app.open_wardrobe()

    def toggle_sound(self):
        self.app.sounds.toggle_mute()
        self.app.sounds.play("click")

    # ---- Reactions ----

    def say(self, text):
        self.message = text
        self.message_timer = MESSAGE_SECONDS

    def start_action(self, action):
        self.action = action
        self.action_time = 0.0
        self.last_bite = -1

    def react(self, result, at=None):
        """Show what happened: speech, animation, sound and effects."""
        self.say(result.message)
        sound = self.app.sounds
        center = self.pet_center()
        s = self.scale

        if result.kind not in ANIMATIONS:  # refused (too full / too tired)
            self.start_action("refuse")
            sound.play("refuse")
            return

        self.start_action(ANIMATIONS[result.kind])
        if result.kind == "petted":
            self.effects.hearts(at or (center[0], center[1] - 60 * s))
            sound.play("petted")
        elif result.kind == "played":
            self.effects.sparkles(center, 10)
            sound.play("played")
        # "fed" plays a chomp sound on each bite, in update()

        if result.xp_gained:
            self.effects.floating_text(f"+{result.xp_gained} XP", self.app.fonts.badge, ui.XP_COLOR,
                                       (center[0] + 110 * s, center[1] - 40 * s))
        banner_pos = (center[0], center[1] - 30 * s)
        if result.evolved:
            self.effects.level_up(center, self.app.fonts.banner, banner_pos,
                                  text="EVOLVED!", stars=48, flash=self.FLASH)
            sound.play("evolve")
            self.app.save()  # don't risk losing a big moment
        elif result.levels_gained:
            self.effects.level_up(center, self.app.fonts.banner, banner_pos, flash=self.FLASH)
            sound.play("level_up")
        for i, name in enumerate(result.unlocked):  # new wardrobe items
            self.effects.floating_text(f"New: {name}!", self.app.fonts.badge, ui.HAPPY_COLOR,
                                       (center[0], center[1] + (20 + i * 22) * s), life=2.6)

    # ---- Update ----

    def update(self, dt):
        self.time += dt
        self.pet.update(dt)
        self.effects.update(dt)

        self.autosave_timer -= dt
        if self.autosave_timer <= 0:
            self.autosave_timer = AUTOSAVE_SECONDS
            self.app.save()

        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = None
        if self.away_timer > 0:
            self.away_timer -= dt

        if self.action:
            self.action_time += dt
            progress = self.action_time / ui.ACTION_DURATIONS[self.action]
            if self.action == "eating":
                bite = int(progress * 6)
                if bite != self.last_bite and bite % 2 == 1 and bite < 6:
                    mouth = self.app.pet_renderer.mouth_position(self.PET_GROUND, self.pet.stage, self.ZOOM)
                    self.effects.crumbs(mouth)
                    self.app.sounds.play("fed")
                self.last_bite = bite
            if progress >= 1:
                self.action = None

        # Say something when the mood changes, and now and then on its own.
        mood = self.pet.mood
        self.chatter_timer -= dt
        if mood != self.last_mood or self.chatter_timer <= 0:
            self.last_mood = mood
            self.chatter_timer = random.uniform(*CHATTER_SECONDS)
            if self.message is None and self.action is None:
                self.say(self.pet.idle_message())

    # ---- Drawing helpers ----

    def draw_pet(self, surface, shadow=True):
        progress = self.action_time / ui.ACTION_DURATIONS[self.action] if self.action else 0.0
        self.app.pet_renderer.draw(surface, self.pet.mood, self.PET_GROUND, self.time, stage=self.pet.stage,
                                   action=self.action, progress=min(1.0, progress),
                                   zoom=self.ZOOM, shadow=shadow, species=self.pet.species,
                                   outfit=self.pet.outfit)


class GameScreen(PetScreen):
    """The full-size window: the pet, its stats, and the Feed / Play buttons."""

    PET_GROUND = (WIDTH // 2, 365)

    def __init__(self, app, pet, greeting=None, seconds_away=None):
        super().__init__(app, pet, greeting, seconds_away)

        # Bars animate smoothly toward the real values instead of jumping.
        self.shown = self._targets()
        self.shown_level = pet.level

        fonts = app.fonts
        self.feed_button = ui.Button((24, 568, 200, 54), "Feed", ui.FEED_COLOR, fonts.button)
        self.play_button = ui.Button((WIDTH - 224, 568, 200, 54), "Play", ui.PLAY_COLOR, fonts.button)
        self.sound_button = ui.IconButton((WIDTH - 58, 22, 34, 34), "sound")
        self.companion_button = ui.IconButton((WIDTH - 100, 22, 34, 34), "paw")
        self.wardrobe_button = ui.IconButton((WIDTH - 142, 22, 34, 34), "hanger")
        self.buttons = [self.feed_button, self.play_button, self.sound_button, self.companion_button,
                        self.wardrobe_button]
        self.hand_cursor = False

    def _targets(self):
        return {
            "hunger": self.pet.hunger / 100,
            "happiness": self.pet.happiness / 100,
            "energy": self.pet.energy / 100,
            "xp": self.pet.xp_progress,
        }

    def xp_bar_tip(self):
        return (24 + (WIDTH - 48) * self.shown["xp"], 92)

    def handle_event(self, event):
        if self.feed_button.handle_event(event):
            self.react(self.pet.feed())
        if self.play_button.handle_event(event):
            self.react(self.pet.play())
        if self.sound_button.handle_event(event):
            self.toggle_sound()
        if self.companion_button.handle_event(event):
            self.app.toggle_companion()
            return
        if self.wardrobe_button.handle_event(event):
            self.app.open_wardrobe()
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.over_pet(event.pos):
                self.react(self.pet.cuddle(), at=event.pos)
        elif event.type == pygame.MOUSEMOTION:
            over = self.over_pet(event.pos) or any(button.hovered for button in self.buttons)
            if over != self.hand_cursor:
                self.hand_cursor = over
                ui.set_hand_cursor(over)
        elif event.type == pygame.KEYDOWN:
            self.handle_shortcut(event.key)

    def update(self, dt):
        super().update(dt)
        if self.pet.level != self.shown_level:
            self.shown_level = self.pet.level
            self.shown["xp"] = 0.0  # refill the XP bar from empty after a level up
            self.effects.sparkles(self.xp_bar_tip(), 10)
        ease = min(1.0, dt * 8)
        for key, target in self._targets().items():
            gained = key == "xp" and target > self.shown[key] + 0.01
            self.shown[key] += (target - self.shown[key]) * ease
            if gained and random.random() < 0.25:  # sparkle while the XP bar fills
                self.effects.sparkles(self.xp_bar_tip(), 1)

    def draw(self, surface):
        fonts = self.app.fonts
        pet = self.pet
        surface.blit(self.app.background, (0, 0))

        # Header: name, a tag like "Shy dog · Junior", level, buttons and XP
        name_img = fonts.title.render(pet.name, True, ui.TEXT)
        name_rect = surface.blit(name_img, (24, 16))
        pill_rect = ui.draw_pill(surface, fonts.badge, f"Lv {pet.level}", ui.XP_COLOR,
                                 topright=(self.wardrobe_button.rect.left - 8, 24))
        room = pill_rect.left - 10 - (name_rect.right + 10)
        for text in (f"{pet.personality.capitalize()} {pet.species_name.lower()} · {pet.stage_name}",
                     f"{pet.species_name} · {pet.stage_name}", pet.stage_name):
            tag = fonts.small.render(text, True, ui.TEXT_SOFT)
            if tag.get_width() <= room:  # use the longest version that fits
                surface.blit(tag, tag.get_rect(bottomleft=(name_rect.right + 10, name_rect.bottom - 6)))
                break
        self.sound_button.icon = "muted" if self.app.sounds.muted else "sound"
        self.sound_button.draw(surface)
        self.companion_button.draw(surface)
        self.wardrobe_button.draw(surface)
        xp_label = "Experience"
        if pet.next_stage_level:
            xp_label += f"  ·  evolves at Lv {pet.next_stage_level}"
        ui.draw_stat(surface, fonts.small, (24, 62), WIDTH - 48, xp_label, self.shown["xp"],
                     f"{pet.xp} / {pet.xp_needed} XP", ui.XP_COLOR)

        # The pet, its mood, effects and what it's saying
        self.draw_pet(surface)
        caption_text = self.away_note if self.away_timer > 0 else pet.mood_text()
        caption = fonts.small.render(caption_text, True, ui.TEXT_SOFT)
        surface.blit(caption, caption.get_rect(midtop=(WIDTH // 2, 384)))
        self.effects.draw(surface)
        if self.message:
            alpha = round(255 * min(1.0, self.message_timer / 0.4))  # fade out at the end
            ui.draw_speech_bubble(surface, fonts.body, self.message, (WIDTH // 2, 168), alpha)

        # Stats
        ui.draw_panel(surface, (16, 416, WIDTH - 32, 134))
        stats = [
            ("Hunger", "hunger", pet.hunger, ui.HUNGER_COLOR),
            ("Happiness", "happiness", pet.happiness, ui.HAPPY_COLOR),
            ("Energy", "energy", pet.energy, ui.ENERGY_COLOR),
        ]
        for i, (label, key, value, color) in enumerate(stats):
            ui.draw_stat(surface, fonts.small, (40, 428 + i * 40), WIDTH - 80, label,
                         self.shown[key], f"{round(value)}%", color)

        self.feed_button.draw(surface)
        self.play_button.draw(surface)
        self.effects.draw_overlay(surface)
