"""Max Mini Game.

This module can run standalone, or be launched from the main game without
tearing down the existing Pygame window.

Key behavior when embedded:
- Uses the provided `screen` surface (no `pygame.display.set_mode`).
- ESC returns control to the caller (does not quit the whole app).
"""

from __future__ import annotations

import os
import random

import pygame


def run(screen: pygame.Surface | None = None) -> None:
    """Run the mini game.

    If `screen` is provided, the mini game draws into that surface and returns
    to the caller on ESC/Home/Quit events, without calling `pygame.quit()`.
    """

    pygame.init()

    created_display = False
    if screen is None:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Max Mini Game")
        created_display = True

    screen_width, screen_height = screen.get_size()

    def exit_whole_program() -> None:
        # ESC should exit the whole program (both main and mini game).
        try:
            pygame.quit()
        except Exception:
            pass
        raise SystemExit(0)

    asset_dir = os.path.join(os.path.dirname(__file__), "Max_assets")
    bg_path = os.path.join(asset_dir, "Max_minigame_bg.png")

    if not os.path.exists(bg_path):
        raise FileNotFoundError(
            f"Missing background image: {bg_path}. Put Max_minigame_bg.png in the Max_assets folder."
        )

    # Load + scale background to fit screen height, then scroll it horizontally.
    bg_raw = pygame.image.load(bg_path).convert()
    bg_raw_w, bg_raw_h = bg_raw.get_size()
    bg_scale = screen_height / bg_raw_h
    bg = pygame.transform.smoothscale(bg_raw, (int(bg_raw_w * bg_scale), screen_height))
    bg_width = bg.get_width()

    scroll_speed_px_per_sec = 220.0
    sprite_scale = 0.75

    player_idle_path = os.path.join(asset_dir, "Max_game_ready_pose.png")
    player_shoot_path = os.path.join(asset_dir, "Max_game_ready_shotpose.png")
    laser_path = os.path.join(asset_dir, "Laser_shot.png")
    laser_sound_path = os.path.join(asset_dir, "laser_gun.wav")
    collect_sound_path = os.path.join(asset_dir, "Collect_wood.wav")
    got_hit_sound_path = os.path.join(asset_dir, "Got_hit.wav")
    replay_button_path = os.path.join(asset_dir, "replay_button.png")
    home_button_path = os.path.join(asset_dir, "home_button.png")
    whiteboard_path = os.path.join(asset_dir, "Whiteboard.png")
    start_button_path = os.path.join(asset_dir, "start_button.png")
    max_full_path = os.path.join(asset_dir, "Max_full.png")

    for p, msg in (
        (player_idle_path, "Missing player image"),
        (player_shoot_path, "Missing player image"),
        (laser_path, "Missing laser image"),
        (replay_button_path, "Missing replay button image"),
        (home_button_path, "Missing home button image"),
        (whiteboard_path, "Missing menu image"),
        (start_button_path, "Missing menu image"),
        (max_full_path, "Missing menu image"),
    ):
        if not os.path.exists(p):
            raise FileNotFoundError(f"{msg}: {p}.")

    player_idle_raw = pygame.image.load(player_idle_path).convert_alpha()
    player_shoot_raw = pygame.image.load(player_shoot_path).convert_alpha()

    player_raw_w, player_raw_h = player_idle_raw.get_size()

    # Scale player relative to screen height.
    player_target_h = int(screen_height * 0.35 * sprite_scale)
    player_scale = player_target_h / player_raw_h

    player_idle_img = pygame.transform.smoothscale(
        player_idle_raw, (int(player_raw_w * player_scale), player_target_h)
    )
    player_shoot_img = pygame.transform.smoothscale(
        player_shoot_raw,
        (int(player_shoot_raw.get_width() * player_scale), player_target_h),
    )

    player_w, player_h = player_idle_img.get_size()
    player_x0 = 40
    player_speed_px_per_sec = 520.0

    laser_raw = pygame.image.load(laser_path).convert_alpha()
    laser_img = pygame.transform.smoothscale(
        laser_raw,
        (
            max(1, int(laser_raw.get_width() * player_scale * 0.5)),
            max(1, int(laser_raw.get_height() * player_scale * 0.5)),
        ),
    )
    laser_w, laser_h = laser_img.get_size()
    laser_speed_px_per_sec = 1400.0
    laser_cooldown_sec = 0.5
    shoot_pose_sec = 0.15
    laser_spawn_rel_x = 0.78
    laser_spawn_rel_y = 0.40

    # Initialize mixer (if not already) and load sounds (optional).
    try:
        if pygame.mixer.get_init() is None:
            pygame.mixer.init()
    except Exception:
        pass

    laser_sound = None
    if os.path.exists(laser_sound_path) and pygame.mixer.get_init() is not None:
        try:
            laser_sound = pygame.mixer.Sound(laser_sound_path)
        except Exception:
            laser_sound = None

    collect_sound = None
    if os.path.exists(collect_sound_path) and pygame.mixer.get_init() is not None:
        try:
            collect_sound = pygame.mixer.Sound(collect_sound_path)
        except Exception:
            collect_sound = None

    got_hit_sound = None
    if os.path.exists(got_hit_sound_path) and pygame.mixer.get_init() is not None:
        try:
            got_hit_sound = pygame.mixer.Sound(got_hit_sound_path)
        except Exception:
            got_hit_sound = None

    wood_path = os.path.join(asset_dir, "wood.png")
    wood_star_path = os.path.join(asset_dir, "star_wood.png")
    wood_moon_path = os.path.join(asset_dir, "moon_wood.png")
    wood_around_path = os.path.join(asset_dir, "around_wood.png")
    for p in (wood_path, wood_star_path, wood_moon_path, wood_around_path):
        if not os.path.exists(p):
            raise FileNotFoundError(f"Missing wood image: {p}.")

    wood_raw = pygame.image.load(wood_path).convert_alpha()
    wood_star_raw = pygame.image.load(wood_star_path).convert_alpha()
    wood_moon_raw = pygame.image.load(wood_moon_path).convert_alpha()
    wood_around_raw = pygame.image.load(wood_around_path).convert_alpha()

    wood_target_h = int(screen_height * 0.12 * sprite_scale)

    wood_scale = wood_target_h / wood_raw.get_height()
    wood_img = pygame.transform.smoothscale(
        wood_raw, (int(wood_raw.get_width() * wood_scale), wood_target_h)
    )
    wood_star_scale = wood_target_h / wood_star_raw.get_height()
    wood_star_img = pygame.transform.smoothscale(
        wood_star_raw, (int(wood_star_raw.get_width() * wood_star_scale), wood_target_h)
    )
    wood_moon_scale = wood_target_h / wood_moon_raw.get_height()
    wood_moon_img = pygame.transform.smoothscale(
        wood_moon_raw, (int(wood_moon_raw.get_width() * wood_moon_scale), wood_target_h)
    )
    wood_around_scale = wood_target_h / wood_around_raw.get_height()
    wood_around_img = pygame.transform.smoothscale(
        wood_around_raw,
        (int(wood_around_raw.get_width() * wood_around_scale), wood_target_h),
    )

    wood_min_speed_px_per_sec = 420.0
    wood_max_speed_px_per_sec = 720.0
    wood_max_vy_px_per_sec = 320.0
    wood_spawn_every_sec = 0.85

    wood_variant_keys = ("star", "moon", "around")
    wood_variants = {
        "star": wood_star_img,
        "moon": wood_moon_img,
        "around": wood_around_img,
    }

    round_duration_sec = 60.0
    win_marks_gt = 30

    hud_font = pygame.font.Font(None, 42)
    end_font = pygame.font.Font(None, 96)

    def scale_to_height(img: pygame.Surface, target_h: int) -> pygame.Surface:
        target_h = max(1, int(target_h))
        w, h = img.get_size()
        if h <= 0:
            return img
        s = target_h / h
        return pygame.transform.smoothscale(img, (max(1, int(w * s)), target_h))

    def scale_to_fit(img: pygame.Surface, max_w: int, max_h: int) -> pygame.Surface:
        max_w = max(1, int(max_w))
        max_h = max(1, int(max_h))
        w, h = img.get_size()
        if w <= 0 or h <= 0:
            return img
        s = min(max_w / w, max_h / h)
        return pygame.transform.smoothscale(
            img,
            (max(1, int(w * s)), max(1, int(h * s))),
        )

    def wrap_text_lines(text: str, font: pygame.font.Font, max_width_px: int) -> list[str]:
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

    replay_btn_raw = pygame.image.load(replay_button_path).convert_alpha()
    replay_btn_target_h = int(screen_height * 0.15 * sprite_scale)
    replay_btn_img = scale_to_height(replay_btn_raw, replay_btn_target_h)

    home_btn_raw = pygame.image.load(home_button_path).convert_alpha()
    home_btn_img = scale_to_height(home_btn_raw, replay_btn_target_h)

    whiteboard_raw = pygame.image.load(whiteboard_path).convert_alpha()
    start_btn_raw = pygame.image.load(start_button_path).convert_alpha()
    max_full_raw = pygame.image.load(max_full_path).convert_alpha()

    invitation_path = os.path.join(asset_dir, "invitation.png")

    whiteboard_img = scale_to_fit(
        whiteboard_raw,
        int(screen_width * 1.0),
        int(screen_height * 0.9),
    )

    max_full_img = scale_to_height(max_full_raw, int(whiteboard_img.get_height() * 0.55))
    start_btn_img = scale_to_height(start_btn_raw, int(max_full_img.get_height() * 0.30))
    invitation_img = None
    if os.path.exists(invitation_path):
        try:
            inv_raw = pygame.image.load(invitation_path).convert_alpha()
            # Make invitation a bit smaller so it doesn't dominate the screen
            # Make invitation larger and slightly higher on screen
            invitation_img = scale_to_fit(
                inv_raw, int(screen_width * 0.65), int(screen_height * 0.65)
            )
        except Exception:
            invitation_img = None
    def draw_scrolling_background(x_offset_px: float) -> None:
        x = -x_offset_px
        while x < screen_width:
            screen.blit(bg, (x, 0))
            x += bg_width

    def show_menu(clock: pygame.time.Clock) -> bool:
        pygame.mouse.set_visible(True)

        whiteboard_rect = whiteboard_img.get_rect()
        max_full_rect = max_full_img.get_rect()
        start_btn_rect = start_btn_img.get_rect()

        center_x = (screen_width // 2) - int(screen_width * 0.12)
        center_y = (screen_height // 2) + int(screen_height * 0.01)
        whiteboard_rect.center = (center_x, center_y)

        if whiteboard_rect.top < 10:
            whiteboard_rect.top = 10
        if whiteboard_rect.bottom > screen_height - 10:
            whiteboard_rect.bottom = screen_height - 10

        # Place Max_full.png next to the whiteboard.
        side_gap = max(12, int(screen_width * 0.02))
        max_full_up = max(6, int(screen_height * 0.05))
        max_full_rect.midleft = (
            whiteboard_rect.right + side_gap,
            whiteboard_rect.centery - max_full_up,
        )

        if max_full_rect.top < 10:
            max_full_rect.top = 10
        if max_full_rect.bottom > screen_height - 10:
            max_full_rect.bottom = screen_height - 10

        # Place start button below Max_full.png.
        start_gap = max(10, int(screen_height * 0.015))
        start_btn_rect.midtop = (max_full_rect.centerx, max_full_rect.bottom + start_gap)

        if start_btn_rect.left < 10:
            start_btn_rect.left = 10
        if start_btn_rect.right > screen_width - 10:
            start_btn_rect.right = screen_width - 10
        if start_btn_rect.bottom > screen_height - 10:
            start_btn_rect.bottom = screen_height - 10

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
            f"Time Limit: {int(round_duration_sec)} seconds",
            f"Win: Reach {win_marks_gt}+ marks",
            "Tip: Hitting wood once changes it (and gives +1)",
            "Touching hit wood gives +1; unhit wood gives -1",
            "Click START to begin  |  ESC to return",
        ]

        # Auto-size fonts to fit the available whiteboard space.
        body_size = max(16, int(whiteboard_rect.height * 0.052))
        title_scale = 1.35
        line_gap = max(2, int(whiteboard_rect.height * 0.008))
        title_gap = max(6, int(whiteboard_rect.height * 0.02))

        while True:
            title_size = max(18, int(body_size * title_scale))
            title_font = pygame.font.Font(None, title_size)
            body_font = pygame.font.Font(None, body_size)

            wrapped_lines: list[tuple[pygame.Surface, pygame.Rect]] = []

            title_surf = title_font.render(instruction_title, True, (10, 10, 10))
            title_rect = title_surf.get_rect()
            title_rect.midtop = (content_rect.centerx, content_rect.top)

            body_extra_down = max(0, int(whiteboard_rect.height * 0.10))
            body_extra_right = max(0, int(whiteboard_rect.width * 0.03))
            body_max_width = max(1, content_rect.width - body_extra_right)

            y = title_rect.bottom + title_gap + body_extra_down
            for block in instruction_blocks:
                for line in wrap_text_lines(block, body_font, body_max_width):
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
                    exit_whole_program()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    exit_whole_program()
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    pygame.mouse.set_visible(False)
                    return True
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if start_btn_rect.collidepoint(event.pos) or whiteboard_rect.collidepoint(event.pos):
                        pygame.mouse.set_visible(False)
                        return True

            draw_scrolling_background(0.0)
            screen.blit(whiteboard_img, whiteboard_rect)
            screen.blit(instruction_title_surf, instruction_title_rect)
            for surf, rect in instruction_line_surfs:
                screen.blit(surf, rect)
            screen.blit(max_full_img, max_full_rect)
            screen.blit(start_btn_img, start_btn_rect)
            pygame.display.flip()
            clock.tick(60)

    # --- Main mini-game loop ---
    running = True
    clock = pygame.time.Clock()

    if not show_menu(clock):
        if created_display:
            pygame.quit()
        return

    try:
        while running:
            pygame.mouse.set_visible(False)

            bg_offset = 0.0
            player_x = float(player_x0)
            player_y = (screen_height - player_h) / 2

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
                remaining = max(0.0, round_duration_sec - elapsed)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        exit_whole_program()
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        exit_whole_program()
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        if laser_cooldown_t <= 0.0:
                            spawn_x = int(player_x) + int(player_shoot_img.get_width() * laser_spawn_rel_x)
                            spawn_y = (
                                int(player_y)
                                + int(player_shoot_img.get_height() * laser_spawn_rel_y)
                                - (laser_h // 2)
                            )
                            projectiles.append([float(spawn_x), float(spawn_y)])
                            laser_cooldown_t = laser_cooldown_sec
                            shoot_pose_t = shoot_pose_sec
                            try:
                                if laser_sound is not None:
                                    laser_sound.play()
                            except Exception:
                                pass

                if not running:
                    break

                keys = pygame.key.get_pressed()
                if keys[pygame.K_w] or keys[pygame.K_UP]:
                    player_y -= player_speed_px_per_sec * dt
                if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                    player_y += player_speed_px_per_sec * dt
                if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                    player_x -= player_speed_px_per_sec * dt
                if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                    player_x += player_speed_px_per_sec * dt

                player_w_max = max(player_idle_img.get_width(), player_shoot_img.get_width())
                player_x = max(0.0, min(float(screen_width - player_w_max), player_x))
                player_y = max(0.0, min(float(screen_height - player_h), player_y))

                if shoot_pose_t > 0.0:
                    shoot_pose_t = max(0.0, shoot_pose_t - dt)
                if laser_cooldown_t > 0.0:
                    laser_cooldown_t = max(0.0, laser_cooldown_t - dt)

                # Spawn wood
                wood_spawn_t -= dt
                if wood_spawn_t <= 0.0:
                    wood_spawn_t = wood_spawn_every_sec
                    wx = float(screen_width + 20)
                    wy = float(random.randint(0, max(0, screen_height - wood_img.get_height())))
                    vx = -random.uniform(wood_min_speed_px_per_sec, wood_max_speed_px_per_sec)
                    vy = random.uniform(-wood_max_vy_px_per_sec, wood_max_vy_px_per_sec)
                    woods.append(
                        {
                            "x": wx,
                            "y": wy,
                            "vx": vx,
                            "vy": vy,
                            "img": wood_img,
                            "hit": False,
                            "variant": "base",
                        }
                    )

                # Move lasers
                for p in projectiles:
                    p[0] += laser_speed_px_per_sec * dt
                projectiles = [p for p in projectiles if p[0] < screen_width + laser_w]

                # Move woods (random vertical movement + bounce)
                for w in woods:
                    w["x"] = float(w["x"]) + float(w["vx"]) * dt
                    w["y"] = float(w["y"]) + float(w["vy"]) * dt

                    w_img = w["img"]
                    h = w_img.get_height()
                    if float(w["y"]) < 0.0:
                        w["y"] = 0.0
                        w["vy"] = abs(float(w["vy"]))
                    elif float(w["y"]) + h > screen_height:
                        w["y"] = float(screen_height - h)
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
                    laser_rect = pygame.Rect(int(px), int(py), laser_w, laser_h)
                    hit_any = False
                    for w in woods:
                        w_img = w["img"]
                        wx = int(float(w["x"]))
                        wy = int(float(w["y"]))
                        wood_rect = pygame.Rect(wx, wy, w_img.get_width(), w_img.get_height())
                        if laser_rect.colliderect(wood_rect):
                            hit_any = True
                            if not bool(w["hit"]):
                                marks += 1
                                cx, cy = wood_rect.center
                                new_kind = random.choice(wood_variant_keys)
                                new_img = wood_variants[new_kind]
                                w["img"] = new_img
                                w["hit"] = True
                                w["variant"] = new_kind
                                w["x"] = float(cx - (new_img.get_width() // 2))
                                w["y"] = float(cy - (new_img.get_height() // 2))
                            break
                    if not hit_any:
                        remaining_projectiles.append([px, py])
                projectiles = remaining_projectiles

                current_player_img = player_shoot_img if shoot_pose_t > 0.0 else player_idle_img
                player_rect = pygame.Rect(
                    int(player_x),
                    int(player_y),
                    current_player_img.get_width(),
                    current_player_img.get_height(),
                )

                # If unhit wood touches Max: -1 mark. If hit wood touches Max: +1 mark.
                kept_woods_after_hit: list[dict[str, object]] = []
                for w in woods:
                    w_img = w["img"]
                    wx = int(float(w["x"]))
                    wy = int(float(w["y"]))
                    wood_rect = pygame.Rect(wx, wy, w_img.get_width(), w_img.get_height())
                    if player_rect.colliderect(wood_rect):
                        variant = str(w.get("variant", "base"))
                        if variant in ("star", "moon", "around"):
                            try:
                                if collect_sound is not None:
                                    collect_sound.play()
                            except Exception:
                                pass
                        elif (not bool(w["hit"])) and variant == "base":
                            try:
                                if got_hit_sound is not None:
                                    got_hit_sound.play()
                            except Exception:
                                pass
                        if bool(w["hit"]):
                            marks += 1
                        else:
                            marks -= 1
                        continue
                    kept_woods_after_hit.append(w)
                woods = kept_woods_after_hit

                bg_offset = (bg_offset + scroll_speed_px_per_sec * dt) % bg_width
                draw_scrolling_background(bg_offset)

                screen.blit(current_player_img, (int(player_x), int(player_y)))
                for w in woods:
                    screen.blit(w["img"], (int(float(w["x"])), int(float(w["y"]))))
                for px, py in projectiles:
                    screen.blit(laser_img, (int(px), int(py)))

                marks_s = hud_font.render(f"Marks: {marks}/{win_marks_gt}", True, (255, 255, 255))
                time_s = hud_font.render(f"Time: {int(remaining)}", True, (255, 255, 255))
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

            won = marks >= win_marks_gt
            title = "YOU WIN" if won else "YOU LOSE"
            subtitle = f"Marks: {marks}"

            t_s = end_font.render(title, True, (255, 255, 255))
            st_s = hud_font.render(subtitle, True, (255, 255, 255))

            t_rect = t_s.get_rect(center=(screen_width // 2, screen_height // 2 - 60))
            st_rect = st_s.get_rect(center=(screen_width // 2, screen_height // 2 + 20))

            replay_btn_rect = replay_btn_img.get_rect(
                center=(
                    screen_width // 2,
                    min(
                        screen_height - (replay_btn_img.get_height() // 2) - 20,
                        st_rect.bottom + (replay_btn_img.get_height() // 2) + 20,
                    ),
                )
            )
            home_btn_rect = home_btn_img.get_rect(
                center=(
                    screen_width // 2,
                    min(
                        screen_height - (home_btn_img.get_height() // 2) - 20,
                        replay_btn_rect.bottom + (home_btn_img.get_height() // 2) + 14,
                    ),
                )
            )

            # If player won and invitation image is available, prepare its rect.
            invitation_rect = None
            if won and (invitation_img is not None):
                # Center horizontally, nudge up vertically (42% down instead of 50%)
                invitation_rect = invitation_img.get_rect(center=(screen_width // 2, int(screen_height * 0.42)))

            pygame.mouse.set_visible(True)
            replay_requested = False
            home_requested = False

            # If showing invitation, clear any pending input so leftover keys
            # (e.g. SPACE from gameplay) don't immediately close the screen.
            if invitation_rect is not None:
                pygame.event.clear()

            while (not replay_requested) and (not home_requested):
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        exit_whole_program()
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        exit_whole_program()
                    # If invitation is shown, only Enter or mouse click returns to caller
                    if invitation_rect is not None:
                        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            return
                        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                            return
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        # Only check the replay/home buttons when invitation isn't shown
                        if invitation_rect is None:
                            if replay_btn_rect.collidepoint(event.pos):
                                replay_requested = True
                            elif home_btn_rect.collidepoint(event.pos):
                                home_requested = True

                draw_scrolling_background(bg_offset)
                if invitation_rect is not None:
                    # Show invitation image when won
                    screen.blit(invitation_img, invitation_rect)
                else:
                    screen.blit(t_s, t_rect)
                    screen.blit(st_s, st_rect)
                    screen.blit(replay_btn_img, replay_btn_rect)
                    screen.blit(home_btn_img, home_btn_rect)
                pygame.display.flip()
                clock.tick(60)

            if replay_requested:
                continue
            if home_requested:
                return

            return
    finally:
        pygame.mouse.set_visible(True)
        if created_display:
            pygame.quit()


def main() -> None:
    run(None)


if __name__ == "__main__":
    main()
