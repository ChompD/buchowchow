"""Small sound effects, generated in code so the project needs no audio files.

To use your own sounds instead, drop a file named after the effect (for
example `fed.wav` or `level_up.ogg`) into assets/sounds/.

If the computer has no working audio device, the game simply stays silent.
"""

import array
import io
import math
import sys
import wave
from pathlib import Path

import pygame

SAMPLE_RATE = 22050

# Each sound is a list of notes: (start Hz, end Hz, seconds, waveform).
# A note that slides from one pitch to another makes "boing" and "chomp" sounds.
RECIPES = {
    "fed": [(260, 170, 0.08, "triangle")],                      # one chomp (played per bite)
    "played": [(300, 760, 0.22, "sine")],                       # boing!
    "petted": [(700, 1000, 0.08, "sine"), (1000, 880, 0.10, "sine")],
    "refuse": [(330, 210, 0.18, "triangle")],
    "level_up": [(523, 523, 0.09, "square"), (659, 659, 0.09, "square"),
                 (784, 784, 0.09, "square"), (1047, 1047, 0.24, "square")],
    "click": [(1100, 900, 0.03, "sine")],
}


def synthesize(notes, volume=0.3):
    """Turn a list of notes into 16-bit audio samples."""
    samples = array.array("h")
    phase = 0.0
    for start, end, seconds, shape in notes:
        count = max(1, int(SAMPLE_RATE * seconds))
        fade = max(1, int(min(0.03, seconds / 3) * SAMPLE_RATE))
        for i in range(count):
            freq = start + (end - start) * i / count
            phase += 2 * math.pi * freq / SAMPLE_RATE
            if shape == "square":
                value = 0.5 if math.sin(phase) >= 0 else -0.5
            elif shape == "triangle":
                value = 2 / math.pi * math.asin(math.sin(phase))
            else:
                value = math.sin(phase)
            envelope = min(1.0, i / 40, (count - i) / fade)  # quick fade in/out avoids clicks
            samples.append(int(value * envelope * volume * 32767))
    return samples


def to_wav(samples):
    """Wrap raw samples in a WAV file held in memory."""
    if sys.byteorder == "big":  # WAV files are little-endian
        samples = array.array("h", samples)
        samples.byteswap()
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(samples.tobytes())
    buffer.seek(0)
    return buffer


class SoundBank:
    """Loads every sound once and plays them by name."""

    def __init__(self, folder):
        self.folder = Path(folder)
        self.sounds = {}
        self.muted = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            for name in RECIPES:
                self.sounds[name] = self._load(name)
        except pygame.error:
            self.sounds = {}  # no audio device: play nothing, but keep the game running

    def _load(self, name):
        for extension in (".wav", ".ogg"):
            path = self.folder / f"{name}{extension}"
            if path.exists():
                try:
                    return pygame.mixer.Sound(str(path))
                except pygame.error:
                    break  # unreadable file: fall back to the built-in sound
        return pygame.mixer.Sound(to_wav(synthesize(RECIPES[name])))

    def play(self, name):
        sound = self.sounds.get(name)
        if sound and not self.muted:
            sound.play()

    def toggle_mute(self):
        self.muted = not self.muted
        return self.muted
