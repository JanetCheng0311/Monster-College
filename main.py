import os
import pygame
import subprocess
import sys
import numpy as np
from moviepy.video.io.VideoFileClip import VideoFileClip


# Initialize Pygame
pygame.init()

# Set up the display in full screen mode (copied from Max Mini Game.py)
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Main Menu")

SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

ASSET_DIR = os.path.join(os.path.dirname(__file__), "meun&map")
BG_PATH = os.path.join(ASSET_DIR, "cloud.png")

if not os.path.exists(BG_PATH):
    raise FileNotFoundError(f"Missing background image: {BG_PATH}. Put cloud.png in the meun&map folder.")

_bg_raw = pygame.image.load(BG_PATH).convert()
_bg_w, _bg_h = _bg_raw.get_size()

# Scale background to fill the screen while preserving aspect ratio
scale = max(SCREEN_WIDTH / _bg_w, SCREEN_HEIGHT / _bg_h)
_bg = pygame.transform.smoothscale(_bg_raw, (int(_bg_w * scale), int(_bg_h * scale)))

# Load menu assets
LOGO_PATH = os.path.join(ASSET_DIR, "logo.png")
START_BTN_PATH = os.path.join(ASSET_DIR, "start_button.png")

VIDEO_PATH = os.path.join(ASSET_DIR, "skytoschool.mp4")

if not os.path.exists(VIDEO_PATH):
    raise FileNotFoundError(f"Missing video file: {VIDEO_PATH}. Put skytoschool.mp4 in the meun&map folder.")

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
    font = pygame.font.SysFont(None, 48)
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
    Audio is ignored to keep implementation simple and reliable across platforms.
    """
    clip = VideoFileClip(path)
    fps = clip.fps if clip.fps and clip.fps > 0 else 30
    clock = pygame.time.Clock()

    try:
        for frame in clip.iter_frames(fps=fps, dtype="uint8"):
            # handle quit / escape events while playing
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    clip.close()
                    return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    clip.close()
                    return

            # frame is HxWx3 RGB
            h, w = frame.shape[0], frame.shape[1]
            # create a surface from the frame bytes
            surf = pygame.image.frombuffer(frame.tobytes(), (w, h), "RGB")
            # scale to fullscreen while preserving aspect
            surf = pygame.transform.smoothscale(surf, (SCREEN_WIDTH, SCREEN_HEIGHT))
            screen.blit(surf, (0, 0))
            pygame.display.flip()
            clock.tick(fps)
    finally:
        try:
            clip.close()
        except Exception:
            pass


def play_video() -> None:
    """Try in-window playback first, then fallback to system opener if it fails."""
    try:
        print(f"Attempting in-window playback: {VIDEO_PATH}")
        sys.stdout.flush()
        play_video_in_pygame(VIDEO_PATH)
        return
    except Exception as e:
        print("In-window playback failed:", e)

    # Fallback: open with system default player
    try:
        print(f"Falling back to system player for: {VIDEO_PATH}")
        sys.stdout.flush()
        if sys.platform == "darwin":
            subprocess.Popen(["open", VIDEO_PATH])
        elif sys.platform.startswith("win"):
            os.startfile(VIDEO_PATH)
        else:
            subprocess.Popen(["xdg-open", VIDEO_PATH])
        return
    except Exception as e:
        print("Fallback open failed:", e)
    print("Unable to open video. Check the file and system defaults.")


if __name__ == "__main__":
    main()
