import os
import pygame
import subprocess
import sys
import importlib.util
import importlib
import numpy as np
import tempfile
import time
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.editor import concatenate_videoclips


# Initialize Pygame
pygame.init()

# Set up the display in full screen mode (copied from Max Mini Game.py)
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Main Menu")

SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

ASSET_DIR = os.path.join(os.path.dirname(__file__), "menu&map")
BG_PATH = os.path.join(ASSET_DIR, "cloud.png")

if not os.path.exists(BG_PATH):
    raise FileNotFoundError(f"Missing background image: {BG_PATH}. Put cloud.png in the menu&map folder.")

_bg_raw = pygame.image.load(BG_PATH).convert()
_bg_w, _bg_h = _bg_raw.get_size()

# Scale background to fill the screen while preserving aspect ratio
scale = max(SCREEN_WIDTH / _bg_w, SCREEN_HEIGHT / _bg_h)
_bg = pygame.transform.smoothscale(_bg_raw, (int(_bg_w * scale), int(_bg_h * scale)))

# Load menu assets
LOGO_PATH = os.path.join(ASSET_DIR, "logo.png")
START_BTN_PATH = os.path.join(ASSET_DIR, "start_button.png")

INTRO_VIDEO_CANDIDATES = (
    os.path.join(ASSET_DIR, "skytoschool.mp4"),
    os.path.join(ASSET_DIR, "monstercollegeintro.mp4"),
    os.path.join(ASSET_DIR, "intro_video", "intro01.mp4"),
)


def resolve_intro_video_path() -> str | None:
    for candidate in INTRO_VIDEO_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    return None

for _p in (LOGO_PATH, START_BTN_PATH):
    if not os.path.exists(_p):
        raise FileNotFoundError(f"Missing menu asset: {_p}.")

_logo_raw = pygame.image.load(LOGO_PATH).convert_alpha()
_start_raw = pygame.image.load(START_BTN_PATH).convert_alpha()

# Scale logo + buttons relative to screen height
# Make the logo larger and the buttons larger as requested
LOGO_SCALE_MULT = 3.5
BTN_SCALE_MULT = 1.8
LOGO_TARGET_H = int(SCREEN_HEIGHT * 0.18 * LOGO_SCALE_MULT)
BTN_TARGET_H = int(SCREEN_HEIGHT * 0.12 * BTN_SCALE_MULT)

def _scale_to_height(img: pygame.Surface, target_h: int) -> pygame.Surface:
    target_h = max(1, int(target_h))
    w, h = img.get_size()
    if h <= 0:
        return img
    scale = target_h / h
    return pygame.transform.smoothscale(img, (max(1, int(w * scale)), target_h))

_logo_img = _scale_to_height(_logo_raw, LOGO_TARGET_H)
_start_img = _scale_to_height(_start_raw, BTN_TARGET_H)


def main() -> None:
    clock = pygame.time.Clock()
    running = True
    pressed_button = None

    # Pre-render simple instruction text
    font = pygame.font.Font(None, 48)
    instr_s = font.render("Press ENTER to play — ESC to quit", True, (255, 255, 255))

    while running:
        dt = clock.tick(60) / 1000.0

        # Compute centered layout for logo + buttons before handling events
        spacing_top = 10
        logo_h = _logo_img.get_height()
        start_h = _start_img.get_height()
        total_h = logo_h + spacing_top + start_h
        # Center the group vertically (moved higher than previous lower-offset layout)
        top_y = int((SCREEN_HEIGHT - total_h) / 2)

        bg_x = (SCREEN_WIDTH - _bg.get_width()) // 2
        bg_y = (SCREEN_HEIGHT - _bg.get_height()) // 2

        logo_rect = _logo_img.get_rect(midtop=(SCREEN_WIDTH // 2, top_y))
        start_rect = _start_img.get_rect(midtop=(SCREEN_WIDTH // 2, logo_rect.bottom + spacing_top))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    # Play video when Enter pressed
                            play_video()
                            show_map()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # record which button was pressed
                if start_rect.collidepoint(event.pos):
                    pressed_button = "start"
                else:
                    pressed_button = None
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # trigger click if press started and ended on same button
                if pressed_button == "start" and start_rect.collidepoint(event.pos):
                    # Play the video when Start is clicked
                    play_video()
                    show_map()
                pressed_button = None

        # Draw background centered
        screen.blit(_bg, (bg_x, bg_y))

        # Draw logo and buttons (centered group)
        screen.blit(_logo_img, logo_rect)

        mx, my = pygame.mouse.get_pos()

        # Simple hover/press visual: slight scale but no glow
        def _maybe_draw_button(img: pygame.Surface, rect: pygame.Rect, hovered: bool, pressed: bool) -> None:
            if pressed:
                scale_mult = 0.96
            elif hovered:
                scale_mult = 1.06
            else:
                scale_mult = 1.0
            w = max(1, int(img.get_width() * scale_mult))
            h = max(1, int(img.get_height() * scale_mult))
            scaled = pygame.transform.smoothscale(img, (w, h))
            srect = scaled.get_rect(center=rect.center)
            screen.blit(scaled, srect)

        hovered = start_rect.collidepoint((mx, my))
        pressed = pressed_button == "start" and pygame.mouse.get_pressed()[0]
        _maybe_draw_button(_start_img, start_rect, hovered, pressed)

        # Draw instructions at bottom center
        instr_rect = instr_s.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
        # Draw a subtle shadow for readability
        shadow = font.render("Press ENTER to play — ESC to quit", True, (0, 0, 0))
        shadow_rect = instr_rect.copy()
        shadow_rect.move_ip(2, 2)
        screen.blit(shadow, shadow_rect)
        screen.blit(instr_s, instr_rect)

        pygame.display.flip()

    pygame.quit()


def play_video_in_pygame(path: str) -> None:
    """Play the given video file inside the existing Pygame `screen`.

    This uses MoviePy to decode frames and blits them into the Pygame surface.
    Playback uses wall-clock timing and frame catch-up to keep A/V in sync.
    """
    clip = VideoFileClip(path)
    fps = clip.fps if clip.fps and clip.fps > 0 else 30
    frame_interval = 1.0 / float(fps)

    # Prepare optional on-screen instruction (styled like the start screen)
    font = pygame.font.Font(None, 48)
    skip_allowed = os.path.basename(path).lower() in {
        "skytoschool.mp4",
        "monstercollegeintro.mp4",
        "intro01.mp4",
    }
    instr_s = None
    shadow = None
    instr_rect = None
    shadow_rect = None
    if skip_allowed:
        instr_text = "Use TAB to skip video"
        instr_s = font.render(instr_text, True, (255, 255, 255))
        shadow = font.render(instr_text, True, (0, 0, 0))
        instr_rect = instr_s.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
        shadow_rect = instr_rect.copy()
        shadow_rect.move_ip(2, 2)

    audio_temp = None
    fallback_start_time = None

    def _playback_time_s() -> float:
        """Return current playback time using audio clock when available."""
        if pygame.mixer.get_init():
            try:
                pos_ms = pygame.mixer.music.get_pos()
                if pos_ms >= 0:
                    return pos_ms / 1000.0
            except Exception:
                pass
        if fallback_start_time is None:
            return 0.0
        return max(0.0, time.perf_counter() - fallback_start_time)
    try:
        # extract and play audio if present
        try:
            if hasattr(clip, "audio") and clip.audio is not None:
                # Use WAV to avoid MP3 encoder delay and improve A/V sync.
                tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                tmp_name = tmp.name
                tmp.close()
                clip.audio.write_audiofile(tmp_name, codec="pcm_s16le", logger=None)
                audio_temp = tmp_name
                try:
                    if not pygame.mixer.get_init():
                        pygame.mixer.init()
                    pygame.mixer.music.load(audio_temp)
                    pygame.mixer.music.play()
                except Exception as e:
                    print("Warning: failed to play audio via pygame.mixer:", e)
        except Exception as e:
            print("Warning: failed to extract/play audio:", e)

        fallback_start_time = time.perf_counter()

        frame_index = 0
        for frame in clip.iter_frames(fps=fps, dtype="uint8"):
            # handle quit / escape / tab events while playing
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    try:
                        if pygame.mixer.get_init():
                            pygame.mixer.music.stop()
                    except Exception:
                        pass
                    clip.close()
                    if audio_temp is not None:
                        try:
                            os.remove(audio_temp)
                        except Exception:
                            pass
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        try:
                            if pygame.mixer.get_init():
                                pygame.mixer.music.stop()
                        except Exception:
                            pass
                        clip.close()
                        if audio_temp is not None:
                            try:
                                os.remove(audio_temp)
                            except Exception:
                                pass
                        return
                    if event.key == pygame.K_TAB and skip_allowed:
                        try:
                            if pygame.mixer.get_init():
                                pygame.mixer.music.stop()
                        except Exception:
                            pass
                        clip.close()
                        if audio_temp is not None:
                            try:
                                os.remove(audio_temp)
                            except Exception:
                                pass
                        return

            # Sync using audio clock: drop late frames, wait if video gets ahead.
            playback_time = _playback_time_s()
            expected_index = int(playback_time * fps)
            if frame_index < expected_index - 1:
                frame_index += 1
                continue
            while frame_index > expected_index + 1:
                time.sleep(0.001)
                playback_time = _playback_time_s()
                expected_index = int(playback_time * fps)

            # frame is HxWx3 RGB
            h, w = frame.shape[0], frame.shape[1]
            # create a surface from the frame bytes
            surf = pygame.image.frombuffer(frame.tobytes(), (w, h), "RGB")
            # Use faster scaling during video playback to reduce CPU pressure and A/V drift.
            if w != SCREEN_WIDTH or h != SCREEN_HEIGHT:
                surf = pygame.transform.scale(surf, (SCREEN_WIDTH, SCREEN_HEIGHT))
            screen.blit(surf, (0, 0))

            # Draw the optional instruction over the video
            if instr_s is not None:
                screen.blit(shadow, shadow_rect)
                screen.blit(instr_s, instr_rect)

            pygame.display.flip()
            frame_index += 1

            # Small cap to keep CPU usage reasonable without harming sync.
            time.sleep(min(frame_interval * 0.3, 0.005))
    finally:
        try:
            clip.close()
        except Exception:
            pass
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass
        if audio_temp is not None:
            try:
                os.remove(audio_temp)
            except Exception:
                pass


def play_video() -> None:
    """Play intro01-04 as one continuous intro sequence.

    TAB skips the entire sequence.
    """
    intro_paths = [os.path.join(INTRO_VIDEO_DIR, name) for name in INTRO_VIDEO_NAMES]
    existing_paths = [p for p in intro_paths if os.path.exists(p)]

    if not existing_paths:
        print(f"No intro videos found in: {INTRO_VIDEO_DIR}")
        return

    try:
        print(f"Attempting in-window playback: {video_path}")
        sys.stdout.flush()
        play_video_in_pygame(video_path)
        return
    except Exception as e:
        print("In-window playback failed:", e)

    # Fallback: open with system default player
    try:
        print(f"Falling back to system player for: {video_path}")
        sys.stdout.flush()
        if sys.platform == "darwin":
            subprocess.Popen(["open", video_path])
        elif sys.platform.startswith("win"):
            os.startfile(video_path)
        else:
            subprocess.Popen(["xdg-open", video_path])
        return
    except Exception as e:
        print("Fallback open failed:", e)
    print("Unable to open video. Check the file and system defaults.")


def show_map() -> None:
    """Display the map image fullscreen and wait until the user quits or presses BACKSPACE to return."""
    global screen, SCREEN_WIDTH, SCREEN_HEIGHT
    MAP_PATH = os.path.join(ASSET_DIR, "map.png")
    if not os.path.exists(MAP_PATH):
        print(f"Missing map image: {MAP_PATH}. Put map.png in the menu&map folder.")
        return

    try:
        map_raw = pygame.image.load(MAP_PATH).convert()
    except Exception as e:
        print("Failed to load map image:", e)
        return

    mw, mh = map_raw.get_size()
    scale = max(SCREEN_WIDTH / mw, SCREEN_HEIGHT / mh)
    map_surf = pygame.transform.smoothscale(map_raw, (int(mw * scale), int(mh * scale)))
    map_x = (SCREEN_WIDTH - map_surf.get_width()) // 2
    map_y = (SCREEN_HEIGHT - map_surf.get_height()) // 2

    clock = pygame.time.Clock()
    showing = True
    # Load button assets for map screen
    def _load_btn(n):
        p = os.path.join(ASSET_DIR, n)
        return pygame.image.load(p).convert_alpha() if os.path.exists(p) else None

    robot_normal = _load_btn("robot01.png")
    robot_hover = _load_btn("robot02.png")
    tiger_normal = _load_btn("tigerlogo1.png")
    tiger_hover = _load_btn("tigerlogo2.png")
    dog_normal = _load_btn("doggegg001.png")
    dog_hover = _load_btn("doggegg002.png")

    # Scale buttons relative to screen height (made larger per request)
    BTN_TARGET_H = int(SCREEN_HEIGHT * 0.18)
    def _scale_opt(img):
        if img is None:
            return None
        return _scale_to_height(img, BTN_TARGET_H)

    # Make robot button a bit larger than the others for emphasis
    robot_img = _scale_to_height(robot_normal, int(BTN_TARGET_H * 1.35)) if robot_normal is not None else None
    robot_img_hov = _scale_to_height(robot_hover, int(BTN_TARGET_H * 1.35)) if robot_hover is not None else None
    tiger_img = _scale_opt(tiger_normal)
    tiger_img_hov = _scale_opt(tiger_hover)
    dog_img = _scale_opt(dog_normal)
    dog_img_hov = _scale_opt(dog_hover)

    # Compute button positions (left, right, top-center for dog egg)
    left_pos = (int(SCREEN_WIDTH * 0.18), int(SCREEN_HEIGHT * 0.5))
    right_pos = (int(SCREEN_WIDTH * 0.82), int(SCREEN_HEIGHT * 0.5))
    top_pos = (int(SCREEN_WIDTH * 0.5), int(SCREEN_HEIGHT * 0.22))

    # Build rects if images exist
    robot_rect = robot_img.get_rect(center=left_pos) if robot_img is not None else None
    tiger_rect = tiger_img.get_rect(center=right_pos) if tiger_img is not None else None
    dog_rect = dog_img.get_rect(center=top_pos) if dog_img is not None else None

    pressed_btn = None
    max_cleared = False
    tiger_cleared = False
    locked_hint_until_ms = 0
    dev_unlock_hint_until_ms = 0
    # Prepare bottom instruction like the start screen
    font = pygame.font.Font(None, 48)
    esc_text = "ESC to close game"
    instr_s = font.render(esc_text, True, (255, 255, 255))
    shadow = font.render(esc_text, True, (0, 0, 0))
    instr_rect = instr_s.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
    shadow_rect = instr_rect.copy()
    shadow_rect.move_ip(2, 2)
    lock_font = pygame.font.Font(None, 36)

    while showing:
        launch_mini_game = False
        launch_tiger_game = False
        launch_dog_game = False
        dog_unlocked = max_cleared and tiger_cleared

        mx, my = pygame.mouse.get_pos()
        hovered_robot = robot_rect.collidepoint((mx, my)) if robot_rect is not None else False
        hovered_tiger = tiger_rect.collidepoint((mx, my)) if tiger_rect is not None else False
        hovered_dog = dog_rect.collidepoint((mx, my)) if dog_rect is not None else False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_BACKSPACE:
                    # Return to main menu loop
                    showing = False
                if event.key == pygame.K_2:
                    # Dev shortcut: force unlock Doggegg by marking both prerequisites as cleared.
                    max_cleared = True
                    tiger_cleared = True
                    dev_unlock_hint_until_ms = pygame.time.get_ticks() + 1800
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if hovered_robot:
                    pressed_btn = "robot"
                elif hovered_tiger:
                    pressed_btn = "tiger"
                elif hovered_dog:
                    pressed_btn = "dog"
                else:
                    pressed_btn = None
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if pressed_btn == "robot" and hovered_robot:
                    # Launch Max Mini Game (smooth: keep this frame on-screen; don't tear down the display).
                    launch_mini_game = True
                elif pressed_btn == "tiger" and hovered_tiger:
                    # Launch Tiger Game with the same embedded-jump behavior as Max Mini Game.
                    launch_tiger_game = True
                elif pressed_btn == "dog" and hovered_dog:
                    if dog_unlocked:
                        launch_dog_game = True
                    else:
                        locked_hint_until_ms = pygame.time.get_ticks() + 2000
                pressed_btn = None

        # Draw map
        screen.blit(map_surf, (map_x, map_y))

        # Draw buttons with hover/pressed visuals
        def _draw_btn(normal, hov, rect, hovered, pressed):
            if rect is None or normal is None:
                return
            img = hov if (hovered or pressed) and hov is not None else normal
            screen.blit(img, img.get_rect(center=rect.center))

        _draw_btn(robot_img, robot_img_hov, robot_rect, hovered_robot, pressed_btn == "robot")
        _draw_btn(tiger_img, tiger_img_hov, tiger_rect, hovered_tiger, pressed_btn == "tiger")
        _draw_btn(dog_img, dog_img_hov, dog_rect, hovered_dog, pressed_btn == "dog")

        if not dog_unlocked and dog_rect is not None:
            # Dim the Doggegg icon until both prerequisite mini-games are cleared.
            lock_mask = pygame.Surface((dog_rect.width, dog_rect.height), pygame.SRCALPHA)
            lock_mask.fill((0, 0, 0, 120))
            screen.blit(lock_mask, dog_rect.topleft)

        now_ms = pygame.time.get_ticks()
        if not dog_unlocked or now_ms < locked_hint_until_ms:
            max_state = "OK" if max_cleared else "Pending"
            tiger_state = "OK" if tiger_cleared else "Pending"
            lock_text = f"Unlock Doggegg: clear Max ({max_state}) and Tiger ({tiger_state})"
            lock_s = lock_font.render(lock_text, True, (255, 255, 255))
            lock_shadow = lock_font.render(lock_text, True, (0, 0, 0))
            lock_rect = lock_s.get_rect(center=(SCREEN_WIDTH // 2, 44))
            lock_shadow_rect = lock_rect.copy()
            lock_shadow_rect.move_ip(2, 2)
            screen.blit(lock_shadow, lock_shadow_rect)
            screen.blit(lock_s, lock_rect)

        if now_ms < dev_unlock_hint_until_ms:
            dev_text = "Dev: forced unlock enabled (key 2)"
            dev_s = lock_font.render(dev_text, True, (255, 235, 120))
            dev_shadow = lock_font.render(dev_text, True, (0, 0, 0))
            dev_rect = dev_s.get_rect(center=(SCREEN_WIDTH // 2, 80))
            dev_shadow_rect = dev_rect.copy()
            dev_shadow_rect.move_ip(2, 2)
            screen.blit(dev_shadow, dev_shadow_rect)
            screen.blit(dev_s, dev_rect)

        # Draw bottom instruction
        screen.blit(shadow, shadow_rect)
        screen.blit(instr_s, instr_rect)
        pygame.display.flip()
        clock.tick(30)

        if launch_mini_game:
            mini_path = os.path.join(os.path.dirname(__file__), "Max_mini_game", "Max Mini Game.py")
            if not os.path.exists(mini_path):
                print("Max Mini Game script not found at", mini_path)
                continue

            # Run the mini game inside the same Pygame window (no subprocess).
            try:
                spec = importlib.util.spec_from_file_location("max_mini_game", mini_path)
                if spec is None or spec.loader is None:
                    raise RuntimeError("Unable to load Max Mini Game module")
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                result = None

                if hasattr(mod, "run"):
                    result = mod.run(screen)
                elif hasattr(mod, "main"):
                    result = mod.main()
                else:
                    raise RuntimeError("Max Mini Game does not define run() or main()")

                if bool(result):
                    max_cleared = True

                # Clear any queued events from the mini game so the map doesn't instantly react.
                try:
                    pygame.event.clear()
                except Exception:
                    pass
            except Exception as e:
                print("Failed to run Max Mini Game:", e)

        if launch_tiger_game:
            tiger_path = os.path.join(os.path.dirname(__file__), "tiger-game", "main.py")
            if not os.path.exists(tiger_path):
                print("Tiger game script not found at", tiger_path)
                continue

            # Run tiger game inside the same Pygame window (no subprocess).
            try:
                spec = importlib.util.spec_from_file_location("tiger_game", tiger_path)
                if spec is None or spec.loader is None:
                    raise RuntimeError("Unable to load Tiger Game module")
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                result = None

                if hasattr(mod, "run"):
                    result = mod.run(screen)
                elif hasattr(mod, "main"):
                    result = mod.main(screen)
                else:
                    raise RuntimeError("Tiger Game does not define run() or main()")

                if bool(result):
                    tiger_cleared = True

                # Clear any queued events from the tiger game so the map doesn't instantly react.
                try:
                    pygame.event.clear()
                except Exception:
                    pass
            except Exception as e:
                print("Failed to run Tiger Game:", e)

        if launch_dog_game:
            dog_path = os.path.join(os.path.dirname(__file__), "sir_doggegg_nap_break", "tetris_game.py")
            if not os.path.exists(dog_path):
                print("Sir Doggegg game script not found at", dog_path)
                continue

            # Run Sir Doggegg game inside the same Pygame window (no subprocess).
            try:
                spec = importlib.util.spec_from_file_location("doggegg_game", dog_path)
                if spec is None or spec.loader is None:
                    raise RuntimeError("Unable to load Sir Doggegg module")
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)

                if hasattr(mod, "run"):
                    mod.run(screen)
                elif hasattr(mod, "main"):
                    mod.main(screen)
                else:
                    raise RuntimeError("Sir Doggegg game does not define run() or main()")

                # Clear any queued events so the map doesn't instantly react.
                try:
                    pygame.event.clear()
                except Exception:
                    pass
            except Exception as e:
                print("Failed to run Sir Doggegg Game:", e)


if __name__ == "__main__":
    main()
