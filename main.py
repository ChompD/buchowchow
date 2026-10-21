"""Desktop Pet - entry point.

Run with:  python main.py
"""

import random
from pathlib import Path

import pygame

import effects
import sounds
import ui
from pet import DEFAULT_NAME, MAX_NAME_LENGTH, Pet

WIDTH, HEIGHT = 460, 640
FPS = 60
MAX_FRAME_TIME = 0.25        # ignore long pauses (e.g. while dragging the window)
MESSAGE_SECONDS = 3.0
CHATTER_SECONDS = (12, 25)   # the pet says something on its own every 12-25 s
PET_CENTER = (WIDTH // 2, 285)
MOUTH_POS = (PET_CENTER[0] + 20, PET_CENTER[1] + 12)
SOUND_FOLDER = Path(__file__).parent / "assets" / "sounds"

# Which animation plays after a successful action.
ANIMATIONS = {"fed": "eating", "played": "playing", "petted": "petted"}


class NameScreen:
    """First screen: the player types a name for their new pet."""

    def __init__(self, app):
        self.app = app
        self.text = ""
        self.time = 0.0
        self.input_rect = pygame.Rect(60, 396, WIDTH - 120, 50)
        self.start_button = ui.Button((WIDTH // 2 - 100, 474, 200, 54), "Start", ui.PLAY_COLOR, app.fonts.button)
        pygame.key.start_text_input()

    def handle_event(self, event):
        if self.start_button.handle_event(event):
            self.confirm()
        elif event.type == pygame.MOUSEMOTION:
            ui.set_hand_cursor(self.start_button.hovered)
        elif event.type == pygame.TEXTINPUT:
            if event.text.isprintable():
                self.text = (self.text + event.text)[:MAX_NAME_LENGTH]
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.confirm()

    def confirm(self):
        pygame.key.stop_text_input()
        ui.set_hand_cursor(False)
        self.app.sounds.play("click")
        self.app.start_game(self.text)

    def update(self, dt):
        self.time += dt

    def draw(self, surface):
        fonts = self.app.fonts
        surface.blit(self.app.background, (0, 0))

        title = fonts.title.render("Meet your new pet!", True, ui.TEXT)
        surface.blit(title, title.get_rect(midtop=(WIDTH // 2, 32)))
        subtitle = fonts.small.render("Give them a name to get started.", True, ui.TEXT_SOFT)
        surface.blit(subtitle, subtitle.get_rect(midtop=(WIDTH // 2, 76)))

        self.app.pet_renderer.draw(surface, "happy", (WIDTH // 2, 245), self.time)

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


class GameScreen:
    """Main screen: the pet, its stats, and the Feed / Play buttons."""

    def __init__(self, app, pet):
        self.app = app
        self.pet = pet
        self.time = 0.0
        self.effects = effects.Effects()

        self.message = None
        self.message_timer = 0.0
        self.say(f"Hi! I'm {pet.name}!")
        self.chatter_timer = random.uniform(*CHATTER_SECONDS)
        self.last_mood = pet.mood

        # One-off animation currently playing (eating, playing, petted, refuse).
        self.action = None
        self.action_time = 0.0
        self.last_bite = -1

        # Bars animate smoothly toward the real values instead of jumping.
        self.shown = self._targets()
        self.shown_level = pet.level

        fonts = app.fonts
        self.feed_button = ui.Button((24, 568, 200, 54), "Feed", ui.FEED_COLOR, fonts.button)
        self.play_button = ui.Button((WIDTH - 224, 568, 200, 54), "Play", ui.PLAY_COLOR, fonts.button)
        self.sound_button = ui.SoundButton((WIDTH - 58, 22, 34, 34))
        self.sound_button.muted = app.sounds.muted
        self.buttons = [self.feed_button, self.play_button, self.sound_button]
        self.hand_cursor = False

    def _targets(self):
        return {
            "hunger": self.pet.hunger / 100,
            "happiness": self.pet.happiness / 100,
            "energy": self.pet.energy / 100,
            "xp": self.pet.xp_progress,
        }

    # ---- Input ----

    def handle_event(self, event):
        if self.feed_button.handle_event(event):
            self.react(self.pet.feed())
        if self.play_button.handle_event(event):
            self.react(self.pet.play())
        if self.sound_button.handle_event(event):
            self.toggle_sound()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.app.pet_renderer.contains(PET_CENTER, event.pos):
                self.react(self.pet.cuddle(), at=event.pos)
        elif event.type == pygame.MOUSEMOTION:
            over = (self.app.pet_renderer.contains(PET_CENTER, event.pos)
                    or any(button.hovered for button in self.buttons))
            if over != self.hand_cursor:
                self.hand_cursor = over
                ui.set_hand_cursor(over)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                self.react(self.pet.feed())
            elif event.key == pygame.K_p:
                self.react(self.pet.play())
            elif event.key == pygame.K_m:
                self.toggle_sound()

    def toggle_sound(self):
        self.sound_button.muted = self.app.sounds.toggle_mute()
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

        if result.kind not in ANIMATIONS:  # refused (too full / too tired)
            self.start_action("refuse")
            sound.play("refuse")
            return

        self.start_action(ANIMATIONS[result.kind])
        if result.kind == "petted":
            self.effects.hearts(at or (PET_CENTER[0], PET_CENTER[1] - 60))
            sound.play("petted")
        elif result.kind == "played":
            self.effects.sparkles(PET_CENTER, 10)
            sound.play("played")
        # "fed" plays a chomp sound on each bite, in update()

        if result.xp_gained:
            self.effects.floating_text(f"+{result.xp_gained} XP", self.app.fonts.badge, ui.XP_COLOR,
                                       (PET_CENTER[0] + 105, PET_CENTER[1] - 40))
        if result.levels_gained:
            self.effects.level_up(PET_CENTER, self.app.fonts.banner, (WIDTH // 2, PET_CENTER[1] - 30))
            sound.play("level_up")

    def xp_bar_tip(self):
        return (24 + (WIDTH - 48) * self.shown["xp"], 92)

    # ---- Update ----

    def update(self, dt):
        self.time += dt
        self.pet.update(dt)
        self.effects.update(dt)

        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = None

        if self.action:
            self.action_time += dt
            progress = self.action_time / ui.ACTION_DURATIONS[self.action]
            if self.action == "eating":
                bite = int(progress * 6)
                if bite != self.last_bite and bite % 2 == 1 and bite < 6:
                    self.effects.crumbs(MOUTH_POS)
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

    # ---- Draw ----

    def draw(self, surface):
        fonts = self.app.fonts
        pet = self.pet
        surface.blit(self.app.background, (0, 0))

        # Header: name, personality, level, sound toggle and XP
        name_img = fonts.title.render(pet.name, True, ui.TEXT)
        name_rect = surface.blit(name_img, (24, 16))
        trait = fonts.small.render(pet.personality.capitalize(), True, ui.TEXT_SOFT)
        surface.blit(trait, trait.get_rect(bottomleft=(name_rect.right + 10, name_rect.bottom - 6)))
        ui.draw_pill(surface, fonts.badge, f"Lv {pet.level}", ui.XP_COLOR,
                     topright=(self.sound_button.rect.left - 10, 24))
        self.sound_button.draw(surface)
        ui.draw_stat(surface, fonts.small, (24, 62), WIDTH - 48, "Experience", self.shown["xp"],
                     f"{pet.xp} / {pet.xp_needed} XP", ui.XP_COLOR)

        # The pet, its mood, effects and what it's saying
        progress = self.action_time / ui.ACTION_DURATIONS[self.action] if self.action else 0.0
        self.app.pet_renderer.draw(surface, pet.mood, PET_CENTER, self.time,
                                   action=self.action, progress=min(1.0, progress))
        caption = fonts.small.render(pet.mood_text(), True, ui.TEXT_SOFT)
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


class App:
    """Owns the window and the main loop, and switches between screens."""

    def __init__(self):
        pygame.mixer.pre_init(sounds.SAMPLE_RATE, -16, 1, 512)  # small buffer = snappy sounds
        pygame.init()
        pygame.display.set_caption("Desktop Pet")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.fonts = ui.Fonts()
        self.background = ui.make_gradient((WIDTH, HEIGHT), ui.BG_TOP, ui.BG_BOTTOM)
        self.pet_renderer = ui.PetRenderer(self.fonts.small)
        self.sounds = sounds.SoundBank(SOUND_FOLDER)
        self.current = NameScreen(self)
        self.running = True

    def start_game(self, name):
        self.current = GameScreen(self, Pet(name))

    def step(self, dt):
        """Handle input, update and draw one frame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                self.current.handle_event(event)
        self.current.update(dt)
        self.current.draw(self.screen)
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000, MAX_FRAME_TIME)
            self.step(dt)
        pygame.quit()


def main():
    App().run()


if __name__ == "__main__":
    main()
