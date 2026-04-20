import re
from pathlib import Path

p = Path('Monster_College.py')
text = p.read_text(encoding='utf-8')

pattern = re.compile(r"def play_intro_sequence\(\) -> None:\n(?:.|\n)*?\n\n(def play_video\(\) -> None:)", re.M)
replacement = (
    "def play_intro_sequence() -> None:\n"
    "    # Play the single intro video file shipped in menu&map.\n"
    "    play_video_in_pygame(VIDEO_PATH, show_skip_hint=True)\n\n\n"
    "\\1"
)
new_text, n = pattern.subn(replacement, text)

if n != 1:
    raise SystemExit(f'Expected to patch 1 intro sequence block, patched {n}.')

p.write_text(new_text, encoding='utf-8')
print('Patched play_intro_sequence() to use VIDEO_PATH.')
