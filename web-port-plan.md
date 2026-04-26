Web Port Plan — Monster College

Goal
- Port one mini-game to run in the browser and provide a path to port the rest.

Prototype choice
- Primary prototype: `sir_doggegg_nap_break/tetris_game.py` (Tetris). Reason: self-contained Pygame logic, minimal external deps.

Approach options
- pygbag (recommended): packages Pygame into WebAssembly via Emscripten. Best for Pygame code, minimal rewrite.
- Pyodide + headless rendering: more complex, requires JS canvas glue; better for non-Pygame pure Python logic.
- Full rewrite in JavaScript/HTML5: highest effort, best performance & compatibility.

Feasibility notes
- `tetris_game.py` uses only Pygame and MoviePy for VideoFileClip import (can be removed/fall-back). It references local fonts and audio — these can be bundled.
- `Max Mini Game` and `tiger-game` use MoviePy/OpenCV/Pillow and dynamic file moves; these will be harder to port and may require rewriting or removing video/audio features.
- Any code that uses subprocess/system file moves, arbitrary filesystem writes, or native extensions will need adaptation for the browser environment.

High-level plan (phases)
1. Prepare prototype workspace.
   - Create `web/pygbag-tetris/` with a minimal `index.html` and a Python entry `main.py` that launches the game.
   - Copy `sir_doggegg_nap_break/tetris_game.py`, required assets (`gamebg.png`, audio files, font), and adjust imports/paths.
2. Make code web-ready.
   - Remove or guard MoviePy import and any filesystem operations.
   - Ensure sound load attempts handle failures (no audio in some browsers).
   - Replace absolute font path with relative `./font/...` and ensure font file is included.
   - Reduce WINDOW_W/HEIGHT reliance; let Pygame create a canvas sized to the browser viewport.
3. Build with pygbag.
   - Install `pygbag` (locally or use GitHub Actions later) and run `pygbag --build` to produce `build/` containing `index.html` + WASM.
4. Test locally.
   - Serve the `build/` directory with a simple static server and verify controls, audio, and assets.
5. Iterate and stabilize.
   - Fix input, resize behavior, audio fallback, and performance issues.
6. Document and replicate.
   - Create a README with publish steps and a recipe to port `Max` and `Tiger` (including caveats about video playback).

Immediate next actions (I can do now)
- Scaffold the `web/pygbag-tetris/` folder with `main.py` wrapper and copy assets into it (I can do this if you approve).
- Produce a small `README` with build and publish steps.

Risks & workarounds
- Movie playback: browsers decode video; heavy Python video libs (MoviePy, OpenCV) won't run. Workaround: use HTML5 <video> for intro sequences in the web build, not MoviePy.
- Large asset sizes: MP4 files may inflate the build size; consider hosting video files on GitHub Releases or a CDN and referencing them.

Estimate (prototype only)
- Scaffolding + lightweight code adjustments: 1–3 hours.
- Debug + polish (audio, resize, inputs): 2–6 hours depending on issues.

If you'd like, I will now scaffold `web/pygbag-tetris/` with a `main.py` launcher and copy the Tetris assets for the prototype. Continue?