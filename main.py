"""Desktop Pet - entry point.

Run with:  python main.py
"""

import pygame

import ui
from pet import DEFAULT_NAME, MAX_NAME_LENGTH, Pet

WIDTH, HEIGHT = 460, 640
FPS = 60
MAX_FRAME_TIME = 0.25      # ignore long pauses (e.g. while dragging the window)
MESSAGE_SECONDS = 3.0
PET_CENTER = (WIDTH // 2, 285)


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
        self.message = f"Hi! I'm {pet.name}!"
        self.message_timer = MESSAGE_SECONDS
        # Bars animate smoothly toward the real values instead of jumping.
        self.shown = self._targets()
        self.shown_level = pet.level

        fonts = app.fonts
        self.feed_button = ui.Button((24, 568, 200, 54), "Feed", ui.FEED_COLOR, fonts.button)
        self.play_button = ui.Button((WIDTH - 224, 568, 200, 54), "Play", ui.PLAY_COLOR, fonts.button)

    def _targets(self):
        return {
            "hunger": self.pet.hunger / 100,
            "happiness": self.pet.happiness / 100,
            "energy": self.pet.energy / 100,
            "xp": self.pet.xp_progress,
        }

    def handle_event(self, event):
        if self.feed_button.handle_event(event):
            self.react(self.pet.feed())
        if self.play_button.handle_event(event):
            self.react(self.pet.play())
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                self.react(self.pet.feed())
            elif event.key == pygame.K_p:
                self.react(self.pet.play())

    def react(self, result):
        self.message = result.message
        self.message_timer = MESSAGE_SECONDS

    def update(self, dt):
        self.time += dt
        self.pet.update(dt)

        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = None

        if self.pet.level != self.shown_level:
            self.shown_level = self.pet.level
            self.shown["xp"] = 0.0  # refill the XP bar from empty after a level up
        ease = min(1.0, dt * 8)
        for key, target in self._targets().items():
            self.shown[key] += (target - self.shown[key]) * ease

    def draw(self, surface):
        fonts = self.app.fonts
        pet = self.pet
        surface.blit(self.app.background, (0, 0))

        # Header: name, level and XP
        surface.blit(fonts.title.render(pet.name, True, ui.TEXT), (24, 16))
        ui.draw_pill(surface, fonts.badge, f"Lv {pet.level}", ui.XP_COLOR, topright=(WIDTH - 24, 24))
        ui.draw_stat(surface, fonts.small, (24, 62), WIDTH - 48, "Experience", self.shown["xp"],
                     f"{pet.xp} / {pet.xp_needed} XP", ui.XP_COLOR)

        # The pet, its mood, and what it's saying
        self.app.pet_renderer.draw(surface, pet.mood, PET_CENTER, self.time)
        caption = fonts.small.render(pet.mood_text(), True, ui.TEXT_SOFT)
        surface.blit(caption, caption.get_rect(midtop=(WIDTH // 2, 384)))
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


class App:
    """Owns the window and the main loop, and switches between screens."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Desktop Pet")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.fonts = ui.Fonts()
        self.background = ui.make_gradient((WIDTH, HEIGHT), ui.BG_TOP, ui.BG_BOTTOM)
        self.pet_renderer = ui.PetRenderer(self.fonts.small)
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
