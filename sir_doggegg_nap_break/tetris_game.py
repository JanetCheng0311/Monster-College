import os
import random
import sys
import tempfile
import time
from dataclasses import dataclass

import pygame
from moviepy.video.io.VideoFileClip import VideoFileClip

WIDTH = 10
HEIGHT = 20
CELL = 32
SIDEBAR = 220
BOARD_X = 30
BOARD_Y = 30
# Match the main menu window size so switching between menu and game keeps the same window dimensions
# (menu uses SCREEN_WIDTH=800, SCREEN_HEIGHT=600)
WINDOW_W = 800
WINDOW_H = 600
FPS = 60
START_DROP_MS = 500
MIN_DROP_MS = 30
DEBUG_MIN_MS = 30
PER_LEVEL_DEC = 25
LOCK_DELAY_MS = 700
FONT_PATH = os.path.join(os.path.dirname(__file__), "..", "font", "PixelifySans-VariableFont_wght.ttf")
BG_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "gamebg.png")
MUSIC_PATH = os.path.join(os.path.dirname(__file__), "Cloud Coins.mp3")
BUTTON_CLICK_SFX_PATH = os.path.join(os.path.dirname(__file__), "button_clicking_soun_#3-1776674335806.mp3")
LINE_CLEAR_SFX_PATH = os.path.join(os.path.dirname(__file__), "tetris_line_clear_so_#4-1776674161372.mp3")
PUZZLE_DROP_SFX_PATH = os.path.join(os.path.dirname(__file__), "tetris_puzzle_drop_s_#1-1776674215861.mp3")
INTRO_VIDEO_CANDIDATES = [
    os.path.join(os.path.dirname(__file__), "takebreak.mp4"),
    os.path.join(os.path.dirname(__file__), "takeabreak.mp4"),
]
GAME_TITLE = "Sir Doggegg's Nap Break"
GAME_STORY = (
    "Sir Doggegg is exhausted from a long day of work. "
    "It just wanted a quick nap, but the unfinished tasks followed it into the dream. "
    "Help Sir Doggegg finish its work while it sleeps, and let it wake up relaxed and ready again."
)

BG = (15, 18, 28)
PANEL = (74, 55, 34)
GRID = (166, 131, 86)
TEXT = (250, 242, 224)
MUTED = (232, 214, 182)
ACCENT = (114, 183, 214)
GAME_OVER = (255, 95, 95)

SHAPES = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(1, 0), (0, 1), (1, 1), (0, 2)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}

COLORS = {
    "I": (102, 232, 255),
    "O": (255, 214, 102),
    "T": (186, 102, 255),
    "S": (102, 242, 143),
    "Z": (255, 102, 118),
    "J": (102, 146, 255),
    "L": (255, 170, 102),
}


def new_board():
    return [[None for _ in range(WIDTH)] for _ in range(HEIGHT)]


@dataclass
class Piece:
    kind: str
    x: int = 3
    y: int = 0
    rotation: int = 0

    @property
    def cells(self):
        rotations = SHAPES[self.kind]
        return rotations[self.rotation % len(rotations)]

    @property
    def color(self):
        return COLORS[self.kind]


class Tetris:
    def __init__(self, screen=None):
        pygame.init()
        pygame.display.set_caption(GAME_TITLE)
        # open in fullscreen when launched directly; reuse the provided screen when launched from the map
        if screen is None:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = screen
        self.audio_enabled = False
        self.game_music = None
        self.game_music_channel = None
        self.button_click_sfx = None
        self.line_clear_sfx = None
        self.puzzle_drop_sfx = None
        self.puzzle_drop_boost_sfx = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.audio_enabled = pygame.mixer.get_init() is not None
        except Exception as e:
            print(f"Warning: Could not initialize audio mixer: {e}")
        # update module-level window size constants to actual screen size
        w, h = self.screen.get_size()
        globals()["WINDOW_W"] = w
        globals()["WINDOW_H"] = h
        # scale fonts relative to window height and keep them about 30% smaller than before
        small_fs = max(10, int(h * 0.022))
        big_fs = max(16, int(h * 0.039))
        self.font = pygame.font.Font(FONT_PATH, small_fs)
        self.big_font = pygame.font.Font(FONT_PATH, big_fs)
        preview_cell = max(12, int(self.font.get_height() * 0.9))
        hold_panel_w = max(120, preview_cell * 4 + 28)

        # center the full layout, including the left hold/next panel and right sidebar
        total_board_w = hold_panel_w + WIDTH * CELL + SIDEBAR + 30
        total_board_h = HEIGHT * CELL
        left_edge = max(0, (w - total_board_w) // 2)
        new_board_x = left_edge + hold_panel_w + 20
        new_board_y = max(0, (h - total_board_h) // 2)
        globals()["BOARD_X"] = new_board_x
        globals()["BOARD_Y"] = new_board_y
        self.clock = pygame.time.Clock()
        # load background image and scale it to screen size
        try:
            bg_img = pygame.image.load(BG_IMAGE_PATH)
            self.bg_image = pygame.transform.scale(bg_img, (w, h))
        except Exception as e:
            print(f"Warning: Could not load background image: {e}")
            self.bg_image = None
        if self.audio_enabled:
            try:
                # Prefer explicit MUSIC_PATH, but fall back to any other mp3 in the folder
                if os.path.exists(MUSIC_PATH):
                    try:
                        self.game_music = pygame.mixer.Sound(MUSIC_PATH)
                        print(f"Debug: loaded game music from {MUSIC_PATH}")
                    except Exception as e:
                        print(f"Debug: failed to load MUSIC_PATH {MUSIC_PATH}: {e}")
                else:
                    # scan for mp3 files in this directory as a fallback (excluding known SFX)
                    dirpath = os.path.dirname(__file__)
                    candidates = [f for f in os.listdir(dirpath) if f.lower().endswith('.mp3')]
                    # exclude sfx filenames
                    exclude = {os.path.basename(BUTTON_CLICK_SFX_PATH), os.path.basename(LINE_CLEAR_SFX_PATH), os.path.basename(PUZZLE_DROP_SFX_PATH)}
                    candidates = [c for c in candidates if c not in exclude]
                    if candidates:
                        pick = os.path.join(dirpath, candidates[0])
                        try:
                            self.game_music = pygame.mixer.Sound(pick)
                            print(f"Debug: loaded fallback game music from {pick}")
                        except Exception as e:
                            print(f"Warning: fallback music found but failed to load: {e}")
                # defer channel allocation until play time; use find_channel() to avoid conflicts
                self.game_music_channel = None
            except Exception as e:
                print(f"Warning: Could not load game music: {e}")
        if self.audio_enabled:
            try:
                if os.path.exists(BUTTON_CLICK_SFX_PATH):
                    self.button_click_sfx = pygame.mixer.Sound(BUTTON_CLICK_SFX_PATH)
                    self.button_click_sfx.set_volume(0.7)
                if os.path.exists(LINE_CLEAR_SFX_PATH):
                    self.line_clear_sfx = pygame.mixer.Sound(LINE_CLEAR_SFX_PATH)
                    self.line_clear_sfx.set_volume(0.7)
                if os.path.exists(PUZZLE_DROP_SFX_PATH):
                    self.puzzle_drop_sfx = pygame.mixer.Sound(PUZZLE_DROP_SFX_PATH)
                    self.puzzle_drop_sfx.set_volume(1.0)
                    self.puzzle_drop_boost_sfx = pygame.mixer.Sound(PUZZLE_DROP_SFX_PATH)
                    self.puzzle_drop_boost_sfx.set_volume(0.5)
            except Exception as e:
                print(f"Warning: Could not load one or more SFX files: {e}")
        self.board = new_board()
        self.current = None
        self.next_piece = self.random_piece()
        # held piece (player can store one piece and swap once per spawn)
        self.hold_piece = None
        self.can_hold = True
        self.game_over = False
        self.score = 0
        self.lines = 0
        self.level = 1
        self.drop_ms = START_DROP_MS
        self.debug_mode = False
        self.debug_offset_ms = 0
        self.debug_step_ms = 200
        self.drop_accumulator = 0
        self.lock_timer_ms = 0
        self.on_ground = False
        self.mode_name = "Easy Mode"
        self.mode_start_drop_ms = START_DROP_MS
        self.mode_per_level_dec = PER_LEVEL_DEC
        self.mode_lock_delay_ms = LOCK_DELAY_MS
        self.mode_min_drop_ms = MIN_DROP_MS
        # Default win threshold (Easy mode). This is updated when a mode
        # is selected via `apply_mode_settings()` during the start sequence.
        self.mode_win_lines = 20
        self.has_won = False
        self.return_to_map = False
        self.spawn_piece()
        # Horizontal hold-to-repeat state
        self.hold_dir = None  # -1 for left, 1 for right, None for no hold
        self.hold_time = 0
        self.hold_repeat_acc = 0
        self.hold_delay_ms = 300  # delay before repeating when holding
        self.hold_repeat_interval = 80  # repeat interval in ms

    def random_piece(self):
        return Piece(random.choice(list(SHAPES.keys())))

    def spawn_piece(self):
        self.current = self.next_piece
        self.current.x = 3
        self.current.y = 0
        self.current.rotation = 0
        # choose a next piece that is not the same type as the piece we just spawned
        self.next_piece = self.random_piece()
        while self.next_piece.kind == self.current.kind:
            self.next_piece = self.random_piece()
        if self.collides(self.current, 0, 0, self.current.rotation):
            # If a spawn immediately collides the board, it's a top-out game over.
            # If the player has already reached the win threshold (when the
            # mode defines one) consider this a win for the end-overlay.
            self.has_won = (self.mode_win_lines is not None) and (self.lines >= self.mode_win_lines)
            self.game_over = True
        # after spawning a new piece, allow holding again
        self.can_hold = True
        self.lock_timer_ms = 0
        self.on_ground = False

    def reset_lock_delay(self):
        self.lock_timer_ms = 0
        self.on_ground = False

    def collides(self, piece, dx, dy, rotation):
        rotations = SHAPES[piece.kind]
        cells = rotations[rotation % len(rotations)]
        for cx, cy in cells:
            x = piece.x + dx + cx
            y = piece.y + dy + cy
            if x < 0 or x >= WIDTH or y >= HEIGHT:
                return True
            if y >= 0 and self.board[y][x] is not None:
                return True
        return False

    def lock_piece(self):
        if self.puzzle_drop_sfx is not None:
            try:
                self.puzzle_drop_sfx.play()
                if self.puzzle_drop_boost_sfx is not None:
                    self.puzzle_drop_boost_sfx.play()
            except Exception:
                pass
        for cx, cy in self.current.cells:
            x = self.current.x + cx
            y = self.current.y + cy
            if 0 <= y < HEIGHT:
                self.board[y][x] = self.current.color
        cleared = self.clear_lines()
        if cleared:
            if self.line_clear_sfx is not None:
                try:
                    self.line_clear_sfx.play()
                except Exception:
                    pass
            self.lines += cleared
            self.score += [0, 100, 300, 500, 800][cleared] * self.level
            self.level = 1 + self.lines // 2
            self.drop_ms = self.compute_drop_ms()
            # If the player reached the win threshold, mark `has_won` but do
            # not immediately end the play session — allow continued play
            # until a real top-out occurs. The final overlay will show the
            # win if `has_won` is True when the game ultimately ends.
            if self.mode_win_lines is not None and self.lines >= self.mode_win_lines:
                self.has_won = True
        self.spawn_piece()

    def hold_current(self):
        """Store the current piece, or swap it with the stored piece.

        Holding is allowed only once per spawn; after a hold, `can_hold` is False
        until the next piece is spawned (i.e., after lock_piece).
        """
        if not self.can_hold or self.game_over or self.current is None:
            return

        if self.hold_piece is None:
            # store the current piece and spawn the next one
            self.hold_piece = Piece(self.current.kind)
            self.spawn_piece()
            # disallow holding again until next lock
            self.can_hold = False
        else:
            # swap current and held pieces
            held_kind = self.hold_piece.kind
            self.hold_piece = Piece(self.current.kind)
            # replace current with the held piece
            self.current = Piece(held_kind)
            self.current.x = 3
            self.current.y = 0
            self.current.rotation = 0
            # if swapping produces immediate collision, game over
            if self.collides(self.current, 0, 0, self.current.rotation):
                # Treat a hold-swap top-out similarly: if lines already meet
                # the win threshold, reflect a win on the overlay.
                self.has_won = (self.mode_win_lines is not None) and (self.lines >= self.mode_win_lines)
                self.game_over = True
            self.can_hold = False

    def clear_lines(self):
        new_rows = [row for row in self.board if any(cell is None for cell in row)]
        cleared = HEIGHT - len(new_rows)
        while len(new_rows) < HEIGHT:
            new_rows.insert(0, [None for _ in range(WIDTH)])
        self.board = new_rows
        return cleared

    def move(self, dx):
        if not self.game_over and not self.collides(self.current, dx, 0, self.current.rotation):
            self.current.x += dx
            self.reset_lock_delay()

    def soft_drop(self):
        if not self.game_over and not self.collides(self.current, 0, 1, self.current.rotation):
            self.current.y += 1
            self.score += 1
            self.reset_lock_delay()
            return True
        return False

    def hard_drop(self):
        if self.game_over:
            return
        while not self.collides(self.current, 0, 1, self.current.rotation):
            self.current.y += 1
            self.score += 2
        self.lock_piece()

    def rotate(self):
        if self.game_over:
            return
        next_rotation = (self.current.rotation + 1) % len(SHAPES[self.current.kind])
        kicks = [0, -1, 1, -2, 2]
        for kick in kicks:
            if not self.collides(self.current, kick, 0, next_rotation):
                self.current.x += kick
                self.current.rotation = next_rotation
                self.reset_lock_delay()
                return

    def restart(self):
        self.board = new_board()
        self.current = None
        self.next_piece = self.random_piece()
        self.hold_piece = None
        self.can_hold = True
        self.game_over = False
        self.score = 0
        self.lines = 0
        self.level = 1
        self.has_won = False
        self.drop_ms = self.compute_drop_ms()
        self.drop_accumulator = 0
        self.spawn_piece()

    def compute_drop_ms(self):
        base = self.mode_start_drop_ms - (self.level - 1) * self.mode_per_level_dec
        value = base + self.debug_offset_ms
        if self.debug_mode:
            return max(DEBUG_MIN_MS, int(value))
        return max(self.mode_min_drop_ms, int(value))

    def start_game_music(self):
        if self.game_music is None:
            print("Debug: start_game_music aborted: no game_music")
            return
        # Attempt to find a free mixer channel to avoid colliding with SFX
        if self.game_music_channel is None:
            try:
                ch = pygame.mixer.find_channel()
                if ch is None:
                    # ensure at least 8 channels are available then try again
                    try:
                        pygame.mixer.set_num_channels(max(8, pygame.mixer.get_num_channels()))
                        ch = pygame.mixer.find_channel()
                    except Exception:
                        ch = None
                if ch is not None:
                    self.game_music_channel = ch
                else:
                    # fallback to a fixed channel index if no free channel found
                    try:
                        self.game_music_channel = pygame.mixer.Channel(1)
                    except Exception:
                        self.game_music_channel = None
            except Exception as e:
                print(f"Debug: error finding channel: {e}")

        if self.game_music_channel is None:
            print("Debug: no available channel to play game music")
            return

        try:
            print(f"Debug: start_game_music called. channel_busy={self.game_music_channel.get_busy()}")
        except Exception:
            pass

        if not self.game_music_channel.get_busy():
            # Reduce baseline music volume by ~15%
            base_vol = 0.9
            vol = max(0.0, base_vol * 0.85)
            print(f"Debug: setting game music volume to {vol}")
            try:
                self.game_music_channel.set_volume(vol)
            except Exception:
                pass
            try:
                self.game_music_channel.play(self.game_music, loops=-1)
                print("Debug: started game music on channel")
            except Exception as e:
                print(f"Debug: failed to start game music: {e}")

    def request_return_to_map(self):
        self.return_to_map = True
        try:
            if self.audio_enabled:
                pygame.mixer.music.stop()
        except Exception:
            pass
        if self.game_music_channel is not None:
            try:
                self.game_music_channel.stop()
            except Exception:
                pass

    def wrap_text(self, text, font, max_width):
        words = text.split()
        lines = []
        current = ""
        for word in words:
            trial = word if not current else f"{current} {word}"
            if font.size(trial)[0] <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def apply_mode_settings(self, mode_name):
        if mode_name == "Difficult Mode":
            self.mode_name = "Difficult Mode"
            self.mode_start_drop_ms = 430
            self.mode_per_level_dec = 32
            self.mode_lock_delay_ms = 520
            self.mode_min_drop_ms = 100
            self.mode_win_lines = 30
        else:
            self.mode_name = "Easy Mode"
            self.mode_start_drop_ms = 520
            self.mode_per_level_dec = 24
            self.mode_lock_delay_ms = 700
            self.mode_min_drop_ms = 200
            self.mode_win_lines = 20

    def title_lines(self):
        return ["Sir Doggegg's", "Nap Break"]

    def play_intro_video(self, path):
        if path is None or not os.path.exists(path):
            return None

        clip = None
        audio_temp_path = None
        last_surface = None
        try:
            clip = VideoFileClip(path)
            fps = clip.fps if clip.fps and clip.fps > 0 else 24
            frame_interval = 1.0 / float(fps)

            fallback_start_time = time.perf_counter()

            def _playback_time_s():
                if self.audio_enabled and pygame.mixer.get_init() is not None:
                    try:
                        pos_ms = pygame.mixer.music.get_pos()
                        if pos_ms >= 0:
                            return pos_ms / 1000.0
                    except Exception:
                        pass
                return max(0.0, time.perf_counter() - fallback_start_time)

            if clip.audio is not None and self.audio_enabled:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    audio_temp_path = tmp.name
                clip.audio.write_audiofile(
                    audio_temp_path,
                    fps=44100,
                    nbytes=2,
                    codec="pcm_s16le",
                    logger=None,
                )
                pygame.mixer.music.load(audio_temp_path)
                pygame.mixer.music.set_volume(1.0)
                # Ensure the intro audio plays only once (no looping)
                pygame.mixer.music.play(loops=0)
                fallback_start_time = time.perf_counter()

            frame_index = 0
            for frame in clip.iter_frames(fps=fps, dtype="uint8"):
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                        return last_surface

                playback_time = _playback_time_s()
                expected_index = int(playback_time * fps)
                if frame_index < expected_index - 1:
                    frame_index += 1
                    continue
                while frame_index > expected_index + 1:
                    time.sleep(0.001)
                    playback_time = _playback_time_s()
                    expected_index = int(playback_time * fps)

                frame_surface = pygame.image.frombuffer(
                    frame.tobytes(), (frame.shape[1], frame.shape[0]), "RGB"
                )
                frame_surface = pygame.transform.scale(frame_surface, (WINDOW_W, WINDOW_H))
                last_surface = frame_surface.copy()

                self.screen.blit(frame_surface, (0, 0))
                skip_hint = self.font.render("Press TAB to skip", True, (255, 255, 255))
                self.screen.blit(skip_hint, (30, WINDOW_H - 44))
                pygame.display.flip()
                frame_index += 1
                time.sleep(min(frame_interval * 0.3, 0.005))
        except Exception as e:
            print(f"Warning: Could not play intro video: {e}")
        finally:
            if self.audio_enabled:
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass
            if clip is not None:
                clip.close()
            if audio_temp_path is not None and os.path.exists(audio_temp_path):
                try:
                    os.remove(audio_temp_path)
                except OSError:
                    pass

        return last_surface

    def show_intro_rules_card(self, last_frame):
        card_w = min(900, WINDOW_W - 120)
        card_h = min(520, WINDOW_H - 120)
        card_x = (WINDOW_W - card_w) // 2
        card_y = (WINDOW_H - card_h) // 2

        title_font = pygame.font.Font(FONT_PATH, max(22, int(WINDOW_H * 0.04)))
        info_font = pygame.font.Font(FONT_PATH, max(14, int(WINDOW_H * 0.024)))

        story_lines = self.wrap_text(GAME_STORY, info_font, card_w - 80)
        rules = [
            "Rules:",
            "- Clear lines to help Sir Doggegg finish dream tasks.",
            "- Move/rotate quickly before each piece locks.",
            "- Every 2 lines raises speed.",
            "- Hold one piece with C or Left Shift.",
        ]

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_TAB):
                    if self.button_click_sfx is not None:
                        try:
                            self.button_click_sfx.play()
                        except Exception:
                            pass
                    return

            self.draw_game_background()

            dim = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 120))
            self.screen.blit(dim, (0, 0))

            pygame.draw.rect(self.screen, (250, 250, 250), (card_x, card_y, card_w, card_h), border_radius=20)
            pygame.draw.rect(self.screen, (55, 55, 55), (card_x, card_y, card_w, card_h), 2, border_radius=20)

            title_y = card_y + 24
            for line in self.title_lines():
                title_surface = title_font.render(line, True, (28, 28, 28))
                self.screen.blit(title_surface, (card_x + 30, title_y))
                title_y += title_surface.get_height() + 2

            y = title_y + 18
            for line in story_lines:
                s = info_font.render(line, True, (40, 40, 40))
                self.screen.blit(s, (card_x + 32, y))
                y += info_font.get_height() + 8

            y += 14
            for line in rules:
                s = info_font.render(line, True, (30, 30, 30))
                self.screen.blit(s, (card_x + 32, y))
                y += info_font.get_height() + 8

            tip = info_font.render("Press ENTER to continue", True, (50, 50, 50))
            self.screen.blit(tip, (card_x + 32, card_y + card_h - 42))
            pygame.display.flip()
            self.clock.tick(FPS)

    def show_mode_select(self):
        modes = ["Easy Mode", "Difficult Mode"]
        selected = 0
        title_font = pygame.font.Font(FONT_PATH, max(24, int(WINDOW_H * 0.045)))
        info_font = pygame.font.Font(FONT_PATH, max(15, int(WINDOW_H * 0.026)))

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_UP, pygame.K_w):
                    if self.button_click_sfx is not None:
                        try:
                            self.button_click_sfx.play()
                        except Exception:
                            pass
                    selected = (selected - 1) % len(modes)
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_DOWN, pygame.K_s):
                    if self.button_click_sfx is not None:
                        try:
                            self.button_click_sfx.play()
                        except Exception:
                            pass
                    selected = (selected + 1) % len(modes)
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.button_click_sfx is not None:
                        try:
                            self.button_click_sfx.play()
                        except Exception:
                            pass
                    return modes[selected]

            self.draw_game_background()

            dim = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 120))
            self.screen.blit(dim, (0, 0))

            panel_w, panel_h = min(840, WINDOW_W - 120), 420
            panel_x = (WINDOW_W - panel_w) // 2
            panel_y = (WINDOW_H - panel_h) // 2
            pygame.draw.rect(self.screen, (250, 250, 250), (panel_x, panel_y, panel_w, panel_h), border_radius=20)
            pygame.draw.rect(self.screen, (55, 55, 55), (panel_x, panel_y, panel_w, panel_h), 2, border_radius=20)

            title_top = panel_y + 24
            for line in self.title_lines():
                title = title_font.render(line, True, (25, 25, 25))
                self.screen.blit(title, title.get_rect(center=(WINDOW_W // 2, title_top + title.get_height() // 2)))
                title_top += title.get_height() + 2

            mode_desc = {
                "Easy Mode": "Win by clearing 20 lines. Min speed is 200ms.",
                "Difficult Mode": "Win by clearing 30 lines. Faster pace and shorter lock delay.",
            }

            y = panel_y + 186
            for i, mode in enumerate(modes):
                is_selected = i == selected
                row_color = (230, 240, 255) if is_selected else (240, 240, 240)
                text_color = (25, 25, 25)
                pygame.draw.rect(self.screen, row_color, (panel_x + 42, y - 10, panel_w - 84, 84), border_radius=10)
                mode_text = info_font.render(mode, True, text_color)
                desc_text = info_font.render(mode_desc[mode], True, (55, 55, 55))
                marker = ">" if is_selected else " "
                marker_text = info_font.render(marker, True, (35, 90, 140))
                self.screen.blit(marker_text, (panel_x + 52, y + 12))
                self.screen.blit(mode_text, (panel_x + 76, y))
                self.screen.blit(desc_text, (panel_x + 76, y + 36))
                y += 104

            hint = info_font.render("Use UP/DOWN and ENTER to start", True, (45, 45, 45))
            self.screen.blit(hint, hint.get_rect(center=(WINDOW_W // 2, panel_y + panel_h - 24)))
            pygame.display.flip()
            self.clock.tick(FPS)

    def return_to_mode_select(self):
        selected_mode = self.show_mode_select()
        self.apply_mode_settings(selected_mode)
        self.restart()

    def show_start_sequence(self):
        intro_path = next((p for p in INTRO_VIDEO_CANDIDATES if os.path.exists(p)), None)
        last_frame = self.play_intro_video(intro_path) if intro_path else None
        self.show_intro_rules_card(last_frame)
        selected_mode = self.show_mode_select()
        self.apply_mode_settings(selected_mode)
        self.restart()

    def draw_cell(self, x, y, color):
        rect = pygame.Rect(BOARD_X + x * CELL, BOARD_Y + y * CELL, CELL, CELL)
        pygame.draw.rect(self.screen, color, rect.inflate(-3, -3), border_radius=6)
        pygame.draw.rect(self.screen, (255, 255, 255), rect.inflate(-3, -3), 1, border_radius=6)

    def draw_board(self):
        pygame.draw.rect(self.screen, PANEL, (BOARD_X - 10, BOARD_Y - 10, WIDTH * CELL + 20, HEIGHT * CELL + 20), border_radius=18)
        for y in range(HEIGHT):
            for x in range(WIDTH):
                cell = self.board[y][x]
                if cell is not None:
                    self.draw_cell(x, y, cell)
                else:
                    rect = pygame.Rect(BOARD_X + x * CELL, BOARD_Y + y * CELL, CELL, CELL)
                    pygame.draw.rect(self.screen, GRID, rect, 1)
        if self.current and not self.game_over:
            for cx, cy in self.current.cells:
                x = self.current.x + cx
                y = self.current.y + cy
                if y >= 0:
                    self.draw_cell(x, y, self.current.color)

    def draw_sidebar(self):
        sx = BOARD_X + WIDTH * CELL + 30
        pygame.draw.rect(self.screen, PANEL, (BOARD_X + WIDTH * CELL + 20, BOARD_Y - 10, SIDEBAR - 10, HEIGHT * CELL + 20), border_radius=18)

        preview_cell = max(12, int(self.font.get_height() * 0.9))
        hold_panel_w = max(120, preview_cell * 4 + 28)
        hold_panel_h = max(240, preview_cell * 6 + 90)
        hold_panel_x = max(10, BOARD_X - hold_panel_w - 20)
        hold_panel_y = BOARD_Y - 10
        pygame.draw.rect(self.screen, PANEL, (hold_panel_x, hold_panel_y, hold_panel_w, hold_panel_h), border_radius=18)

        # place the sidebar contents relative to BOARD_Y so the whole group stays centered
        sidebar_top = BOARD_Y + 12
        title_font_size = self.big_font.get_height()
        title_font = pygame.font.Font(FONT_PATH, title_font_size)
        title_surfaces = [title_font.render(line, True, TEXT) for line in self.title_lines()]
        while title_font_size > max(12, int(WINDOW_H * 0.02)):
            widest = max(surface.get_width() for surface in title_surfaces)
            if widest <= SIDEBAR - 24:
                break
            title_font_size -= 1
            title_font = pygame.font.Font(FONT_PATH, title_font_size)
            title_surfaces = [title_font.render(line, True, TEXT) for line in self.title_lines()]
        title_y = sidebar_top
        for surface in title_surfaces:
            self.screen.blit(surface, (sx, title_y))
            title_y += surface.get_height() + 2

        # Stats list (scaled and spaced based on font height)
        line_h = self.font.get_height() + 18
        stats_start = title_y + 18

        def label(text, value, offset_index):
            y = stats_start + offset_index * line_h
            t = self.font.render(text, True, MUTED)
            v = self.font.render(str(value), True, TEXT)
            self.screen.blit(t, (sx, y))
            self.screen.blit(v, (sx, y + self.font.get_height() + 2))

        label("Score", self.score, 0)
        label("Lines", self.lines, 1)
        label("Level", self.level, 2)

        # Debug / Drop rate display
        dbg_text = "DEBUG: ON" if self.debug_mode else "DEBUG: OFF"
        dbg_col = ACCENT if self.debug_mode else MUTED
        dbg_render = self.font.render(dbg_text, True, dbg_col)
        self.screen.blit(dbg_render, (sx, stats_start + 3 * line_h))

        drop_val = int(self.drop_ms)
        d = self.font.render(f"Drop(ms): {drop_val}", True, TEXT)
        self.screen.blit(d, (sx, stats_start + 4 * line_h))

        # Next preview above Hold in the left panel
        left_label_x = hold_panel_x + 12
        next_label_y = hold_panel_y + 14
        nxt = self.font.render("Next", True, MUTED)
        self.screen.blit(nxt, (left_label_x, next_label_y))
        next_box_y = next_label_y + nxt.get_height() + 14
        preview_x = left_label_x + 6
        for cx, cy in self.next_piece.cells:
            rect = pygame.Rect(preview_x + cx * preview_cell, next_box_y + cy * preview_cell, preview_cell, preview_cell)
            pygame.draw.rect(self.screen, self.next_piece.color, rect.inflate(-3, -3), border_radius=6)
            pygame.draw.rect(self.screen, (255, 255, 255), rect.inflate(-3, -3), 1, border_radius=6)

        # Hold preview below Next in the same left panel
        hld = self.font.render("Hold", True, MUTED)
        hold_label_y = next_box_y + preview_cell * 3 + 28
        self.screen.blit(hld, (left_label_x, hold_label_y))
        hold_box_y = hold_label_y + hld.get_height() + 14
        hold_preview_x = left_label_x + 6
        if self.hold_piece is not None:
            for cx, cy in self.hold_piece.cells:
                rect = pygame.Rect(hold_preview_x + cx * preview_cell, hold_box_y + cy * preview_cell, preview_cell, preview_cell)
                pygame.draw.rect(self.screen, self.hold_piece.color, rect.inflate(-3, -3), border_radius=6)
                pygame.draw.rect(self.screen, (255, 255, 255), rect.inflate(-3, -3), 1, border_radius=6)
        else:
            pygame.draw.rect(self.screen, GRID, (hold_preview_x, hold_box_y, preview_cell * 4, preview_cell * 3), 1)

        # Controls at bottom of sidebar (anchor near board bottom)
        controls = [
            "Left/Right: move",
            "Up / X: rotate",
            "Down: soft drop",
            "Space: hard drop",
            "C / LShift: hold",
            "R: restart",
            "Esc: quit",
        ]
        bottom_margin = 20
        controls_start = BOARD_Y + HEIGHT * CELL - bottom_margin - len(controls) * (self.font.get_height() + 10)
        yy = controls_start
        for line in controls:
            txt = self.font.render(line, True, MUTED)
            self.screen.blit(txt, (sx, yy))
            yy += self.font.get_height() + 10

    def draw_game_over(self):
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        title_font = pygame.font.Font(FONT_PATH, max(30, int(WINDOW_H * 0.08)))
        stat_font = pygame.font.Font(FONT_PATH, max(24, int(WINDOW_H * 0.045)))
        hint_font = pygame.font.Font(FONT_PATH, max(18, int(WINDOW_H * 0.03)))

        # Consider a win if either `has_won` was set earlier, or the lines
        # currently meet the mode threshold.
        won_by_lines = bool(self.has_won) or (self.mode_win_lines is not None and self.lines >= self.mode_win_lines)
        headline = "You Win!" if won_by_lines else "Game Over"
        headline_color = ACCENT if won_by_lines else GAME_OVER
        game_over_text = title_font.render(headline, True, headline_color)
        score_text = stat_font.render(f"Score: {self.score}", True, TEXT)
        lines_text = stat_font.render(f"Lines Cleared: {self.lines}", True, TEXT)
        restart_text = hint_font.render("Press R to restart", True, TEXT)
        back_text = hint_font.render("Press B to return to the map", True, TEXT)
        mode_text = hint_font.render("Press T to return and switch game mode", True, TEXT)

        center_x = WINDOW_W // 2
        center_y = WINDOW_H // 2
        self.screen.blit(game_over_text, game_over_text.get_rect(center=(center_x, center_y - 95)))
        self.screen.blit(score_text, score_text.get_rect(center=(center_x, center_y - 20)))
        self.screen.blit(lines_text, lines_text.get_rect(center=(center_x, center_y + 20)))
        self.screen.blit(restart_text, restart_text.get_rect(center=(center_x, center_y + 70)))
        self.screen.blit(back_text, back_text.get_rect(center=(center_x, center_y + 100)))
        self.screen.blit(mode_text, mode_text.get_rect(center=(center_x, center_y + 130)))

    def draw_game_background(self):
        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))
        else:
            self.screen.fill(BG)
        self.draw_board()
        self.draw_sidebar()

    def draw(self):
        self.draw_game_background()
        if self.game_over:
            self.draw_game_over()
        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_b and self.game_over:
                    self.request_return_to_map()
                    return
                if event.key == pygame.K_t and self.game_over:
                    self.return_to_mode_select()
                    return
                if event.key in (pygame.K_UP, pygame.K_x):
                    self.rotate()
                elif event.key == pygame.K_LEFT:
                    self.move(-1)
                    # start hold for left
                    self.hold_dir = -1
                    self.hold_time = 0
                    self.hold_repeat_acc = 0
                elif event.key == pygame.K_RIGHT:
                    self.move(1)
                    # start hold for right
                    self.hold_dir = 1
                    self.hold_time = 0
                    self.hold_repeat_acc = 0
                elif event.key == pygame.K_DOWN:
                    self.soft_drop()
                elif event.key == pygame.K_SPACE:
                    self.hard_drop()
                elif event.key == pygame.K_r:
                    self.restart()
                elif event.key in (pygame.K_c, pygame.K_LSHIFT):
                    # hold / swap piece
                    self.hold_current()
                elif event.key == pygame.K_1:
                    self.debug_mode = not self.debug_mode
                elif event.key == pygame.K_COMMA:
                    self.debug_mode = True
                    self.debug_offset_ms += self.debug_step_ms
                    self.drop_ms = self.compute_drop_ms()
                elif event.key == pygame.K_PERIOD:
                    self.debug_mode = True
                    self.debug_offset_ms -= self.debug_step_ms
                    self.drop_ms = self.compute_drop_ms()
            if event.type == pygame.KEYUP:
                # stop hold when releasing left/right
                if event.key == pygame.K_LEFT and self.hold_dir == -1:
                    self.hold_dir = None
                    self.hold_time = 0
                    self.hold_repeat_acc = 0
                elif event.key == pygame.K_RIGHT and self.hold_dir == 1:
                    self.hold_dir = None
                    self.hold_time = 0
                    self.hold_repeat_acc = 0

        # remove per-frame instantaneous repeats; horizontal hold handled in update(dt)
        keys = pygame.key.get_pressed()
        if not self.game_over:
            # keep single-keydown moves from KEYDOWN events; holding is handled in update()
            pass

    def update(self, dt):
        if self.game_over:
            return
        # `dt` from `clock.tick()` is already milliseconds; don't multiply by 1000.
        self.drop_accumulator += dt
        if self.drop_accumulator >= self.drop_ms:
            self.drop_accumulator = 0
            if not self.soft_drop():
                self.on_ground = True
        if self.on_ground:
            self.lock_timer_ms += dt
            if self.lock_timer_ms >= self.mode_lock_delay_ms:
                self.lock_piece()
        # handle hold-to-repeat for horizontal movement
        if self.hold_dir is not None:
            self.hold_time += dt
            if self.hold_time >= self.hold_delay_ms:
                self.hold_repeat_acc += dt
                while self.hold_repeat_acc >= self.hold_repeat_interval:
                    # repeat move
                    self.move(self.hold_dir)
                    self.hold_repeat_acc -= self.hold_repeat_interval

    def run(self):
        self.show_start_sequence()
        self.start_game_music()
        while not self.return_to_map:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.update(dt)
            self.draw()


def run(screen=None):
    Tetris(screen=screen).run()


def main(screen=None):
    run(screen)


if __name__ == "__main__":
    main()
