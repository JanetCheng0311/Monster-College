#!/usr/bin/env bash
set -euo pipefail
# Helper: change into this script's directory (so you can run it from repo root)
cd "$(dirname "$0")"

# Pass flags before --build to ensure pygbag parses them as options, not as app folder names.
# Use: ./build.sh [extra pygbag args]
pygbag --disable-sound-format-error --build . "$@"
