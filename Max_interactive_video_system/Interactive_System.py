"""Interactive video system (simple branching A/B).

Behavior:
- Plays `Max_scenes001.mp4`.
- When it ends, shows two buttons: A (left) and B (right).
- Clicking A plays `Round1_A.mp4`.
- Clicking B plays `Round1_B.mp4`.
- After `Round1_A.mp4` or `Round1_B.mp4` ends, plays `Max_scenes002.mp4`.
- When `Max_scenes002.mp4` ends, shows the buttons again.
- Clicking A plays `Max_s2_A_New.mp4`.
- Clicking B plays `Max_s2_B.mp4`.

Notes:
- Video is decoded with MoviePy and displayed with Pygame.
- Audio is played via `pygame.mixer` when available.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pygame


@dataclass(frozen=True)
class InteractiveConfig:
    """Basic configuration for interactive video system."""

    base_dir: Path

    start_video: str = "Max_scenes001.mp4"
    option_a_video: str = "Round1_A.mp4"
    option_b_video: str = "Round1_B.mp4"
    after_round1_video: str = "Max_scenes002.mp4"

    option2_a_video: str = "Max_s2_A_New.mp4"
    option2_b_video: str = "Max_s2_B.mp4"

    fps_fallback: int = 30


Choice = Literal["A", "B"]


@dataclass
class PlayVideoResult:
    ended: bool
    last_frame: pygame.Surface | None
    last_frame_rect: pygame.Rect | None


def _fit_rect(src_w: int, src_h: int, dst_w: int, dst_h: int) -> pygame.Rect:
    """Compute a centered rect preserving aspect ratio."""
    src_w = max(1, int(src_w))
    src_h = max(1, int(src_h))
    dst_w = max(1, int(dst_w))
    dst_h = max(1, int(dst_h))
    scale = min(dst_w / src_w, dst_h / src_h)
    w = max(1, int(src_w * scale))
    h = max(1, int(src_h * scale))
    x = (dst_w - w) // 2
    y = (dst_h - h) // 2
    return pygame.Rect(x, y, w, h)


def _play_video(screen: pygame.Surface, video_path: Path, fps_fallback: int) -> PlayVideoResult:
    """Play a video inside the provided pygame screen.

    Returns a result containing whether playback ended normally, plus the last frame
    rendered (scaled) and its destination rect.
    """
    try:
        from moviepy.video.io.VideoFileClip import VideoFileClip  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "MoviePy is required to play videos in-window. Install with `pip install moviepy`."
        ) from e

    if not video_path.exists():
        raise FileNotFoundError(f"Missing video: {video_path}")

    clock = pygame.time.Clock()

    clip = VideoFileClip(str(video_path))

    screen_w, screen_h = screen.get_size()
    frame_rect = _fit_rect(int(clip.w), int(clip.h), screen_w, screen_h)

    # --- Audio (optional) ---
    # We extract audio to a cached WAV on disk because pygame can't reliably
    # stream MP4 audio directly.
    audio_tmp_path: Path | None = None
    try:
        if pygame.mixer.get_init() is None:
            pygame.mixer.init()
    except Exception as e:
        print("[audio] pygame.mixer.init failed:", type(e).__name__, e)

    try:
        if getattr(clip, "audio", None) is not None and pygame.mixer.get_init() is not None:
            cache_dir = video_path.parent / ".cache_audio"
            cache_dir.mkdir(parents=True, exist_ok=True)
            audio_tmp_path = cache_dir / f"{video_path.stem}.wav"

            if (not audio_tmp_path.exists()) or audio_tmp_path.stat().st_size == 0:
                # Write once, reuse next runs.
                # MoviePy 2.x API: no `verbose` argument.
                clip.audio.write_audiofile(
                    str(audio_tmp_path),
                    fps=44100,
                    nbytes=2,
                    codec="pcm_s16le",
                    logger=None,
                )

            try:
                pygame.mixer.music.load(str(audio_tmp_path))
                pygame.mixer.music.play()
            except Exception:
                audio_tmp_path = None
    except Exception:
        print("[audio] audio extraction/playback setup failed")
        audio_tmp_path = None

    # --- Video loop ---
    # Render frame based on elapsed time for better A/V sync.
    start_ms = pygame.time.get_ticks()
    duration = float(getattr(clip, "duration", 0.0) or 0.0)
    if duration <= 0:
        duration = 10_000.0  # effectively "until quit" for malformed clips

    target_fps = int(getattr(clip, "fps", None) or fps_fallback)
    if target_fps <= 0:
        target_fps = int(fps_fallback)
    target_fps = max(24, min(60, target_fps))

    last_frame_surf: pygame.Surface | None = None
    last_frame_rect: pygame.Rect | None = frame_rect

    try:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    try:
                        pygame.mixer.music.stop()
                    except Exception:
                        pass
                    return PlayVideoResult(False, last_frame_surf, last_frame_rect)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    try:
                        pygame.mixer.music.stop()
                    except Exception:
                        pass
                    return PlayVideoResult(False, last_frame_surf, last_frame_rect)

            t = (pygame.time.get_ticks() - start_ms) / 1000.0
            if t >= duration:
                break

            frame = clip.get_frame(t)
            h, w = int(frame.shape[0]), int(frame.shape[1])
            surf = pygame.image.frombuffer(frame.tobytes(), (w, h), "RGB").convert()
            surf = pygame.transform.smoothscale(surf, (frame_rect.width, frame_rect.height))
            last_frame_surf = surf

            screen.fill((0, 0, 0))
            screen.blit(surf, frame_rect)
            pygame.display.flip()
            clock.tick(target_fps)

        return PlayVideoResult(True, last_frame_surf, last_frame_rect)
    finally:
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

        try:
            clip.close()
        except Exception:
            pass


def _choose_option(
    screen: pygame.Surface,
    background: pygame.Surface | None = None,
    background_rect: pygame.Rect | None = None,
    button_a_image_path: Path | None = None,
    button_b_image_path: Path | None = None,
) -> Choice | None:
    """Show A/B buttons and return the chosen option (or None on quit)."""
    clock = pygame.time.Clock()
    pygame.mouse.set_visible(True)

    screen_w, screen_h = screen.get_size()

    # Optional image buttons (use original pixel size; no scaling).
    btn_a_img: pygame.Surface | None = None
    btn_b_img: pygame.Surface | None = None
    try:
        if button_a_image_path is not None and button_a_image_path.exists():
            btn_a_img = pygame.image.load(str(button_a_image_path)).convert_alpha()
        if button_b_image_path is not None and button_b_image_path.exists():
            btn_b_img = pygame.image.load(str(button_b_image_path)).convert_alpha()
    except Exception:
        btn_a_img = None
        btn_b_img = None

    # Default (non-image) button size.
    fallback_button_w = int(screen_w * 0.22)
    fallback_button_h = int(screen_h * 0.14)

    # If images are available, use their original sizes for both the visuals and hitboxes.
    button_a_w = btn_a_img.get_width() if btn_a_img is not None else fallback_button_w
    button_a_h = btn_a_img.get_height() if btn_a_img is not None else fallback_button_h
    button_b_w = btn_b_img.get_width() if btn_b_img is not None else fallback_button_w
    button_b_h = btn_b_img.get_height() if btn_b_img is not None else fallback_button_h

    gap = int(screen_w * 0.06)
    center_y = int(screen_h * 0.77)

    total_w = button_a_w + gap + button_b_w
    left_x = (screen_w - total_w) // 2
    right_x = left_x + button_a_w + gap

    btn_a = pygame.Rect(left_x, center_y - (button_a_h // 2), button_a_w, button_a_h)
    btn_b = pygame.Rect(right_x, center_y - (button_b_h // 2), button_b_w, button_b_h)

    font = pygame.font.SysFont(None, max(24, int(fallback_button_h * 0.55)))
    hint_font = pygame.font.SysFont(None, max(18, int(screen_h * 0.04)))

    while True:
        mx, my = pygame.mouse.get_pos()
        hover_a = btn_a.collidepoint((mx, my))
        hover_b = btn_b.collidepoint((mx, my))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_a.collidepoint(event.pos):
                    return "A"
                if btn_b.collidepoint(event.pos):
                    return "B"

        # Keep the final video frame on-screen behind the buttons.
        if background is not None and background_rect is not None:
            screen.fill((0, 0, 0))
            screen.blit(background, background_rect)
        else:
            screen.fill((0, 0, 0))

        # Draw buttons
        def draw_btn_fallback(rect: pygame.Rect, label: str, hovered: bool) -> None:
            bg = (70, 70, 70) if not hovered else (110, 110, 110)
            pygame.draw.rect(screen, bg, rect, border_radius=10)
            pygame.draw.rect(screen, (220, 220, 220), rect, width=3, border_radius=10)
            txt = font.render(label, True, (255, 255, 255))
            screen.blit(txt, txt.get_rect(center=rect.center))

        if btn_a_img is not None:
            screen.blit(btn_a_img, btn_a)
            if hover_a:
                pygame.draw.rect(screen, (255, 255, 255), btn_a, width=3, border_radius=10)
        else:
            draw_btn_fallback(btn_a, "A", hover_a)

        if btn_b_img is not None:
            screen.blit(btn_b_img, btn_b)
            if hover_b:
                pygame.draw.rect(screen, (255, 255, 255), btn_b, width=3, border_radius=10)
        else:
            draw_btn_fallback(btn_b, "B", hover_b)

        hint = hint_font.render("Choose an option", True, (220, 220, 220))
        screen.blit(hint, hint.get_rect(center=(screen_w // 2, int(screen_h * 0.55))))

        pygame.display.flip()
        clock.tick(60)


def run(screen: pygame.Surface | None = None, config: InteractiveConfig | None = None) -> int:
    """Run the interactive video system.

    If `screen` is provided, videos will be rendered into that surface and this
    function will return to the caller without calling `pygame.quit()`.
    """
    created_display = False

    if config is None:
        config = InteractiveConfig(base_dir=Path(__file__).resolve().parent)

    start_path = config.base_dir / config.start_video
    a_path = config.base_dir / config.option_a_video
    b_path = config.base_dir / config.option_b_video
    after_round1_path = config.base_dir / config.after_round1_video

    option2_a_path = config.base_dir / config.option2_a_video
    option2_b_path = config.base_dir / config.option2_b_video

    button_a_img = config.base_dir / "Button_A.png"
    button_b_img = config.base_dir / "Button_B.png"

    if screen is None:
        pygame.init()
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Interactive Video System")
        created_display = True

    try:
        start_result = _play_video(screen, start_path, fps_fallback=config.fps_fallback)
        if not start_result.ended:
            return 0

        choice = _choose_option(
            screen,
            start_result.last_frame,
            start_result.last_frame_rect,
            button_a_image_path=button_a_img,
            button_b_image_path=button_b_img,
        )
        if choice is None:
            return 0

        next_path = a_path if choice == "A" else b_path
        round1_result = _play_video(screen, next_path, fps_fallback=config.fps_fallback)
        if not round1_result.ended:
            return 0

        after_round1_result = _play_video(screen, after_round1_path, fps_fallback=config.fps_fallback)
        if not after_round1_result.ended:
            return 0

        choice2 = _choose_option(
            screen,
            after_round1_result.last_frame,
            after_round1_result.last_frame_rect,
            button_a_image_path=button_a_img,
            button_b_image_path=button_b_img,
        )
        if choice2 is None:
            return 0

        next2_path = option2_a_path if choice2 == "A" else option2_b_path
        _play_video(screen, next2_path, fps_fallback=config.fps_fallback)
        return 0
    finally:
        # Only quit pygame if we created the display here.
        if created_display:
            pygame.quit()


def main() -> int:
    return run(screen=None, config=None)


if __name__ == "__main__":
    raise SystemExit(main())
