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


def draw_scrolling_background(x_offset_px: float) -> None:
    x = -x_offset_px
    while x < SCREEN_WIDTH:
        screen.blit(_bg, (x, 0))
        x += BG_WIDTH


# Main game loop
def main() -> None:
    running = True
    clock = pygame.time.Clock()

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
                    spawn_x = int(player_x) + int(_player_shoot_img.get_width() * LASER_SPAWN_REL_X)
                    spawn_y = (
                        int(player_y)
                        + int(_player_shoot_img.get_height() * LASER_SPAWN_REL_Y)
                        - (LASER_H // 2)
                    )
                    projectiles.append([float(spawn_x), float(spawn_y)])
                    laser_cooldown_t = LASER_COOLDOWN_SEC
                    shoot_pose_t = SHOOT_POSE_SEC

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            player_y -= PLAYER_SPEED_PX_PER_SEC * dt
        if keys[pygame.K_s]:
            player_y += PLAYER_SPEED_PX_PER_SEC * dt
        if keys[pygame.K_a]:
            player_x -= PLAYER_SPEED_PX_PER_SEC * dt
        if keys[pygame.K_d]:
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

        # Remove woods that exited left; penalize if still wood.png (never hit)
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
                wood_rect = pygame.Rect(wx, wy, wood_img.get_width(), wood_img.get_height())
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

        # If unhit wood.png touches Max: -1 mark. If a transformed (hit) wood touches Max: +1 mark.
        # Any wood that touches Max is removed.
        kept_woods_after_hit: list[dict[str, object]] = []
        for w in woods:
            wood_img = w["img"]
            wx = int(float(w["x"]))
            wy = int(float(w["y"]))
            wood_rect = pygame.Rect(wx, wy, wood_img.get_width(), wood_img.get_height())
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

    if round_finished:
        won = marks >= WIN_MARKS_GT
        title = "YOU WIN" if won else "YOU LOSE"
        subtitle = f"Marks: {marks}"

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return

            draw_scrolling_background(bg_offset)

            t_s = END_FONT.render(title, True, (255, 255, 255))
            st_s = HUD_FONT.render(subtitle, True, (255, 255, 255))

            t_rect = t_s.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
            st_rect = st_s.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))

            screen.blit(t_s, t_rect)
            screen.blit(st_s, st_rect)

            pygame.display.flip()
            clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
