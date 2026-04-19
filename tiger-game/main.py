import os
import sys
import random
import math
import pygame
import importlib
import tempfile
from PIL import Image
import shutil
from PIL import Image

try:
    cv2 = importlib.import_module('cv2')
except Exception:
    cv2 = None

# Simple pygame game:
import shutil

# Simple pygame game:
# - Load background PNG whose filename contains '背景'
# - Load player GIF (animated) and animate frames
# - Load ball PNGs (filename contains 'ball' or '球') and spawn randomly
# - Background scrolls left in an infinite loop
# - Player GIF moves steadily to the right; player controls vertical movement with UP/DOWN
# - On collision with a ball: play sound and score++ (displayed top-left)

# Configuration
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
BG_SPEED = 2           # background scrolling speed (pixels/frame)
PLAYER_SPEED_X = 1.5   # player's automatic rightward speed (pixels/frame)
PLAYER_SPEED_Y = 4     # player's up/down speed when pressing keys
BALL_SPAWN_INTERVAL = 900  # milliseconds (shorter so balls appear more often)
BALL_SPEED = BG_SPEED  # balls move left at background speed so they appear to approach
TARGET_SCORE = 30
GAME_DURATION_SECONDS = 60
PLAYER_SCALE_FACTOR = math.sqrt(0.1 / 6.0)  # base scale used previously
# reduce area to 2/3 of current displayed area: multiply linear scale by sqrt(2/3)
PLAYER_SCALE_FACTOR = PLAYER_SCALE_FACTOR * math.sqrt(2.0/3.0)
# increase collision shrink so touch must be closer (more negative inflate)
COLLISION_MARGIN = 12  # pixels to shrink collision rect on each side to account for transparent padding

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')

def organize_assets():
    """Move game asset files from the project folder into the assets/ directory.
    Files moved: background PNGs containing '背景', any GIF, ball PNGs (containing 'ball' or '球'), and common audio files.
    This uses shutil.move so the original file is removed from its source location.
    """
    os.makedirs(ASSETS_DIR, exist_ok=True)
    moved = []
    for fn in os.listdir(BASE_DIR):
        fpath = os.path.join(BASE_DIR, fn)
        # skip directories and the assets folder itself
        if not os.path.isfile(fpath) or os.path.abspath(os.path.dirname(fpath)) == os.path.abspath(ASSETS_DIR):
            continue
        low = fn.lower()
        should_move = False
        if '背景' in fn and low.endswith('.png'):
            should_move = True
        elif low.endswith('.gif'):
            should_move = True
        elif ("ball" in low or '球' in fn) and low.endswith('.png'):
            should_move = True
        elif low.endswith(('.wav', '.ogg', '.mp3', '.mp4', '.mov', '.avi', '.mkv')):
            should_move = True
        if should_move:
            try:
                target = os.path.join(ASSETS_DIR, fn)
                # if a file with same name exists in assets, avoid overwrite by renaming
                if os.path.exists(target):
                    base, ext = os.path.splitext(fn)
                    i = 1
                    while True:
                        new_name = f"{base}_{i}{ext}"
                        new_target = os.path.join(ASSETS_DIR, new_name)
                        if not os.path.exists(new_target):
                            target = new_target
                            break
                        i += 1
                shutil.move(fpath, target)
                moved.append(fn)
            except Exception as e:
                print('Failed to move', fpath, e)
    if moved:
        print('Moved files to assets:', moved)
    else:
        print('No files moved.')

# Helpers
def load_background():
    if not os.path.isdir(ASSETS_DIR):
        print('Assets folder not found:', ASSETS_DIR)
        return None
    for fn in os.listdir(ASSETS_DIR):
        if '背景' in fn and fn.lower().endswith('.png'):
            path = os.path.join(ASSETS_DIR, fn)
            try:
                img = pygame.image.load(path).convert_alpha()
                return img
            except Exception as e:
                print('Failed to load background', path, e)
    print('No background PNG with "背景" in filename found in assets.')
    return None

def render_multiline(text, font, color, max_width):
    """Render wrapped text into a transparent surface."""
    words = text.split(' ')
    lines = []
    current = ''
    for w in words:
        test = (current + ' ' + w).strip()
        if current and font.size(test)[0] > max_width:
            lines.append(current)
            current = w
        else:
            current = test
    if current:
        lines.append(current)

    line_h = font.get_linesize()
    surf_h = max(1, line_h * max(1, len(lines)))
    surf = pygame.Surface((max_width, surf_h), pygame.SRCALPHA)
    y = 0
    for ln in lines:
        ln_s = font.render(ln, True, color)
        surf.blit(ln_s, (0, y))
        y += line_h
    return surf

def pil_image_to_surface(pil_img):
    mode = pil_img.mode
    size = pil_img.size
    data = pil_img.tobytes()
    return pygame.image.fromstring(data, size, mode).convert_alpha()

def load_gif_frames(path):
    frames = []
    try:
        img = Image.open(path)
    except Exception as e:
        print('Failed to open GIF', path, e)
        return frames
    try:
        n = getattr(img, 'n_frames', 1)
        for frame_index in range(0, n):
            img.seek(frame_index)
            frame = img.convert('RGBA')
            surf = pil_image_to_surface(frame)
            # 缩小到原面积的四分之一 -> 线性尺寸缩小 50%
            w, h = surf.get_width(), surf.get_height()
            new_w = max(1, int(w * PLAYER_SCALE_FACTOR))
            new_h = max(1, int(h * PLAYER_SCALE_FACTOR))
            try:
                surf = pygame.transform.smoothscale(surf, (new_w, new_h))
            except Exception:
                surf = pygame.transform.scale(surf, (new_w, new_h))
            frames.append(surf)
    except EOFError:
        pass
    return frames

def find_player_gif():
    if not os.path.isdir(ASSETS_DIR):
        return None
    for fn in os.listdir(ASSETS_DIR):
        if fn.lower().endswith('.gif'):
            return os.path.join(ASSETS_DIR, fn)
    print('No GIF found in assets for player.')
    return None

def find_ball_images():
    out = []
    if not os.path.isdir(ASSETS_DIR):
        return out
    for fn in os.listdir(ASSETS_DIR):
        low = fn.lower()
        if ("ball" in low or '球' in fn) and low.endswith('.png'):
            out.append(os.path.join(ASSETS_DIR, fn))
    return out

def find_sound():
    if not os.path.isdir(ASSETS_DIR):
        return None
    for fn in os.listdir(ASSETS_DIR):
        if fn.lower().endswith(('.wav', '.ogg', '.mp3')) and ('hit' in fn.lower() or '碰' in fn or 'sound' in fn.lower() or 'audio' in fn.lower()):
            return os.path.join(ASSETS_DIR, fn)
    # fallback: any wav/ogg
    for fn in os.listdir(ASSETS_DIR):
        if fn.lower().endswith(('.wav', '.ogg', '.mp3')):
            return os.path.join(ASSETS_DIR, fn)
    return None

def find_victory_sound():
    if not os.path.isdir(ASSETS_DIR):
        return None
    for fn in os.listdir(ASSETS_DIR):
        low = fn.lower()
        if low.endswith(('.wav', '.ogg', '.mp3')) and ('win' in low or 'victory' in low or '胜利' in fn or 'vict' in low):
            return os.path.join(ASSETS_DIR, fn)
    return find_sound()

def find_ding_sound():
    if not os.path.isdir(ASSETS_DIR):
        return None
    for fn in os.listdir(ASSETS_DIR):
        low = fn.lower()
        if low.endswith(('.wav', '.ogg', '.mp3')) and ('ding' in low or '叮' in fn or 'ding' in low):
            return os.path.join(ASSETS_DIR, fn)
    return None

def find_end_image():
    if not os.path.isdir(ASSETS_DIR):
        return None
    for fn in os.listdir(ASSETS_DIR):
        low = fn.lower()
        if low.endswith('.png') and ('end' in low or '结束' in fn or 'gameover' in low or 'over' in low):
            return os.path.join(ASSETS_DIR, fn)
    return None

def find_failed_end_image():
    if not os.path.isdir(ASSETS_DIR):
        return None
    for fn in os.listdir(ASSETS_DIR):
        low = fn.lower()
        if low.endswith('.png') and ('failed' in low or 'fail' in low or '失败' in fn):
            return os.path.join(ASSETS_DIR, fn)
    return None

def find_player_png_frames():
    """Return list of up to two player PNG paths named like 'tiger*' in assets."""
    out = []
    if not os.path.isdir(ASSETS_DIR):
        return out
    cand = []
    for fn in os.listdir(ASSETS_DIR):
        if fn.lower().endswith('.png') and 'tiger' in fn.lower():
            cand.append(os.path.join(ASSETS_DIR, fn))
    cand.sort()
    # take first two if available
    return cand[:2]

def find_image_by_keywords(keywords):
    if not os.path.isdir(ASSETS_DIR):
        return None
    for fn in os.listdir(ASSETS_DIR):
        low = fn.lower()
        if not low.endswith('.png'):
            continue
        if any(k in low for k in keywords):
            return os.path.join(ASSETS_DIR, fn)
    return None

def find_intro_video():
    if not os.path.isdir(ASSETS_DIR):
        return None
    for fn in os.listdir(ASSETS_DIR):
        low = fn.lower()
        if low.endswith(('.mp4', '.mov', '.avi', '.mkv')) and ('introduce' in low or 'intro' in low or 'tiger' in low):
            return os.path.join(ASSETS_DIR, fn)
    return None

def play_video_fullscreen(screen, clock, video_path):
    if not video_path:
        print('MenuLog: Continue clicked but intro video not found.')
        return
    if cv2 is None:
        print('MenuLog: OpenCV not available, cannot play intro video.')
        return

    cap = cv2.VideoCapture(video_path)
    temp_video_path = None
    if not cap.isOpened():
        # Fallback for Windows + non-ASCII paths: copy to temp ASCII path then open.
        try:
            cap.release()
        except Exception:
            pass
        try:
            suffix = os.path.splitext(video_path)[1] or '.mp4'
            temp_file = tempfile.NamedTemporaryFile(prefix='intro_video_', suffix=suffix, delete=False)
            temp_video_path = temp_file.name
            temp_file.close()
            shutil.copy2(video_path, temp_video_path)
            cap = cv2.VideoCapture(temp_video_path)
        except Exception as e:
            print('MenuLog: failed to prepare temp intro video:', e)
            temp_video_path = None

    if not cap.isOpened():
        print('MenuLog: failed to open intro video:', video_path)
        if temp_video_path and os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
            except Exception:
                pass
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 1:
        fps = 30.0
    frame_delay = max(1, int(1000 / fps))
    scr_w, scr_h = screen.get_size()
    last_frame_surf = None
    last_pos = (0, 0)

    playing = True
    while playing:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                if temp_video_path and os.path.exists(temp_video_path):
                    try:
                        os.remove(temp_video_path)
                    except Exception:
                        pass
                return

        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        fh, fw = frame.shape[:2]
        scale = max(scr_w / fw, scr_h / fh)
        new_w = max(1, int(fw * scale))
        new_h = max(1, int(fh * scale))
        frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        frame_surf = pygame.image.frombuffer(frame.tobytes(), (new_w, new_h), 'RGB')

        x = (scr_w - new_w) // 2
        y = (scr_h - new_h) // 2
        last_frame_surf = frame_surf.copy()
        last_pos = (x, y)
        screen.fill((0, 0, 0))
        screen.blit(frame_surf, (x, y))
        pygame.display.flip()
        clock.tick(max(1, int(1000 / frame_delay)))

    cap.release()
    if temp_video_path and os.path.exists(temp_video_path):
        try:
            os.remove(temp_video_path)
        except Exception:
            pass

    # Keep the video end frame on screen and do not return to end menu by user click/ESC.
    if last_frame_surf is not None:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
            screen.fill((0, 0, 0))
            screen.blit(last_frame_surf, last_pos)
            pygame.display.flip()
            clock.tick(FPS)

# Game objects
class Player:
    def __init__(self, frames, x=50, y=SCREEN_HEIGHT//2):
        self.frames = frames or []
        self.frame_idx = 0
        self.anim_timer = 0
        self.anim_interval = 100  # ms per frame
        self.x = x
        self.y = y
        self.w = frames[0].get_width() if frames else 50
        self.h = frames[0].get_height() if frames else 50

    def update(self, dt, up=False, down=False):
        # animate
        self.anim_timer += dt
        if self.anim_timer >= self.anim_interval:
            self.anim_timer -= self.anim_interval
            self.frame_idx = (self.frame_idx + 1) % max(1, len(self.frames))
        # player stays horizontally fixed (visual movement comes from background/balls)
        # move up/down by input; accept boolean flags for robustness
        if up:
            self.y -= PLAYER_SPEED_Y
        if down:
            self.y += PLAYER_SPEED_Y
        # clamp
        self.y = max(0, min(SCREEN_HEIGHT - self.h, self.y))

    def draw(self, surface, offset_x=0):
        if self.frames:
            surf = self.frames[self.frame_idx]
            surface.blit(surf, (self.x + offset_x, self.y))
        else:
            pygame.draw.rect(surface, (255,0,0), (self.x+offset_x, self.y, 50, 50))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

class Ball:
    def __init__(self, surf, x, y):
        self.surf = surf
        self.x = x
        self.y = y
        self.w = surf.get_width()
        self.h = surf.get_height()

    def update(self, dt):
        self.x -= BALL_SPEED

    def draw(self, surface, offset_x=0):
        surface.blit(self.surf, (self.x + offset_x, self.y))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

# Main
def main(screen: pygame.Surface | None = None):
    pygame.init()
    try:
        if pygame.mixer.get_init() is None:
            pygame.mixer.init()
    except Exception:
        pass
    global SCREEN_WIDTH, SCREEN_HEIGHT
    created_display = False
    # Use native fullscreen mode to avoid desktop scaling bars.
    if screen is None:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        created_display = True
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
    pygame.display.set_caption('Flying Tiger Game')
    clock = pygame.time.Clock()

    # organize assets into assets/ directory
    organize_assets()

    # load assets
    bg_img = load_background()
    green_box_img = None
    start_btn_img = None
    continue_btn_img = None
    retry_btn_img = None
    menu_btn_img = None
    quit_btn_img = None
    green_box_path = os.path.join(ASSETS_DIR, 'green box.png')
    start_btn_path = os.path.join(ASSETS_DIR, 'start.png')
    continue_btn_path = os.path.join(ASSETS_DIR, 'continue.png')
    retry_btn_path = os.path.join(ASSETS_DIR, 'retry.png')
    menu_btn_path = os.path.join(ASSETS_DIR, 'Back to the menu.png')
    quit_btn_path = os.path.join(ASSETS_DIR, 'quit.png')
    intro_video_path = find_intro_video()
    if os.path.exists(green_box_path):
        try:
            green_box_img = pygame.image.load(green_box_path).convert_alpha()
        except Exception as e:
            print('Failed to load green box image', green_box_path, e)
    if os.path.exists(start_btn_path):
        try:
            start_btn_img = pygame.image.load(start_btn_path).convert_alpha()
        except Exception as e:
            print('Failed to load start button image', start_btn_path, e)
    if os.path.exists(continue_btn_path):
        try:
            continue_btn_img = pygame.image.load(continue_btn_path).convert_alpha()
        except Exception as e:
            print('Failed to load continue button image', continue_btn_path, e)
    if os.path.exists(retry_btn_path):
        try:
            retry_btn_img = pygame.image.load(retry_btn_path).convert_alpha()
        except Exception as e:
            print('Failed to load retry button image', retry_btn_path, e)
    if os.path.exists(menu_btn_path):
        try:
            menu_btn_img = pygame.image.load(menu_btn_path).convert_alpha()
        except Exception as e:
            print('Failed to load menu button image', menu_btn_path, e)
    if os.path.exists(quit_btn_path):
        try:
            quit_btn_img = pygame.image.load(quit_btn_path).convert_alpha()
        except Exception as e:
            print('Failed to load quit button image', quit_btn_path, e)
    # Prefer tiger PNG frames (tiger1/tiger2) for transparent player; fallback to GIF
    player_frames = []
    png_paths = find_player_png_frames()
    if png_paths:
        for p in png_paths:
            try:
                img = pygame.image.load(p).convert_alpha()
                # scale player frames so area becomes ~1/10, preserving aspect
                bw, bh = img.get_width(), img.get_height()
                new_w = max(1, int(bw * PLAYER_SCALE_FACTOR))
                new_h = max(1, int(bh * PLAYER_SCALE_FACTOR))
                try:
                    img = pygame.transform.smoothscale(img, (new_w, new_h))
                except Exception:
                    img = pygame.transform.scale(img, (new_w, new_h))
                player_frames.append(img)
            except Exception as e:
                print('Failed to load player png', p, e)
    else:
        player_gif_path = find_player_gif()
        if player_gif_path:
            player_frames = load_gif_frames(player_gif_path)
    ball_imgs = []
    hit_sound = None
    for p in find_ball_images():
        try:
            img = pygame.image.load(p).convert_alpha()
            # 如果球图片过大，按比例缩小以便在屏幕上可见
            max_dim = 80
            bw, bh = img.get_width(), img.get_height()
            if bw > max_dim or bh > max_dim:
                scale = min(max_dim / bw, max_dim / bh)
                new_size = (max(1, int(bw * scale)), max(1, int(bh * scale)))
                try:
                    img = pygame.transform.smoothscale(img, new_size)
                except Exception:
                    img = pygame.transform.scale(img, new_size)
            ball_imgs.append(img)
        except Exception as e:
            print('Failed to load ball image', p, e)
    hit_sound_path = find_sound()
    if hit_sound_path:
        try:
            hit_sound = pygame.mixer.Sound(hit_sound_path)
        except Exception as e:
            print('Failed to load sound', hit_sound_path, e)
    # prefer a ding sound for per-ball scoring if available
    ding_sound_path = find_ding_sound()
    ding_sound = None
    if ding_sound_path:
        try:
            ding_sound = pygame.mixer.Sound(ding_sound_path)
        except Exception as e:
            print('Failed to load ding sound', ding_sound_path, e)
    # set reasonable volumes
    try:
        if ding_sound:
            ding_sound.set_volume(0.6)
        if hit_sound:
            hit_sound.set_volume(0.6)
    except Exception:
        pass
    victory_sound_path = find_victory_sound()
    victory_sound = None
    if victory_sound_path:
        try:
            victory_sound = pygame.mixer.Sound(victory_sound_path)
            try:
                victory_sound.set_volume(0.9)
            except Exception:
                pass
        except Exception as e:
            print('Failed to load victory sound', victory_sound_path, e)

    # background tiling variables
    if bg_img:
        bg_w = bg_img.get_width()
        bg_h = bg_img.get_height()
        scale = max(SCREEN_WIDTH / bg_w, SCREEN_HEIGHT / bg_h)
        if scale != 1:
            new_bw = max(1, int(math.ceil(bg_w * scale)))
            new_bh = max(1, int(math.ceil(bg_h * scale)))
            bg_img = pygame.transform.smoothscale(bg_img, (new_bw, new_bh))
            bg_w = bg_img.get_width()
            bg_h = bg_img.get_height()
    else:
        # fallback solid color
        bg_w = SCREEN_WIDTH
        bg_h = SCREEN_HEIGHT

    bg_offset = 0

    def create_player():
        if player_frames:
            pf_w = player_frames[0].get_width()
            start_x = SCREEN_WIDTH // 2 - pf_w // 2
            return Player(player_frames, x=start_x, y=SCREEN_HEIGHT//2)
        surf = pygame.Surface((50,50), pygame.SRCALPHA)
        surf.fill((255,0,0))
        start_x = SCREEN_WIDTH // 2 - 50 // 2
        return Player([surf], x=start_x, y=SCREEN_HEIGHT//2)

    def create_initial_balls(player_obj):
        new_balls = []
        if ball_imgs:
            for _ in range(4):
                surf = random.choice(ball_imgs)
                player_right_x = player_obj.x + player_obj.w
                min_x = max(player_right_x + 20, SCREEN_WIDTH // 2)
                max_x = max(min_x, SCREEN_WIDTH - surf.get_width())
                if min_x <= max_x:
                    x = random.randint(min_x, max_x)
                else:
                    x = SCREEN_WIDTH + random.randint(50, 400)
                max_y = max(0, SCREEN_HEIGHT - surf.get_height())
                y = random.randint(0, max_y)
                new_balls.append(Ball(surf, x, y))
        return new_balls

    player = create_player()
    balls = create_initial_balls(player)
    SPAWN_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(SPAWN_EVENT, BALL_SPAWN_INTERVAL)

    score = 0
    font = pygame.font.Font(None, 36)
    start_font = pygame.font.Font(None, 30)
    won = False
    failed = False
    end_surface = None
    end_start = None
    show_start_screen = True
    show_end_screen = False
    start_rect = None
    continue_rect = None
    retry_rect = None
    menu_rect = None
    quit_rect = None
    game_start_ticks = None
    game_duration_ms = GAME_DURATION_SECONDS * 1000

    running = True
    move_up = False
    move_down = False
    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if created_display:
                    running = False
                else:
                    return
            elif event.type == SPAWN_EVENT:
                # spawn a ball at random y and x beyond right edge
                if ball_imgs:
                    surf = random.choice(ball_imgs)
                    x = SCREEN_WIDTH + random.randint(50, 400)
                    max_y = max(0, SCREEN_HEIGHT - surf.get_height())
                    y = random.randint(0, max_y)
                    balls.append(Ball(surf, x, y))
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if created_display:
                        running = False
                    else:
                        return
                if event.key == pygame.K_UP:
                    move_up = True
                elif event.key == pygame.K_w:
                    move_up = True
                elif event.key == pygame.K_DOWN:
                    move_down = True
                elif event.key == pygame.K_s:
                    move_down = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_UP:
                    move_up = False
                elif event.key == pygame.K_w:
                    move_up = False
                elif event.key == pygame.K_DOWN:
                    move_down = False
                elif event.key == pygame.K_s:
                    move_down = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if show_start_screen:
                    if start_rect and start_rect.collidepoint(event.pos):
                        show_start_screen = False
                        show_end_screen = False
                        won = False
                        failed = False
                        end_surface = None
                        score = 0
                        player = create_player()
                        balls = create_initial_balls(player)
                        game_start_ticks = pygame.time.get_ticks()
                elif show_end_screen:
                    if retry_rect and retry_rect.collidepoint(event.pos):
                        print('MenuLog: Retry clicked, restarting game.')
                        show_end_screen = False
                        show_start_screen = False
                        won = False
                        failed = False
                        end_surface = None
                        score = 0
                        player = create_player()
                        balls = create_initial_balls(player)
                        game_start_ticks = pygame.time.get_ticks()
                    elif menu_rect and menu_rect.collidepoint(event.pos):
                        print('MenuLog: Menu clicked.')
                        # Match Max Mini Game home behavior: return to caller menu immediately.
                        return
                    elif continue_rect and continue_rect.collidepoint(event.pos):
                        print('MenuLog: Continue clicked, play intro video.')
                        play_video_fullscreen(screen, clock, intro_video_path)
                    elif quit_rect and quit_rect.collidepoint(event.pos):
                        print('MenuLog: Quit clicked, closing game.')
                        if created_display:
                            running = False
                        else:
                            return

        if show_start_screen:
            if bg_img:
                tx = -int(bg_offset) - 2
                while tx < SCREEN_WIDTH + 2:
                    ty = -2
                    while ty < SCREEN_HEIGHT + 2:
                        screen.blit(bg_img, (tx, ty))
                        ty += bg_h
                    tx += bg_w
                if -bg_offset > -bg_w:
                    ty = -2
                    while ty < SCREEN_HEIGHT + 2:
                        screen.blit(bg_img, (-int(bg_offset) - bg_w - 2, ty))
                        ty += bg_h
            else:
                screen.fill((20, 20, 60))

            # green box surface
            box_w = int(SCREEN_WIDTH * 0.76)
            box_h = int(SCREEN_HEIGHT * 0.64)
            if green_box_img:
                try:
                    gb_surf = pygame.transform.smoothscale(green_box_img, (box_w, box_h))
                except Exception:
                    gb_surf = pygame.transform.scale(green_box_img, (box_w, box_h))
            else:
                gb_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
                gb_surf.fill((34, 139, 34, 220))

            gb_rect = gb_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(gb_surf, gb_rect.topleft)

            # instruction text
            instruction = (
                'How to Play: Use UP and DOWN to move the tiger. '
                'Hit balls to score points. Reach 30 points to win. '
                'You only have 60s.'
            )
            txt_surf = render_multiline(instruction, start_font, (0, 0, 0), int(box_w * 0.62))
            txt_x = gb_rect.left + (box_w - txt_surf.get_width()) // 2
            txt_y = gb_rect.top + int(box_h * 0.39)
            screen.blit(txt_surf, (txt_x, txt_y))

            # start button
            btn_w = int(box_w * 0.34)
            btn_h = int(btn_w * 0.35)
            if start_btn_img:
                try:
                    btn_surf = pygame.transform.smoothscale(start_btn_img, (btn_w, btn_h))
                except Exception:
                    btn_surf = pygame.transform.scale(start_btn_img, (btn_w, btn_h))
            else:
                btn_surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
                btn_surf.fill((240, 240, 240, 255))
            start_rect = btn_surf.get_rect(center=(SCREEN_WIDTH // 2, gb_rect.top + int(box_h * 0.78)))
            screen.blit(btn_surf, start_rect.topleft)

            pygame.display.flip()
            continue

        if show_end_screen:
            if end_surface:
                try:
                    end_full = pygame.transform.smoothscale(end_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
                except Exception:
                    end_full = pygame.transform.scale(end_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
                screen.blit(end_full, (0, 0))
            else:
                screen.fill((15, 15, 15))

            btn_w = int(SCREEN_WIDTH * 0.22 * math.sqrt(0.5))
            btn_h = int(btn_w * 0.33)
            center_y = int(SCREEN_HEIGHT * 0.82)
            gap = int(btn_w * 0.45)

            labels = [retry_btn_img, menu_btn_img, continue_btn_img, quit_btn_img]
            count = len(labels)
            total_w = btn_w * count + gap * (count - 1)
            left_x = (SCREEN_WIDTH - total_w) // 2

            def build_button(image_obj, x, y):
                if image_obj:
                    try:
                        s = pygame.transform.smoothscale(image_obj, (btn_w, btn_h))
                    except Exception:
                        s = pygame.transform.scale(image_obj, (btn_w, btn_h))
                else:
                    s = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
                    s.fill((240, 240, 240, 255))
                r = s.get_rect(center=(x, y))
                screen.blit(s, r.topleft)
                return r

            retry_rect = build_button(retry_btn_img, left_x + btn_w // 2, center_y)
            menu_rect = build_button(menu_btn_img, left_x + gap + btn_w + btn_w // 2, center_y)
            continue_rect = build_button(continue_btn_img, left_x + 2 * (gap + btn_w) + btn_w // 2, center_y)
            quit_rect = build_button(quit_btn_img, left_x + 3 * (gap + btn_w) + btn_w // 2, center_y)

            pygame.display.flip()
            continue

        keys = pygame.key.get_pressed()
        if game_start_ticks is None:
            game_start_ticks = pygame.time.get_ticks()
        elapsed_ms = pygame.time.get_ticks() - game_start_ticks
        elapsed_seconds = min(GAME_DURATION_SECONDS, int(elapsed_ms // 1000))
        remaining_ms = max(0, game_duration_ms - elapsed_ms)
        remaining_seconds = int(math.ceil(remaining_ms / 1000.0))

        # Combine get_pressed and explicit key events to be robust
        effective_up = keys[pygame.K_UP] or keys[pygame.K_w] or move_up
        effective_down = keys[pygame.K_DOWN] or keys[pygame.K_s] or move_down
        player.update(dt, effective_up, effective_down)

        # update background offset
        bg_offset = (bg_offset + BG_SPEED) % (bg_w if bg_img else SCREEN_WIDTH)

        # update balls
        for b in balls:
            b.update(dt)
        # remove off-screen balls
        balls = [b for b in balls if b.x + b.w > -100]

        # check collisions (player vs balls)
        p_rect = player.get_rect()
        collided = []
        for b in balls:
            # shrink both rects to avoid transparent-edge false collisions
            try:
                pr = p_rect.inflate(-2*COLLISION_MARGIN, -2*COLLISION_MARGIN)
            except Exception:
                pr = p_rect
            br = b.get_rect()
            try:
                br = br.inflate(-2*COLLISION_MARGIN, -2*COLLISION_MARGIN)
            except Exception:
                br = b.get_rect()
            # ensure rects still have positive size
            if pr.width <= 0 or pr.height <= 0:
                pr = p_rect
            if br.width <= 0 or br.height <= 0:
                br = b.get_rect()
            if pr.colliderect(br):
                collided.append(b)
        for b in collided:
            # only play ding/hit if we haven't reached the target yet
            if score < TARGET_SCORE:
                if ding_sound:
                    try:
                        ding_sound.play()
                    except Exception:
                        pass
                elif hit_sound:
                    try:
                        hit_sound.play()
                    except Exception:
                        pass
            score += 1
            if b in balls:
                balls.remove(b)
        # check win condition after handling collisions
        if not won and score >= TARGET_SCORE:
            won = True
            if victory_sound:
                try:
                    victory_sound.play()
                except Exception:
                    pass
            # load end image
            end_path = find_end_image()
            if end_path:
                try:
                    end_img = pygame.image.load(end_path).convert_alpha()
                    # scale to fit screen while preserving aspect
                    ew, eh = end_img.get_width(), end_img.get_height()
                    scale = min(SCREEN_WIDTH / ew, SCREEN_HEIGHT / eh)
                    new_size = (max(1, int(ew*scale)), max(1, int(eh*scale)))
                    try:
                        # scale to COVER the screen (may crop) so end image fully covers game view
                        scale = max(SCREEN_WIDTH / ew, SCREEN_HEIGHT / eh)
                        new_size = (max(1, int(ew*scale)), max(1, int(eh*scale)))
                        end_surface = pygame.transform.smoothscale(end_img, new_size)
                    except Exception:
                        end_surface = pygame.transform.scale(end_img, new_size)
                except Exception as e:
                    print('Failed to load end image', end_path, e)
            end_start = pygame.time.get_ticks()
            show_end_screen = True

        # countdown ends: if target not reached, show failed end screen
        if not won and not failed and remaining_ms <= 0 and score < TARGET_SCORE:
            failed = True
            fail_end_path = find_failed_end_image()
            if fail_end_path:
                try:
                    fail_end_img = pygame.image.load(fail_end_path).convert_alpha()
                    fw, fh = fail_end_img.get_width(), fail_end_img.get_height()
                    scale = max(SCREEN_WIDTH / fw, SCREEN_HEIGHT / fh)
                    new_size = (max(1, int(fw * scale)), max(1, int(fh * scale)))
                    try:
                        end_surface = pygame.transform.smoothscale(fail_end_img, new_size)
                    except Exception:
                        end_surface = pygame.transform.scale(fail_end_img, new_size)
                except Exception as e:
                    print('Failed to load failed end image', fail_end_path, e)
            end_start = pygame.time.get_ticks()
            show_end_screen = True

        # draw
        if bg_img:
            # 平铺背景，确保完全覆盖屏幕（从 -bg_offset 开始向右一直画到屏幕右边）
            tx = -int(bg_offset) - 2
            while tx < SCREEN_WIDTH + 2:
                ty = -2
                while ty < SCREEN_HEIGHT + 2:
                    screen.blit(bg_img, (tx, ty))
                    ty += bg_h
                tx += bg_w
            # 也向左多画一块以防 bg_offset 很小导致左侧空隙
            if -bg_offset > -bg_w:
                ty = -2
                while ty < SCREEN_HEIGHT + 2:
                    screen.blit(bg_img, (-int(bg_offset) - bg_w - 2, ty))
                    ty += bg_h
        else:
            screen.fill((20, 20, 60))

        # draw balls
        for b in balls:
            b.draw(screen)

        # draw player
        player.draw(screen)

        # draw score as score:X/30
        score_surf = font.render(f'Score: {score}/{TARGET_SCORE}', True, (255,255,255))
        screen.blit(score_surf, (10, 10))

        # draw countdown progress as time:X/60 below score
        timer_surf = font.render(f'Time: {elapsed_seconds}/{GAME_DURATION_SECONDS}', True, (255,255,255))
        screen.blit(timer_surf, (10, 46))

        pygame.display.flip()

    if created_display:
        pygame.quit()


def run(screen: pygame.Surface | None = None):
    """Run tiger game; when embedded, return to caller instead of quitting pygame."""
    return main(screen)

if __name__ == '__main__':
    main()
