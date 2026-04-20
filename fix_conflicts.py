import re
from pathlib import Path

path = Path('Monster_College.py')
text = path.read_text(encoding='utf-8')

conflict_re = re.compile(r"<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>>[^\n]*\n", re.S)

def choose(a, b):
    # 1) Intro video config: prefer single VIDEO_PATH if present
    if 'VIDEO_PATH' in a and 'monstercollegeintro.mp4' in a:
        return a + "\n"
    # 2) skip_allowed logic: prefer function parameter version
    if 'skip_allowed = show_skip_hint' in b:
        return b + "\n"
    # 3) draw instruction: prefer robust None-check
    if 'shadow' in b and 'instr_rect' in b and 'shadow_rect' in b:
        return b + "\n"
    # fallback
    return a + "\n"

n_subs = 0

def _repl(m):
    global n_subs
    n_subs += 1
    return choose(m.group(1), m.group(2))

text2 = conflict_re.sub(_repl, text)

# Fix a known bad join where 'while True:' got appended to a comment line.
# Keep indentation of the comment line.
text2 = re.sub(
    r"(?m)^(\s*)# wait until it's time to display this frame \(keeps sync with audio\)\s*while True:\s*$",
    r"\1# wait until it's time to display this frame (keeps sync with audio)\n\1while True:",
    text2,
)

# Also fix any other accidental ']if' tokenization that could remain.
text2 = re.sub(r"\](\s*)if (missing_parts)\s*:", r"]\nif \\2:", text2)

if text2 == text:
    print('No changes made (no conflict markers found).')
else:
    path.write_text(text2, encoding='utf-8')
    print(f'Resolved {n_subs} conflict block(s) and wrote updated {path}.')

# Sanity check: ensure no conflict markers remain
remaining = re.findall(r"<<<<<<<|=======|>>>>>>>", text2)
print('Remaining conflict markers:', len(remaining))
