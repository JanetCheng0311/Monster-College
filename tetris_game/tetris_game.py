import random
import sys
from dataclasses import dataclass

import pygame

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
MIN_DROP_MS = 10
DEBUG_MIN_MS = 10
PER_LEVEL_DEC = 25

BG = (15, 18, 28)
PANEL = (25, 28, 40)
GRID = (45, 50, 68)
TEXT = (235, 238, 245)
MUTED = (170, 176, 190)
ACCENT = (92, 190, 255)
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
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Tetris")
        # open in fullscreen to match menu (`Monster_College.py` uses fullscreen)
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        # update module-level window size constants to actual screen size
        w, h = self.screen.get_size()
        globals()["WINDOW_W"] = w
        globals()["WINDOW_H"] = h
        # center the board and sidebar within the window
        total_board_w = WIDTH * CELL + SIDEBAR
        total_board_h = HEIGHT * CELL
        new_board_x = max(0, (w - total_board_w) // 2)
        new_board_y = max(0, (h - total_board_h) // 2)
        globals()["BOARD_X"] = new_board_x
        globals()["BOARD_Y"] = new_board_y
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 24, bold=True)
        self.big_font = pygame.font.SysFont("arial", 48, bold=True)
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
            self.game_over = True
        # after spawning a new piece, allow holding again
        self.can_hold = True

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
        for cx, cy in self.current.cells:
            x = self.current.x + cx
            y = self.current.y + cy
            if 0 <= y < HEIGHT:
                self.board[y][x] = self.current.color
        cleared = self.clear_lines()
        if cleared:
            self.lines += cleared
            self.score += [0, 100, 300, 500, 800][cleared] * self.level
            self.level = 1 + self.lines // 10
            self.drop_ms = self.compute_drop_ms()
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
            self.can_hold = False
            self.spawn_piece()
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

    def soft_drop(self):
        if not self.game_over and not self.collides(self.current, 0, 1, self.current.rotation):
            self.current.y += 1
            self.score += 1
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
        self.drop_ms = self.compute_drop_ms()
        self.drop_accumulator = 0
        self.spawn_piece()

    def compute_drop_ms(self):
        base = START_DROP_MS - (self.level - 1) * PER_LEVEL_DEC
        value = base + self.debug_offset_ms
        if self.debug_mode:
            return max(DEBUG_MIN_MS, int(value))
        return max(MIN_DROP_MS, int(value))

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
        title = self.big_font.render("TETRIS", True, TEXT)
        self.screen.blit(title, (sx, 52))

        # Hold preview
        hld = self.font.render("Hold", True, MUTED)
        self.screen.blit(hld, (sx, 100))
        hold_preview_x = sx + 15
        hold_preview_y = 125
        if self.hold_piece is not None:
            for cx, cy in self.hold_piece.cells:
                rect = pygame.Rect(hold_preview_x + cx * 22, hold_preview_y + cy * 22, 22, 22)
                pygame.draw.rect(self.screen, self.hold_piece.color, rect.inflate(-3, -3), border_radius=6)
                pygame.draw.rect(self.screen, (255, 255, 255), rect.inflate(-3, -3), 1, border_radius=6)
        else:
            # draw an empty preview box
            pygame.draw.rect(self.screen, GRID, (hold_preview_x, hold_preview_y, 88, 66), 1)

        def label(text, value, y):
            t = self.font.render(text, True, MUTED)
            v = self.font.render(str(value), True, TEXT)
            self.screen.blit(t, (sx, y))
            self.screen.blit(v, (sx, y + 28))

        label("Score", self.score, 130)
        label("Lines", self.lines, 220)
        label("Level", self.level, 310)

        # Debug / Drop rate display
        dbg_y = 340
        dbg_text = "DEBUG: ON" if self.debug_mode else "DEBUG: OFF"
        dbg_col = ACCENT if self.debug_mode else MUTED
        dbg_render = self.font.render(dbg_text, True, dbg_col)
        self.screen.blit(dbg_render, (sx, dbg_y))

        drop_y = 370
        drop_val = int(self.drop_ms)
        d = self.font.render(f"Drop(ms): {drop_val}", True, TEXT)
        self.screen.blit(d, (sx, drop_y))

        nxt = self.font.render("Next", True, MUTED)
        self.screen.blit(nxt, (sx, 400))
        preview_x = sx + 15
        preview_y = 445
        for cx, cy in self.next_piece.cells:
            rect = pygame.Rect(preview_x + cx * 22, preview_y + cy * 22, 22, 22)
            pygame.draw.rect(self.screen, self.next_piece.color, rect.inflate(-3, -3), border_radius=6)
            pygame.draw.rect(self.screen, (255, 255, 255), rect.inflate(-3, -3), 1, border_radius=6)

        controls = [
            "Left/Right: move",
            "Up / X: rotate",
            "Down: soft drop",
            "Space: hard drop",
            "R: restart",
            "Esc: quit",
        ]
        yy = 560
        for line in controls:
            txt = self.font.render(line, True, MUTED)
            self.screen.blit(txt, (sx, yy))
            yy += 28

    def draw_game_over(self):
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        text = self.big_font.render("Game Over", True, GAME_OVER)
        sub = self.font.render("Press R to restart", True, TEXT)
        self.screen.blit(text, text.get_rect(center=(WINDOW_W // 2, WINDOW_H // 2 - 25)))
        self.screen.blit(sub, sub.get_rect(center=(WINDOW_W // 2, WINDOW_H // 2 + 25)))

    def draw(self):
        self.screen.fill(BG)
        self.draw_board()
        self.draw_sidebar()
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
        while True:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.update(dt)
            self.draw()


def main():
    Tetris().run()


if __name__ == "__main__":
    main()
