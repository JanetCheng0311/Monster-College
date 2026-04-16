# Monster School — Competition Day

Interactive branching video where the audience chooses the story.

## Quick Overview

Follow three students — Flying Tiger, Max, and Sir Doggegg—as they head into Competition Day. Viewers vote at key moments; each choice branches the video and changes relationships, challenges, and endings.

## How It Works (short)

- Scenes play as short clips with decision prompts.
- Choices load the next branch; branches may reconverge or lead to unique outcomes.

## Max Mini Game (Pygame)

A fullscreen, side-scrolling shooter mini game.

### What you need in the folder

- Game script: `Max_mini_game/Max Mini Game.py`
- Assets folder: `Max_mini_game/Max_assets/` with these PNGs:
  - `Max_minigame_bg.png`
  - `Max_game_ready_pose.png`
  - `Max_game_ready_shotpose.png`
  - `Laser_shot.png`
  - `wood.png`, `star_wood.png`, `moon_wood.png`, `around_wood.png`

If any file is missing, the game will stop and tell you which image is missing.

### Install (one time)

```powershell
python -m pip install pygame
```

If you use this repo’s venv, you can also do:

```powershell
& .venv/Scripts/python.exe -m pip install pygame
```

### Run

From the repository root (Windows PowerShell):

```powershell
& .venv/Scripts/python.exe "Max_mini_game/Max Mini Game.py"
```

Or with your system Python:

```powershell
python "Max_mini_game/Max Mini Game.py"
```

### Controls

- `W` / `S`: move up / down
- `A` / `D`: move left / right
- `Space`: shoot
- `Esc`: quit

### Scoring (easy rules)

- You play for **60 seconds**.
- You win if your marks are **30 or more** ($\text{Marks} \ge 30$).
- Laser hits:
  - When your laser hits an **unhit** wood for the first time: **+1 mark** and it transforms.
- Touching wood with Max:
  - Touch a **hit / transformed** wood: **+1 mark** (collect it).
  - Touch an **unhit** `wood.png`: **-1 mark**.
- Missed wood:
  - If an **unhit** `wood.png` flies off the **left edge**: **-1 mark**.

## Contribute

