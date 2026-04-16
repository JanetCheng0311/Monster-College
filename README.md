# Monster School — Competition Day

Interactive branching video where the audience chooses the story.

## Quick Overview

Follow three students — Flying Tiger, Max, and Sir Doggegg—as they head into Competition Day. Viewers vote at key moments; each choice branches the video and changes relationships, challenges, and endings.

## How It Works (short)

- Scenes play as short clips with decision prompts.
- Choices load the next branch; branches may reconverge or lead to unique outcomes.

## Max Mini Game (Pygame)

A fullscreen, side-scrolling shooter mini game.

- File: `Max_mini_game/Max Mini Game.py`
- Assets folder: `Max_mini_game/Max_assets/`

### Requirements

- Python 3
- Pygame (`pip install pygame`)

### Run

From the repository root (Windows PowerShell):

```powershell
& .venv/Scripts/python.exe "Max_mini_game/Max Mini Game.py"
```

If you are not using the provided venv:

```powershell
python "Max_mini_game/Max Mini Game.py"
```

### Controls

- `W` / `S`: move up / down
- `A` / `D`: move left / right
- `Space`: shoot (laser)
- `Esc`: quit

### Goal / Rules

- Round length: 60 seconds
- Win condition: $\text{Marks} \ge 30$
- Shooting: first time a laser hits a wood, it transforms into a random variant and you gain **+2 marks**
- Penalties:
  - If **unhit** `wood.png` touches Max: **-1 mark**
  - If **unhit** `wood.png` exits the screen on the left: **-1 mark**

## Contribute

