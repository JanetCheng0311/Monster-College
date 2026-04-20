#!/usr/bin/env bash
set -euo pipefail

# fetch_assets.sh
# Download large media assets from a shared Google Drive folder,
# then place them into the correct project directories.

# Ensure asset dirs exist
mkdir -p "menu&map/intro_video" "tetris_game"

DEFAULT_DRIVE_FOLDER_URL="https://drive.google.com/drive/folders/140KtZPATTSU3Ngl9Kr-ivbabi4sqTBL8?usp=sharing"
DRIVE_FOLDER_URL="${1:-$DEFAULT_DRIVE_FOLDER_URL}"
TMP_DIR=".tmp_assets_download"
PYTHON_CMD="python3"

if ! command -v python3 >/dev/null 2>&1; then
	echo "Error: python3 is required."
	exit 1
fi


# Prefer project virtualenv Python when available.
if [[ -x ".venv/bin/python" ]]; then
	PYTHON_CMD=".venv/bin/python"
fi

if ! "$PYTHON_CMD" -m gdown --help >/dev/null 2>&1; then
	echo "Installing gdown..."
	if ! "$PYTHON_CMD" -m pip install gdown; then
		echo "Failed to install gdown automatically."
		echo "Try running:"
		echo "  python3 -m venv .venv"
		echo "  source .venv/bin/activate"
		echo "  python -m pip install gdown"
		exit 1
	fi
fi

rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"

echo "Downloading from Google Drive folder..."
"$PYTHON_CMD" -m gdown --folder "$DRIVE_FOLDER_URL" --output "$TMP_DIR"

copy_asset() {
	local filename="$1"
	local target_path="$2"
	local found_path
	found_path="$(find "$TMP_DIR" -type f -name "$filename" -print -quit)"

	if [[ -n "$found_path" ]]; then
		mkdir -p "$(dirname "$target_path")"
		cp -f "$found_path" "$target_path"
		echo "Placed: $target_path"
	else
		echo "Warning: not found in Drive folder: $filename"
	fi
}

# Intro videos
copy_asset "intro01.mp4" "menu&map/intro_video/intro01.mp4"
copy_asset "intro02.mp4" "menu&map/intro_video/intro02.mp4"
copy_asset "intro03.mp4" "menu&map/intro_video/intro03.mp4"
copy_asset "intro04.mp4" "menu&map/intro_video/intro04.mp4"

# Optional legacy intro file
copy_asset "monstercollegeintro.mp4" "menu&map/monstercollegeintro.mp4"

# Tetris assets
copy_asset "takeabreak.mp4" "tetris_game/takeabreak.mp4"
copy_asset "button_clicking_soun_#3-1776674335806.mp3" "tetris_game/button_clicking_soun_#3-1776674335806.mp3"
copy_asset "tetris_line_clear_so_#4-1776674161372.mp3" "tetris_game/tetris_line_clear_so_#4-1776674161372.mp3"
copy_asset "tetris_puzzle_drop_s_#1-1776674215861.mp3" "tetris_game/tetris_puzzle_drop_s_#1-1776674215861.mp3"

rm -rf "$TMP_DIR"

echo "Download complete."
