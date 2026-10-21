"""Desktop Pet - entry point.

Run with:  python main.py

The App owns the window and the main loop. It switches between the screens in
screens.py and the companion window in companion.py.
"""

from pathlib import Path

import pygame

import companion
import desktop_window
import sounds
import ui
from companion import CompanionScreen
from pet import Pet
from save_manager import DEFAULT_SAVE_PATH, SaveManager
from screens import HEIGHT, WIDTH, GameScreen, NameScreen, PetScreen
from wardrobe_screen import WardrobeScreen

FPS = 60
MAX_FRAME_TIME = 0.25  # ignore long pauses (e.g. while dragging the window)
TITLE = "Desktop Pet"
SOUND_FOLDER = Path(__file__).parent / "assets" / "sounds"


class App:
    """Owns the window and the main loop, and switches between screens."""

    def __init__(self, save_path=DEFAULT_SAVE_PATH):
        pygame.mixer.pre_init(sounds.SAMPLE_RATE, -16, 1, 512)  # small buffer = snappy sounds
        pygame.init()
        self.window = pygame.Window(TITLE, (WIDTH, HEIGHT))
        self.screen = self.window.get_surface()
        self.clock = pygame.time.Clock()
        self.fonts = ui.Fonts()
        self.background = ui.make_gradient((WIDTH, HEIGHT), ui.BG_TOP, ui.BG_BOTTOM)
        self.pet_renderer = ui.PetRenderer(self.fonts.small, self.fonts.title)
        self.window.set_icon(self._make_icon())
        self.sounds = sounds.SoundBank(SOUND_FOLDER)
        self.save_manager = SaveManager(save_path)
        self.running = True

        self.in_companion = False   # is the window currently the small desktop pet?
        self.see_through = False    # did making the background invisible work?
        self.companion_pos = None   # where the companion window was last placed
        self.wardrobe_from_companion = False
        self.walking = True         # does the companion wander, or stay in one spot?

        loaded = self.save_manager.load()
        self.companion_pos = self._checked_position(loaded.settings.get("companion_pos"))
        self.walking = loaded.settings.get("walking") is not False  # on unless switched off
        if loaded.pet:
            screen_class = CompanionScreen if loaded.settings.get("companion") is True else GameScreen
            self.show(screen_class(self, loaded.pet, seconds_away=loaded.seconds_away))
        elif loaded.status == "corrupt":
            where = f" It was kept as {loaded.backup_path.name}." if loaded.backup_path else ""
            self.show(NameScreen(self, notice=f"Your old save file couldn't be read, so here's a new pet.{where}"))
        else:
            self.show(NameScreen(self))

    # ---- Screens and window modes ----

    def show(self, screen):
        """Switch to `screen`, resizing the window if it needs the other mode."""
        wants_companion = isinstance(screen, CompanionScreen)
        if wants_companion != self.in_companion:
            self._set_window_mode(wants_companion)
        self.current = screen

    def _set_window_mode(self, to_companion):
        window = self.window
        if to_companion:
            window.borderless = True
            window.size = companion.SIZE
            window.always_on_top = True
            window.position = self.companion_pos or desktop_window.default_position(
                companion.SIZE, self.desktop_size())
            self.see_through = desktop_window.set_see_through(window.handle)
        else:
            desktop_window.clear_see_through(window.handle)
            self.see_through = False
            window.always_on_top = False
            window.borderless = False
            window.size = (WIDTH, HEIGHT)
            window.position = pygame.WINDOWPOS_CENTERED
        self.screen = window.get_surface()  # the drawing surface changes with the size
        self.in_companion = to_companion
        ui.set_hand_cursor(False)

    def toggle_companion(self):
        """Switch between the full game window and the desktop companion."""
        if not isinstance(self.current, PetScreen):
            return
        pet = self.current.pet
        if self.in_companion:
            self.companion_pos = self.window.position
            self.show(GameScreen(self, pet))
        else:
            self.show(CompanionScreen(self, pet, greeting=pet.say("companion_on")))
        self.save()

    def open_wardrobe(self):
        """Dress up the pet (the wardrobe always opens in the full-size window)."""
        if not isinstance(self.current, PetScreen):
            return
        pet = self.current.pet
        self.wardrobe_from_companion = self.in_companion
        if self.in_companion:
            self.companion_pos = self.window.position
        self.show(WardrobeScreen(self, pet))

    def close_wardrobe(self, changed=False):
        """Go back to wherever the wardrobe was opened from."""
        pet = self.current.pet
        greeting = pet.say("outfit") if changed else None
        back_to = CompanionScreen if self.wardrobe_from_companion else GameScreen
        self.show(back_to(self, pet, greeting=greeting))
        self.save()

    def start_game(self, name, species=None):
        pet = Pet(name, species=species)
        self.show(GameScreen(self, pet, greeting=f"Hi! I'm {pet.name}!"))
        self.save()

    # ---- Saving and quitting ----

    def settings(self):
        if self.in_companion:
            self.companion_pos = self.window.position
        in_wardrobe_from_companion = isinstance(self.current, WardrobeScreen) and self.wardrobe_from_companion
        return {
            "companion": self.in_companion or in_wardrobe_from_companion,
            "companion_pos": list(self.companion_pos) if self.companion_pos else None,
            "walking": self.walking,
        }

    def save(self):
        pet = getattr(self.current, "pet", None)  # the name screen has no pet yet
        if pet is not None:
            self.save_manager.save(pet, self.settings())

    def quit(self):
        self.save()
        self.running = False

    # ---- Helpers ----

    @staticmethod
    def desktop_size():
        sizes = pygame.display.get_desktop_sizes()
        return sizes[0] if sizes else (1280, 720)

    def _checked_position(self, value):
        """A saved window position, if it is valid and still on screen."""
        if (isinstance(value, (list, tuple)) and len(value) == 2
                and all(isinstance(v, int) and not isinstance(v, bool) for v in value)
                and desktop_window.fits_on_screen(value, companion.SIZE, self.desktop_size())):
            return tuple(value)
        return None

    def _make_icon(self):
        """Draw a tiny pet for the taskbar and title bar icon."""
        icon = pygame.Surface((64, 64), pygame.SRCALPHA)
        self.pet_renderer.draw(icon, "happy", (32, 60), 0.0, zoom=0.36, shadow=False)
        return icon

    # ---- Main loop ----

    def step(self, dt):
        """Handle input, update and draw one frame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            else:
                self.current.handle_event(event)
        self.current.update(dt)
        self.current.draw(self.screen)
        self.window.flip()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000, MAX_FRAME_TIME)
            self.step(dt)
        pygame.quit()


def main():
    App().run()


if __name__ == "__main__":
    main()
