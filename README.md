# Monster College - Competition Day

Interactive branching video project with several Pygame mini-games.

## Main Entry Point

Run the whole project from the repository root:

```bash
python Monster_College.py
```

This launches the main menu and lets you play the included scenes and mini-games.

## Quick Start

1. Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If large media assets (videos and audio) missing can download using this:

```bash
bash scripts/fetch_assets.sh
# Or supply an alternate Drive folder URL:
bash scripts/fetch_assets.sh "YOUR_DRIVE_FOLDER_URL"
```

## Project Layout

- `Monster_College.py` - main menu / launcher.
- `menu&map/` - map UI and intro videos (`menu&map/intro_video`).
- `sir_doggegg_nap_break/` - Sir Doggegg mini-game and assets (renamed from `tetris_game`).
- `Max_mini_game/` - Max mini-game and assets.
- `tiger-game/` - Tiger mini-game.
- `scripts/fetch_assets.sh` - helper to download large media files.

## Running a Specific Mini-Game

You can launch mini-games from the main menu (Max, Tiger, Sir Doggegg). The launcher imports and executes modules in the same Pygame window.

To run Max directly:

```bash
python "Max_mini_game/Max Mini Game.py"
```

## Assets and File Names

The fetch script expects these asset paths in the Drive folder:

- `menu&map/intro_video/intro01.mp4` to `intro04.mp4`
- `sir_doggegg_nap_break/takeabreak.mp4`
- `sir_doggegg_nap_break/button_clicking_soun_#3-1776674335806.mp3`
- `sir_doggegg_nap_break/tetris_line_clear_so_#4-1776674161372.mp3`
- `sir_doggegg_nap_break/tetris_puzzle_drop_s_#1-1776674215861.mp3`

If you rename assets on the Drive side, update `scripts/fetch_assets.sh` accordingly.

## Development Notes

- Large media files are excluded from Git; use `scripts/fetch_assets.sh` or Git LFS.
- When launched from the map, mini-games reuse the existing Pygame `screen` object; when launched directly they open fullscreen.

## GitHub Pages deployment

- A playable web prototype (Tetris) is available at `docs/index.html`.
- The repo includes a GitHub Actions workflow that publishes the `docs/` folder to the `gh-pages` branch on every push to `main`.

To enable Pages serving from the `gh-pages` branch:
1. Go to your repository Settings → Pages.
2. Under "Source" choose "Deploy from a branch" and set Branch = `gh-pages`, Folder = `/ (root)`, then Save.
3. Wait a minute — your Pages site should appear at the repo Pages URL.

If you prefer to serve directly from `main`/`docs`, instead set Source = `main` and Folder = `/docs` in the Pages settings.