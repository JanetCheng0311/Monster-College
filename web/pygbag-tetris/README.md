pygbag prototype — Sir Doggegg Tetris

This folder contains a prototype scaffold to build the Tetris mini-game for the web using `pygbag`.

Quick steps (local):

1. Install pygbag (requires Python >=3.8 and Rust/emscripten toolchain if building locally). For easiest testing, use `pygbag` CLI via pip:

```bash
python -m pip install --user pygbag
```

2. From this folder, build the web distribution:

```bash
cd web/pygbag-tetris
pygbag --build .
```

3. Serve the created `build/` directory with a static server, for example:

```bash
python -m http.server --directory build 8000
```

4. Open `http://localhost:8000` in your browser.

Notes:
- I copied `tetris_game.py` and available assets (background image, mp3s, font) into this folder. If any assets are missing, copy them from `sir_doggegg_nap_break/`.
- The original game may import `moviepy` or do filesystem operations; I left those imports in place but the web build will ignore unsupported native modules. We may need to guard or remove those imports for a clean build.
- If you want, I can continue by adjusting `tetris_game.py` to remove unsupported imports and ensure it sizes correctly to the browser canvas.
