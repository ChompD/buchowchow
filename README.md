# Desktop Pet

A cute, cozy virtual pet built with Python and Pygame. Name your pet, feed it, play with it, and watch it level up.

The long-term goal is a real desktop companion: a small floating pet that stays on your screen while you use other apps.

![Desktop Pet screenshot](docs/screenshot.png)

## Features

**Working now**

- Name your pet when the game starts (or keep the default, "Mochi")
- **Feed** and **Play** buttons, with keyboard shortcuts `F` and `P`
- Hunger, happiness and energy stats that change over time, kept between 0 and 100
- XP and levels, with each level needing a bit more XP than the last
- Five moods (happy, content, hungry, tired, sad), each with its own face and movement
- Speech-bubble reactions to what you do (including "too full" and "too sleepy")

**Planned**

- More animations, random personality messages, sound effects, and clicking on the pet
- XP and level-up visual effects
- Evolution stages unlocked at higher levels
- Saving and loading progress (JSON), including stat changes while the app is closed
- Desktop companion mode: a small, draggable, always-on-top window

## Requirements

- Windows (other systems should work but are untested)
- Python 3.10 or newer (developed on Python 3.14)

This project uses [pygame-ce](https://pyga.me/), the community edition of Pygame. Your code still says `import pygame`, and it has ready-made installs for the newest Python versions. The original `pygame` package doesn't support Python 3.14 yet.

## Installation

```powershell
git clone https://github.com/<your-username>/desktop-pet.git
cd desktop-pet
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell refuses to run `Activate.ps1`, run this once and try again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## Usage

```powershell
python main.py
```

1. Type a name and press **Enter** (or click **Start**).
2. Click **Feed** or **Play** (or press `F` / `P`).
3. Watch the stats and your pet's mood change over time.

| Action | Effect | XP |
|---|---|---|
| Feed | Hunger -30, happiness +5. Refused if the pet is already full. | +10 |
| Play | Happiness +20, energy -15, hunger +10. Refused if the pet is too tired. | +15 |

Over time your pet slowly gets hungrier and less happy, and recovers energy by resting.

## Running the tests

```powershell
pip install -r requirements-dev.txt
python -m pytest
```

## Project structure

```
desktop-pet/
├── main.py              # Window, main loop and screens (naming, game)
├── pet.py               # Pet rules: stats, actions, XP, moods (no Pygame)
├── ui.py                # Drawing: colours, buttons, bars, speech bubble, the pet
├── assets/
│   ├── sprites/         # Custom pet art (coming later)
│   └── sounds/          # Sound effects (coming later)
├── tests/
│   └── test_pet.py      # Tests for the pet rules
├── docs/screenshot.png
├── requirements.txt     # What you need to play
├── requirements-dev.txt # Extra tools for development (pytest)
└── pyproject.toml       # Test settings
```

The game rules in `pet.py` don't import Pygame, so they can be tested without opening a window. The pet is drawn from simple shapes in `ui.PetRenderer`; replacing that class's `draw` method is all it takes to switch to custom sprites later.

## Roadmap

- [x] Phase 1: Basic working pet
- [ ] Phase 2: Personality and animation
- [ ] Phase 3: Progression and saving
- [ ] Phase 4: Desktop companion mode
