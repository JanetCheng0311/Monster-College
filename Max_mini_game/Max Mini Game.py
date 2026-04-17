import os
import random

import pygame

# Initialize Pygame
pygame.init()

# Set up the display in full screen mode
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Max Mini Game")

SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

ASSET_DIR = os.path.join(os.path.dirname(__file__), "Max_assets")
BG_PATH = os.path.join(ASSET_DIR, "Max_minigame_bg.png")

if not os.path.exists(BG_PATH):
    raise FileNotFoundError(
        f"Missing background image: {BG_PATH}. Put Max_minigame_bg.png in the Max_assets folder."
    )

# Load + scale background to fit screen height, then scroll it horizontally.
_bg_raw = pygame.image.load(BG_PATH).convert()
_bg_raw_w, _bg_raw_h = _bg_raw.get_size()
_bg_scale = SCREEN_HEIGHT / _bg_raw_h
_bg = pygame.transform.smoothscale(_bg_raw, (int(_bg_raw_w * _bg_scale), SCREEN_HEIGHT))
BG_WIDTH = _bg.get_width()

SCROLL_SPEED_PX_PER_SEC = 220.0

# Global scale for all sprites except the background.
SPRITE_SCALE = 0.75

PLAYER_IDLE_PATH = os.path.join(ASSET_DIR, "Max_game_ready_pose.png")
PLAYER_SHOOT_PATH = os.path.join(ASSET_DIR, "Max_game_ready_shotpose.png")
LASER_PATH = os.path.join(ASSET_DIR, "Laser_shot.png")
REPLAY_BUTTON_PATH = os.path.join(ASSET_DIR, "replay_button.png")
HOME_BUTTON_PATH = os.path.join(ASSET_DIR, "home_button.png")
WHITEBOARD_PATH = os.path.join(ASSET_DIR, "Whiteboard.png")
START_BUTTON_PATH = os.path.join(ASSET_DIR, "start_button.png")
MAX_FULL_PATH = os.path.join(ASSET_DIR, "Max_full.png")

if not os.path.exists(PLAYER_IDLE_PATH):
    raise FileNotFoundError(
        f"Missing player image: {PLAYER_IDLE_PATH}. Put Max_game_ready_pose.png in the Max_assets folder."
    )
if not os.path.exists(PLAYER_SHOOT_PATH):
    raise FileNotFoundError(
        f"Missing player image: {PLAYER_SHOOT_PATH}. Put Max_game_ready_shotpose.png in the Max_assets folder."
    )
if not os.path.exists(LASER_PATH):
    raise FileNotFoundError(
        f"Missing laser image: {LASER_PATH}. Put Laser_shot.png in the Max_assets folder."
    )
if not os.path.exists(REPLAY_BUTTON_PATH):
    raise FileNotFoundError(
        f"Missing replay button image: {REPLAY_BUTTON_PATH}. Put replay_button.png in the Max_assets folder."
    )
if not os.path.exists(HOME_BUTTON_PATH):
    raise FileNotFoundError(
        f"Missing home button image: {HOME_BUTTON_PATH}. Put home_button.png in the Max_assets folder."
    )
if not os.path.exists(WHITEBOARD_PATH):
    raise FileNotFoundError(
        f"Missing menu image: {WHITEBOARD_PATH}. Put Whiteboard.png in the Max_assets folder."
    )
if not os.path.exists(START_BUTTON_PATH):
    raise FileNotFoundError(
        f"Missing menu image: {START_BUTTON_PATH}. Put start_button.png in the Max_assets folder."
    )
if not os.path.exists(MAX_FULL_PATH):
    raise FileNotFoundError(
        f"Missing menu image: {MAX_FULL_PATH}. Put Max_full.png in the Max_assets folder."
    )

_player_idle_raw = pygame.image.load(PLAYER_IDLE_PATH).convert_alpha()
_player_shoot_raw = pygame.image.load(PLAYER_SHOOT_PATH).convert_alpha()

_player_raw_w, _player_raw_h = _player_idle_raw.get_size()

# Scale player relative to screen height.
_PLAYER_TARGET_H = int(SCREEN_HEIGHT * 0.35 * SPRITE_SCALE)
_player_scale = _PLAYER_TARGET_H / _player_raw_h

_player_idle_img = pygame.transform.smoothscale(
    _player_idle_raw, (int(_player_raw_w * _player_scale), _PLAYER_TARGET_H)
)
_player_shoot_img = pygame.transform.smoothscale(
    _player_shoot_raw,
    (int(_player_shoot_raw.get_width() * _player_scale), _PLAYER_TARGET_H),
)

PLAYER_W, PLAYER_H = _player_idle_img.get_size()
PLAYER_X = 40
PLAYER_SPEED_PX_PER_SEC = 520.0

_laser_raw = pygame.image.load(LASER_PATH).convert_alpha()
_laser_img = pygame.transform.smoothscale(
    _laser_raw,
    (
        max(1, int(_laser_raw.get_width() * _player_scale * 0.5)),
        max(1, int(_laser_raw.get_height() * _player_scale * 0.5)),
    ),
)
LASER_W, LASER_H = _laser_img.get_size()
LASER_SPEED_PX_PER_SEC = 1400.0
LASER_COOLDOWN_SEC = 0.5
SHOOT_POSE_SEC = 0.15

LASER_SPAWN_REL_X = 0.78
LASER_SPAWN_REL_Y = 0.40

WOOD_PATH = os.path.join(ASSET_DIR, "wood.png")
WOOD_STAR_PATH = os.path.join(ASSET_DIR, "star_wood.png")
WOOD_MOON_PATH = os.path.join(ASSET_DIR, "moon_wood.png")
WOOD_AROUND_PATH = os.path.join(ASSET_DIR, "around_wood.png")

for _p in (WOOD_PATH, WOOD_STAR_PATH, WOOD_MOON_PATH, WOOD_AROUND_PATH):
    if not os.path.exists(_p):
        raise FileNotFoundError(f"Missing wood image: {_p}.")

_wood_raw = pygame.image.load(WOOD_PATH).convert_alpha()
_wood_star_raw = pygame.image.load(WOOD_STAR_PATH).convert_alpha()
_wood_moon_raw = pygame.image.load(WOOD_MOON_PATH).convert_alpha()
_wood_around_raw = pygame.image.load(WOOD_AROUND_PATH).convert_alpha()

WOOD_TARGET_H = int(SCREEN_HEIGHT * 0.12 * SPRITE_SCALE)

_wood_scale = WOOD_TARGET_H / _wood_raw.get_height()
_wood_img = pygame.transform.smoothscale(
    _wood_raw, (int(_wood_raw.get_width() * _wood_scale), WOOD_TARGET_H)
)

_wood_star_scale = WOOD_TARGET_H / _wood_star_raw.get_height()
_wood_star_img = pygame.transform.smoothscale(
    _wood_star_raw, (int(_wood_star_raw.get_width() * _wood_star_scale), WOOD_TARGET_H)
)

_wood_moon_scale = WOOD_TARGET_H / _wood_moon_raw.get_height()
_wood_moon_img = pygame.transform.smoothscale(
    _wood_moon_raw, (int(_wood_moon_raw.get_width() * _wood_moon_scale), WOOD_TARGET_H)
)

_wood_around_scale = WOOD_TARGET_H / _wood_around_raw.get_height()
_wood_around_img = pygame.transform.smoothscale(
    _wood_around_raw, (int(_wood_around_raw.get_width() * _wood_around_scale), WOOD_TARGET_H)
)

WOOD_MIN_SPEED_PX_PER_SEC = 420.0
WOOD_MAX_SPEED_PX_PER_SEC = 720.0
WOOD_MAX_VY_PX_PER_SEC = 320.0
WOOD_SPAWN_EVERY_SEC = 0.85

WOOD_VARIANT_KEYS = ("star", "moon", "around")
WOOD_VARIANTS = {
    "star": _wood_star_img,
    "moon": _wood_moon_img,
    "around": _wood_around_img,
}

ROUND_DURATION_SEC = 60.0
WIN_MARKS_GT = 30

HUD_FONT = pygame.font.SysFont(None, 42)
END_FONT = pygame.font.SysFont(None, 96)


def _scale_to_height(img: pygame.Surface, target_h: int) -> pygame.Surface:
    target_h = max(1, int(target_h))
    w, h = img.get_size()
    if h <= 0:
        return img
    scale = target_h / h
    return pygame.transform.smoothscale(img, (max(1, int(w * scale)), target_h))


def _scale_to_fit(img: pygame.Surface, max_w: int, max_h: int) -> pygame.Surface:
    max_w = max(1, int(max_w))
    max_h = max(1, int(max_h))
    w, h = img.get_size()
    if w <= 0 or h <= 0:
        return img
    scale = min(max_w / w, max_h / h)
    return pygame.transform.smoothscale(img, (max(1, int(w * scale)), max(1, int(h * scale))))


def _wrap_text_lines(text: str, font: pygame.font.Font, max_width_px: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = words[0]

    for w in words[1:]:
        test = f"{current} {w}"
        if font.size(test)[0] <= max_width_px:
            current = test
        else:
            lines.append(current)
            current = w
    lines.append(current)
    return lines


_replay_btn_raw = pygame.image.load(REPLAY_BUTTON_PATH).convert_alpha()
REPLAY_BTN_TARGET_H = int(SCREEN_HEIGHT * 0.15 * SPRITE_SCALE)
_replay_btn_img = _scale_to_height(_replay_btn_raw, REPLAY_BTN_TARGET_H)

_home_btn_raw = pygame.image.load(HOME_BUTTON_PATH).convert_alpha()
_home_btn_img = _scale_to_height(_home_btn_raw, REPLAY_BTN_TARGET_H)

_whiteboard_raw = pygame.image.load(WHITEBOARD_PATH).convert_alpha()
_start_btn_raw = pygame.image.load(START_BUTTON_PATH).convert_alpha()
_max_full_raw = pygame.image.load(MAX_FULL_PATH).convert_alpha()

_whiteboard_img = _scale_to_fit(
    _whiteboard_raw,
    int(SCREEN_WIDTH * 1.0),
    int(SCREEN_HEIGHT * 0.9),
)

_max_full_img = _scale_to_height(_max_full_raw, int(_whiteboard_img.get_height() * 0.55))
_start_btn_img = _scale_to_height(_start_btn_raw, int(_max_full_img.get_height() * 0.30))


def draw_scrolling_background(x_offset_px: float) -> None:
    x = -x_offset_px
    while x < SCREEN_WIDTH:
        screen.blit(_bg, (x, 0))
        x += BG_WIDTH


def show_menu(clock: pygame.time.Clock) -> bool:
    pygame.mouse.set_visible(True)

    whiteboard_rect = _whiteboard_img.get_rect()
    max_full_rect = _max_full_img.get_rect()
    start_btn_rect = _start_btn_img.get_rect()

    gap = max(12, int(SCREEN_HEIGHT * 0.02))

    center_x = (SCREEN_WIDTH // 2) - int(SCREEN_WIDTH * 0.12)
    center_y = (SCREEN_HEIGHT // 2) + int(SCREEN_HEIGHT * 0.01)
    whiteboard_rect.center = (center_x, center_y)

    if whiteboard_rect.top < 10:
        whiteboard_rect.top = 10
    if whiteboard_rect.bottom > SCREEN_HEIGHT - 10:
        whiteboard_rect.bottom = SCREEN_HEIGHT - 10

    # Place Max_full.png next to the whiteboard.
    side_gap = max(12, int(SCREEN_WIDTH * 0.02))
    max_full_up = max(6, int(SCREEN_HEIGHT * 0.05))
    max_full_rect.midleft = (
        whiteboard_rect.right + side_gap,
        whiteboard_rect.centery - max_full_up,
    )

    if max_full_rect.top < 10:
        max_full_rect.top = 10
    if max_full_rect.bottom > SCREEN_HEIGHT - 10:
        max_full_rect.bottom = SCREEN_HEIGHT - 10

    # Place start button below Max_full.png.
    start_gap = max(10, int(SCREEN_HEIGHT * 0.015))
    start_btn_rect.midtop = (max_full_rect.centerx, max_full_rect.bottom + start_gap)

    if start_btn_rect.left < 10:
        start_btn_rect.left = 10
    if start_btn_rect.right > SCREEN_WIDTH - 10:
        start_btn_rect.right = SCREEN_WIDTH - 10
    if start_btn_rect.bottom > SCREEN_HEIGHT - 10:
        start_btn_rect.bottom = SCREEN_HEIGHT - 10

    # Prepare instruction text to draw on the whiteboard.
    content_pad_x = max(14, int(whiteboard_rect.width * 0.08))
    content_pad_y = max(14, int(whiteboard_rect.height * 0.10))
    content_rect = pygame.Rect(
        whiteboard_rect.left + content_pad_x,
        whiteboard_rect.top + content_pad_y,
        max(1, whiteboard_rect.width - (2 * content_pad_x)),
        max(1, whiteboard_rect.height - (2 * content_pad_y)),
    )

    # Nudge instructions slightly down + right.
    instruction_offset_x = int(whiteboard_rect.width * 0.04)
    instruction_offset_y = int(whiteboard_rect.height * 0.05)
    content_rect.x += instruction_offset_x
    content_rect.y += instruction_offset_y

    content_rect.clamp_ip(
        pygame.Rect(
            whiteboard_rect.left + 6,
            whiteboard_rect.top + 6,
            max(1, whiteboard_rect.width - 12),
            max(1, whiteboard_rect.height - 12),
        )
    )

    instruction_title = "Mini Game Instructions"
    instruction_blocks = [
        "Move: WASD or Arrow Keys",
        "Shoot: SPACE",
        f"Time Limit: {int(ROUND_DURATION_SEC)} seconds",
        f"Win: Reach {WIN_MARKS_GT}+ marks",
        "Tip: Hitting wood once changes it (and gives +1)",
        "Touching hit wood gives +1; unhit wood gives -1",
        "Click START to begin  |  ESC to quit",
    ]

    # Auto-size fonts to fit the available whiteboard space.
    body_size = max(16, int(whiteboard_rect.height * 0.052))
    title_scale = 1.35
    line_gap = max(2, int(whiteboard_rect.height * 0.008))
    title_gap = max(6, int(whiteboard_rect.height * 0.02))

    while True:
        title_size = max(18, int(body_size * title_scale))
        title_font = pygame.font.SysFont(None, title_size)
        body_font = pygame.font.SysFont(None, body_size)

        wrapped_lines: list[tuple[pygame.Surface, pygame.Rect]] = []

        title_surf = title_font.render(instruction_title, True, (10, 10, 10))
        title_rect = title_surf.get_rect()
        title_rect.midtop = (content_rect.centerx, content_rect.top)

        body_extra_down = max(0, int(whiteboard_rect.height * 0.10))
        body_extra_right = max(0, int(whiteboard_rect.width * 0.03))
        body_max_width = max(1, content_rect.width - body_extra_right)

        y = title_rect.bottom + title_gap + body_extra_down
        for block in instruction_blocks:
            for line in _wrap_text_lines(block, body_font, body_max_width):
                surf = body_font.render(line, True, (10, 10, 10))
                rect = surf.get_rect()
                rect.topleft = (content_rect.left + body_extra_right, y)
                wrapped_lines.append((surf, rect))
                y = rect.bottom + line_gap
            y += line_gap

        total_h = (y - content_rect.top)
        if total_h <= content_rect.height or body_size <= 14:
            instruction_title_surf = title_surf
            instruction_title_rect = title_rect
            instruction_line_surfs = wrapped_lines
            break

        body_size -= 1

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                pygame.mouse.set_visible(False)
                return True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_btn_rect.collidepoint(event.pos) or whiteboard_rect.collidepoint(event.pos):
                    pygame.mouse.set_visible(False)
                    return True

        draw_scrolling_background(0.0)
        screen.blit(_whiteboard_img, whiteboard_rect)
        screen.blit(instruction_title_surf, instruction_title_rect)
        for surf, rect in instruction_line_surfs:
            screen.blit(surf, rect)
        screen.blit(_max_full_img, max_full_rect)
        screen.blit(_start_btn_img, start_btn_rect)
        pygame.display.flip()
        clock.tick(60)


# Main game loop
def main() -> None:
    running = True
    clock = pygame.time.Clock()

    if not show_menu(clock):
        pygame.quit()
        return

    while running:
        pygame.mouse.set_visible(False)

        bg_offset = 0.0
        player_x = float(PLAYER_X)
        player_y = (SCREEN_HEIGHT - PLAYER_H) / 2

        marks = 0
        elapsed = 0.0
        round_finished = False

        shoot_pose_t = 0.0
        laser_cooldown_t = 0.0
        projectiles: list[list[float]] = []

        woods: list[dict[str, object]] = []
        wood_spawn_t = 0.0

        while running:
            dt = clock.tick(60) / 1000.0
            elapsed += dt
            remaining = max(0.0, ROUND_DURATION_SEC - elapsed)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    if laser_cooldown_t <= 0.0:
                        spawn_x = int(player_x) + int(
                            _player_shoot_img.get_width() * LASER_SPAWN_REL_X
                        )
                        spawn_y = (
                            int(player_y)
                            + int(_player_shoot_img.get_height() * LASER_SPAWN_REL_Y)
                            - (LASER_H // 2)
                        )
                        projectiles.append([float(spawn_x), float(spawn_y)])
                        laser_cooldown_t = LASER_COOLDOWN_SEC
                        shoot_pose_t = SHOOT_POSE_SEC

            if not running:
                break

            keys = pygame.key.get_pressed()
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                player_y -= PLAYER_SPEED_PX_PER_SEC * dt
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                player_y += PLAYER_SPEED_PX_PER_SEC * dt
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                player_x -= PLAYER_SPEED_PX_PER_SEC * dt
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                player_x += PLAYER_SPEED_PX_PER_SEC * dt

            player_w_max = max(_player_idle_img.get_width(), _player_shoot_img.get_width())
            player_x = max(0.0, min(float(SCREEN_WIDTH - player_w_max), player_x))
            player_y = max(0.0, min(float(SCREEN_HEIGHT - PLAYER_H), player_y))

            if shoot_pose_t > 0.0:
                shoot_pose_t = max(0.0, shoot_pose_t - dt)
            if laser_cooldown_t > 0.0:
                laser_cooldown_t = max(0.0, laser_cooldown_t - dt)

            # Spawn wood
            wood_spawn_t -= dt
            if wood_spawn_t <= 0.0:
                wood_spawn_t = WOOD_SPAWN_EVERY_SEC
                wx = float(SCREEN_WIDTH + 20)
                wy = float(random.randint(0, max(0, SCREEN_HEIGHT - _wood_img.get_height())))
                vx = -random.uniform(WOOD_MIN_SPEED_PX_PER_SEC, WOOD_MAX_SPEED_PX_PER_SEC)
                vy = random.uniform(-WOOD_MAX_VY_PX_PER_SEC, WOOD_MAX_VY_PX_PER_SEC)
                woods.append(
                    {
                        "x": wx,
                        "y": wy,
                        "vx": vx,
                        "vy": vy,
                        "img": _wood_img,
                        "hit": False,
                        "variant": "base",
                    }
                )

            # Move lasers
            for p in projectiles:
                p[0] += LASER_SPEED_PX_PER_SEC * dt
            projectiles = [p for p in projectiles if p[0] < SCREEN_WIDTH + LASER_W]

            # Move woods (random vertical movement + bounce)
            for w in woods:
                w["x"] = float(w["x"]) + float(w["vx"]) * dt
                w["y"] = float(w["y"]) + float(w["vy"]) * dt

                wood_img = w["img"]
                h = wood_img.get_height()
                if float(w["y"]) < 0.0:
                    w["y"] = 0.0
                    w["vy"] = abs(float(w["vy"]))
                elif float(w["y"]) + h > SCREEN_HEIGHT:
                    w["y"] = float(SCREEN_HEIGHT - h)
                    w["vy"] = -abs(float(w["vy"]))

            # Remove woods that exited left; penalize if never hit
            kept_woods: list[dict[str, object]] = []
            for w in woods:
                if float(w["x"]) > -float(w["img"].get_width()):
                    kept_woods.append(w)
                else:
                    if not bool(w["hit"]):
                        marks -= 1
            woods = kept_woods

            # Laser hits wood => change wood sprite randomly (+1 mark for first hit)
            remaining_projectiles: list[list[float]] = []
            for px, py in projectiles:
                laser_rect = pygame.Rect(int(px), int(py), LASER_W, LASER_H)
                hit_any = False
                for w in woods:
                    wood_img = w["img"]
                    wx = int(float(w["x"]))
                    wy = int(float(w["y"]))
                    wood_rect = pygame.Rect(
                        wx, wy, wood_img.get_width(), wood_img.get_height()
                    )
                    if laser_rect.colliderect(wood_rect):
                        hit_any = True
                        if not bool(w["hit"]):
                            marks += 1
                            cx, cy = wood_rect.center
                            new_kind = random.choice(WOOD_VARIANT_KEYS)
                            new_img = WOOD_VARIANTS[new_kind]
                            w["img"] = new_img
                            w["hit"] = True
                            w["variant"] = new_kind
                            w["x"] = float(cx - (new_img.get_width() // 2))
                            w["y"] = float(cy - (new_img.get_height() // 2))
                        break
                if not hit_any:
                    remaining_projectiles.append([px, py])
            projectiles = remaining_projectiles

            player_img = _player_shoot_img if shoot_pose_t > 0.0 else _player_idle_img
            player_rect = pygame.Rect(
                int(player_x),
                int(player_y),
                player_img.get_width(),
                player_img.get_height(),
            )

            # If unhit wood touches Max: -1 mark. If hit wood touches Max: +1 mark.
            # Any wood that touches Max is removed.
            kept_woods_after_hit: list[dict[str, object]] = []
            for w in woods:
                wood_img = w["img"]
                wx = int(float(w["x"]))
                wy = int(float(w["y"]))
                wood_rect = pygame.Rect(
                    wx, wy, wood_img.get_width(), wood_img.get_height()
                )
                if player_rect.colliderect(wood_rect):
                    if bool(w["hit"]):
                        marks += 1
                    else:
                        marks -= 1
                    continue
                kept_woods_after_hit.append(w)
            woods = kept_woods_after_hit

            bg_offset = (bg_offset + SCROLL_SPEED_PX_PER_SEC * dt) % BG_WIDTH
            draw_scrolling_background(bg_offset)

            screen.blit(player_img, (int(player_x), int(player_y)))
            for w in woods:
                screen.blit(w["img"], (int(float(w["x"])), int(float(w["y"]))))
            for px, py in projectiles:
                screen.blit(_laser_img, (int(px), int(py)))

            # HUD
            marks_s = HUD_FONT.render(
                f"Marks: {marks}/{WIN_MARKS_GT}", True, (255, 255, 255)
            )
            time_s = HUD_FONT.render(f"Time: {int(remaining)}", True, (255, 255, 255))
            screen.blit(marks_s, (20, 20))
            screen.blit(time_s, (20, 60))

            pygame.display.flip()

            if remaining <= 0.0:
                round_finished = True
                break

        if not running:
            break

        if not round_finished:
            break

        won = marks >= WIN_MARKS_GT
        title = "YOU WIN" if won else "YOU LOSE"
        subtitle = f"Marks: {marks}"

        t_s = END_FONT.render(title, True, (255, 255, 255))
        st_s = HUD_FONT.render(subtitle, True, (255, 255, 255))

        t_rect = t_s.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
        st_rect = st_s.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))

        replay_btn_rect = _replay_btn_img.get_rect(
            center=(
                SCREEN_WIDTH // 2,
                min(
                    SCREEN_HEIGHT - (_replay_btn_img.get_height() // 2) - 20,
                    st_rect.bottom + (_replay_btn_img.get_height() // 2) + 20,
                ),
            )
        )

        home_btn_rect = _home_btn_img.get_rect(
            center=(
                SCREEN_WIDTH // 2,
                min(
                    SCREEN_HEIGHT - (_home_btn_img.get_height() // 2) - 20,
                    replay_btn_rect.bottom + (_home_btn_img.get_height() // 2) + 14,
                ),
            )
        )

        pygame.mouse.set_visible(True)
        replay_requested = False
        home_requested = False

        while running and (not replay_requested) and (not home_requested):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if replay_btn_rect.collidepoint(event.pos):
                        replay_requested = True
                    elif home_btn_rect.collidepoint(event.pos):
                        home_requested = True

            draw_scrolling_background(bg_offset)

            screen.blit(t_s, t_rect)
            screen.blit(st_s, st_rect)
            screen.blit(_replay_btn_img, replay_btn_rect)
            screen.blit(_home_btn_img, home_btn_rect)

            pygame.display.flip()
            clock.tick(60)

        if not running:
            break
        if replay_requested:
            continue
        if home_requested:
            running = False
            break
        break

    pygame.quit()


if __name__ == "__main__":
    main()
