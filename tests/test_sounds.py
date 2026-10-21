"""Tests for the generated sound effects (no audio device needed)."""

import wave

from sounds import RECIPES, SAMPLE_RATE, synthesize, to_wav


def test_every_sound_has_samples_in_range():
    for name, notes in RECIPES.items():
        samples = synthesize(notes)
        expected = sum(int(SAMPLE_RATE * seconds) for _, _, seconds, _ in notes)
        assert len(samples) == expected, name
        assert max(abs(s) for s in samples) <= 32767


def test_sounds_start_and_end_quietly():
    samples = synthesize(RECIPES["played"])
    assert samples[0] == 0
    assert abs(samples[-1]) < 1000


def test_wav_file_is_valid():
    samples = synthesize(RECIPES["click"])
    with wave.open(to_wav(samples)) as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert wav.getframerate() == SAMPLE_RATE
        assert wav.getnframes() == len(samples)
