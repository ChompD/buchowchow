# Desktop Pet

A cute, cozy virtual pet built with Python and Pygame. Pick a fluffy dog, a gray cat or a bunny, name it, feed it, play with it, pet it, and watch it level up and grow from a baby into royalty.

When you want it nearby while you work, switch to **companion mode**: the pet hops out of its window and sits on your desktop, always on top, with a see-through background.

![Desktop Pet screenshot](docs/screenshot.png)

## Features

- Three kinds of pet to choose from:
  - **Dog**: a fluffy golden pup with a topknot, floppy dark-tipped ears and a wagging tail
  - **Gray cat**: forehead stripes, whiskers and a curly tail
  - **Bunny**: tall ears, little teeth and a cotton tail
- Name your pet when the game starts (or keep the default, "Mochi")
- A random personality for every pet (cheerful, playful, foodie, sleepy or shy) and species-specific lines ("*wags tail*", "Purrr...", "*binky!*")
- **Feed** and **Play** buttons, and click the pet to give it a pat
- Hunger, happiness and energy stats that change over time, kept between 0 and 100
- XP and levels, with each level needing a bit more XP than the last
- Five moods (happy, content, hungry, tired, sad), each with its own face and idle animation
- Action animations: munching a cookie, a spinning jump, a squishy wobble when petted, and a head shake when it says no
- Speech bubbles with random lines, plus the pet chatting on its own now and then
- Sound effects, generated in code (no audio files needed), with a mute button
- Visual effects: floating "+XP" text, sparkles, hearts, crumbs, and level-up and evolution bursts
- Four evolution stages, each a bit bigger
- A wardrobe with 15 hats, glasses, neckwear and outfits in 7 colours, with more unlocking as your pet levels up
- Automatic saving, with time passing (gently) while the game is closed
- Damaged save files are backed up instead of crashing the game
- Desktop companion mode: a small, always-on-top pet with a see-through background that walks, runs, naps, looks around and barks at your cursor (or stays put, or turns into a click-through ghost, when you tell it to)

## Requirements

- Windows (other systems should work but are untested; see the note under Companion mode)
- Python 3.10 or newer (developed on Python 3.14)

This project uses [pygame-ce](https://pyga.me/), the community edition of Pygame. Your code still says `import pygame`, and it has ready-made installs for the newest Python versions. The original `pygame` package doesn't support Python 3.14 yet.

## Installation

```powershell
git clone https://github.com/ChompD/buchowchow.git
cd buchowchow
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

1. Pick a dog, gray cat or bunny (click a card, or use the arrow keys), type a name, and press **Enter** (or click **Start**).
2. Click **Feed** or **Play**, or click the pet itself.
3. Watch the stats and your pet's mood change over time.

| Action | How | Effect | XP |
|---|---|---|---|
| Feed | Feed button or `F` | Hunger -30, happiness +5. Refused if the pet is already full. | +10 |
| Play | Play button or `P` | Happiness +20, energy -15, hunger +10. Refused if the pet is too tired. | +15 |
| Pet | Click the pet | Happiness +3 (at most once every 4 seconds) | none |
| Mute | Speaker button or `M` | Turns sound effects on or off | |
| Wardrobe | Hanger button or `W` | Dress up your pet | |
| Companion mode | Paw button or `C` | Switches between the full window and the desktop pet | |

Over time your pet slowly gets hungrier and less happy, and recovers energy by resting.

### Companion mode

Click the paw button (or press `C`) and the pet moves out onto your desktop: a small window with no border, always on top, where only the pet and its speech bubble are visible.

- **A life of its own:** every so often the pet picks something to do: **walk** or **run** along the top of your taskbar (facing the way it goes), **sit**, **lie down**, **look around**, or do a **curious head tilt** with a "?". Its mood decides what it prefers: happy pets run and play more, sad ones lie down more, and tired ones only sit or lie down (with floating Zs). It always does something calm after a walk or run, so it isn't distracting, and it pauses while your mouse is over it.
- **Notices your cursor:** when your mouse comes close, the pet turns to watch it, and sometimes barks with a "!" (the cat meows, the bunny thumps), with a sound. It won't do this more than once every 20 seconds.
- **Stay / Walk:** choose **Stay here** in the right-click menu (or press `S`) and the pet stays in one spot: it still sits, lies down, looks around, tilts its head and notices your cursor, but never walks or runs off. Choose **Walk around** to let it roam again.
- **Ghost mode:** choose **Ghost mode** in the right-click menu (or press `G`) and the pet fades a little and lets *every* click pass straight through it, so it can never get in your way. It keeps doing its thing, but doesn't bark. To reach it again, **hold `Ctrl` and point at the pet**: it turns solid and clickable while you hold `Ctrl`, so you can drag it, pet it, or right-click → **Leave ghost mode**. (Windows only.)
- **Drag** the pet to move it anywhere on screen. With walking on, it drops back down to the taskbar when you let go. In Stay mode it stays where you put it, and snaps neatly against the taskbar or the side of the screen if you drop it close to one.
- **Click** it to give it a pat.
- **Hover** over it to see its level, hunger, happiness and energy.
- **Right-click** it for a menu: Feed, Play, Sound on/off, Stay here / Walk around, Ghost mode, Wardrobe, Big window, Hide, Quit.
- `F`, `P`, `M`, `S`, `G`, `C` and `W` work too, after clicking the pet so its window has focus.
- **Hide** minimizes it; click its taskbar button to bring it back.

Clicks on the see-through area go straight through to whatever is behind, so the pet never gets in the way. The game remembers whether you were in companion mode, whether the pet was walking or staying, whether it was a ghost, and where you left it. If that spot is no longer on screen (say, after unplugging a monitor), it goes back to the bottom-right corner.

Walking and snapping use your main screen. On Windows the game asks where the taskbar is; elsewhere it assumes a 48-pixel taskbar at the bottom.

The see-through background uses a Windows feature (a "colour key": every pixel of one exact colour becomes invisible). On other systems, companion mode still works but has a plain background.

### Wardrobe

Click the hanger button (or press `W`) to dress up your pet. Pick a slot along the middle, click an item to put it on (or **None** to take it off), and choose a colour with the swatches at the bottom. Each card shows your pet wearing that item. Press **Done** (or `Esc`) to go back; the outfit is saved with your pet.

| Slot | Items (unlock level) |
|---|---|
| Head | Bow (1), Flower (1), Party hat (2), Beanie (3), Crown (10) |
| Face | Glasses (1), Sunglasses (4), Heart shades (6) |
| Neck | Bell collar (1), Bandana (2), Bow tie (3), Scarf (5) |
| Outfit | Sweater (1), T-shirt (2), Raincoat (4) |

Everything except the crown and sunglasses comes in pink, red, orange, yellow, green, blue or purple. When a level up unlocks something new, a "New: ..." note pops up over your pet.

To add an item, add it to `ITEMS` in `wardrobe.py` and give it a drawing function in `ui.ITEM_PAINTERS`.

### Evolution

Your pet grows as it levels up. Each stage is a bit bigger:

| Stage | Level |
|---|---|
| Baby | 1 |
| Junior | 3 |
| Adult | 6 |
| Royal | 10 |

Pets saved before the wardrobe existed keep the accessories their stage used to give them (a bow, a bell collar, a crown), and you can change them freely.

### Saving

Your pet is saved to `save.json` in the project folder:

- when you close the window,
- every 30 seconds while you play,
- right after it evolves,
- when you switch modes or finish dragging the companion.

Next time you start the game, your pet is loaded automatically, in whichever mode you left it.

While the game is closed, time still passes for your pet, but 80 times slower, and at most 8 hours count. After a night away it will be hungry and want attention, but it's never in danger.

If the save file is damaged, the game doesn't crash. It renames the file to `save.corrupt-<date>.json` (so nothing is lost) and starts a new pet.

To start over with a new pet, close the game and delete `save.json`.

### Custom sounds

The sound effects are generated in code. To use your own, put a `.wav` or `.ogg` file in `assets/sounds/` named after the effect: `fed`, `played`, `petted`, `refuse`, `level_up`, `evolve`, `click`, `bark`, `meow` or `thump` (for example `assets/sounds/level_up.wav`).

## Running the tests

```powershell
pip install -r requirements-dev.txt
python -m pytest
```

## Project structure

```
buchowchow/
├── main.py              # The App: window, main loop, switching screens and window modes
├── screens.py           # Name screen, shared PetScreen behaviour, and the full game screen
├── companion.py         # Companion mode: the small desktop pet, dragging and its menu
├── wardrobe.py          # Wardrobe rules: items, slots, colours, unlocks, what the pet wears (no Pygame)
├── wardrobe_screen.py   # The Wardrobe screen
├── desktop_window.py    # See-through window and ghost mode (Windows), finding the taskbar, snapping to edges
├── wander.py            # What the companion does on its own: walk, run, sit, lie, look, tilt, bark (no Pygame)
├── pet.py               # Pet rules: stats, actions, XP, moods, personality, evolution (no Pygame)
├── save_manager.py      # Saving/loading save.json, offline time, damaged-file backups
├── messages.py          # Everything the pet can say, by situation, personality and species
├── ui.py                # Drawing: colours, buttons, bars, speech bubble, the pets and their animations
├── effects.py           # Particles, floating text and the level-up / evolution banner
├── sounds.py            # Generated sound effects
├── assets/
│   ├── sprites/         # Custom pet art (coming later)
│   └── sounds/          # Optional custom sound effects
├── tests/               # Tests for the pet rules, wardrobe, walking, saving, messages, sounds and window placement
├── docs/screenshot.png
├── requirements.txt     # What you need to play
├── requirements-dev.txt # Extra tools for development (pytest)
└── pyproject.toml       # Test settings
```

The game rules in `pet.py` don't import Pygame, so they can be tested without opening a window.

The full game and the companion share their behaviour through `screens.PetScreen` (talking, reacting, animations, autosave). `GameScreen` and `CompanionScreen` only decide the layout and how you interact.

Animations work as **poses**: each frame, `ui.idle_pose` (for moods) or `ui.action_pose` (for one-off actions) describes how high the pet is, how squished or rotated it is, and which face it makes. `ui.PetRenderer` then draws that pose. To switch to custom sprites later, only `PetRenderer` needs to change.

Each kind of pet is described in `ui.SPECIES_LOOKS`: its colours, ear style, tail, nose and extras like whiskers or teeth. To add a new animal, add an entry there, add it to `SPECIES` in `messages.py`, and optionally give it its own lines in `BY_SPECIES`.

Saves from before species existed load as a dog.

## Roadmap

- [x] Phase 1: Basic working pet
- [x] Phase 2: Personality and animation
- [x] Phase 3: Progression and saving
- [x] Phase 4: Desktop companion mode

Ideas for later: a focus timer where your pet cheers you on, napping when you're away from the computer, custom pixel-art sprites, and a packaged `.exe` so it runs without Python.
