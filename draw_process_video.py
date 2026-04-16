import argparse
import os
import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np


TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
DEFAULT_STAGE_COUNT = 20
DEFAULT_DURATION = 10
DEFAULT_FPS = 24
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create a vertical timelapse-style drawing video from one finished image."
    )
    parser.add_argument("--input", dest="input_image", help="Path to one source image.")
    parser.add_argument(
        "--input-dir",
        default="in",
        help="Directory with source images for batch processing.",
    )
    parser.add_argument(
        "--stages-dir",
        default="temp_stages",
        help="Directory for intermediate stage images.",
    )
    parser.add_argument(
        "--videos-dir",
        default="output_videos",
        help="Directory for final videos.",
    )
    parser.add_argument(
        "--frames-dir",
        default="temp_frames",
        help="Temporary directory for rendered video frames.",
    )
    parser.add_argument(
        "--stage-count",
        type=int,
        default=DEFAULT_STAGE_COUNT,
        help="Number of intermediate stages to generate.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=DEFAULT_DURATION,
        help="Final video duration in seconds.",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=DEFAULT_FPS,
        help="Frames per second for the final video.",
    )
    parser.add_argument(
        "--keep-stages",
        action="store_true",
        help="Keep stage images after video export.",
    )
    parser.add_argument(
        "--keep-frames",
        action="store_true",
        help="Keep temporary frame images after video export.",
    )
    parser.add_argument(
        "--stages-only",
        action="store_true",
        help="Generate only stage images without MP4 export.",
    )
    parser.add_argument(
        "--ffmpeg-bin",
        default=None,
        help="Optional full path to ffmpeg.exe.",
    )
    return parser.parse_args()


def find_ffmpeg(explicit_path: str | None = None) -> str | None:
    if explicit_path:
        explicit = Path(explicit_path)
        if explicit.exists():
            return str(explicit)

    env_ffmpeg = os.environ.get("FFMPEG_BIN")
    if env_ffmpeg:
        env_path = Path(env_ffmpeg)
        if env_path.exists():
            return str(env_path)

    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path

    local_appdata = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    if local_appdata.exists():
        matches = sorted(local_appdata.glob("**/ffmpeg.exe"))
        if matches:
            return str(matches[-1])
    return None


def ensure_ffmpeg(explicit_path: str | None = None) -> str:
    ffmpeg_path = find_ffmpeg(explicit_path)
    if ffmpeg_path is None:
        raise RuntimeError(
            "ffmpeg was not found in PATH, FFMPEG_BIN, or common WinGet locations. Install ffmpeg or pass --ffmpeg-bin."
        )
    return ffmpeg_path


def read_image(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return image


def resize_to_cover(image: np.ndarray, width: int, height: int) -> np.ndarray:
    h, w = image.shape[:2]
    scale = max(width / w, height / h)
    resized = cv2.resize(
        image,
        (int(round(w * scale)), int(round(h * scale))),
        interpolation=cv2.INTER_CUBIC,
    )
    y0 = max((resized.shape[0] - height) // 2, 0)
    x0 = max((resized.shape[1] - width) // 2, 0)
    return resized[y0 : y0 + height, x0 : x0 + width]


def resize_to_fit(image: np.ndarray, width: int, height: int) -> np.ndarray:
    h, w = image.shape[:2]
    scale = min(width / w, height / h)
    return cv2.resize(
        image,
        (max(1, int(round(w * scale))), max(1, int(round(h * scale)))),
        interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC,
    )


def sample_border_color(image: np.ndarray) -> np.ndarray:
    border = max(12, min(image.shape[:2]) // 30)
    h, w = image.shape[:2]
    strips = [
        image[:border, :, :],
        image[max(0, h - border) :, :, :],
        image[:, :border, :],
        image[:, max(0, w - border) :, :],
    ]
    pixels = np.concatenate([strip.reshape(-1, 3) for strip in strips], axis=0)
    return np.median(pixels, axis=0).astype(np.uint8)


def sample_edge_colors(image: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    border = max(12, min(image.shape[:2]) // 30)
    h, w = image.shape[:2]
    top = image[:border, :, :]
    bottom = image[max(0, h - border) :, :, :]
    left = image[:, :border, :]
    right = image[:, max(0, w - border) :, :]
    return (
        np.median(top.reshape(-1, 3), axis=0).astype(np.uint8),
        np.median(bottom.reshape(-1, 3), axis=0).astype(np.uint8),
        np.median(left.reshape(-1, 3), axis=0).astype(np.uint8),
        np.median(right.reshape(-1, 3), axis=0).astype(np.uint8),
    )


def create_edge_gradient_background(image: np.ndarray, width: int, height: int) -> np.ndarray:
    border_color = sample_border_color(image)
    top_color, bottom_color, left_color, right_color = sample_edge_colors(image)

    top_mix = ((top_color.astype(np.float32) * 0.7) + (border_color.astype(np.float32) * 0.3)).astype(np.uint8)
    bottom_mix = ((bottom_color.astype(np.float32) * 0.7) + (border_color.astype(np.float32) * 0.3)).astype(np.uint8)
    left_mix = ((left_color.astype(np.float32) * 0.65) + (border_color.astype(np.float32) * 0.35)).astype(np.uint8)
    right_mix = ((right_color.astype(np.float32) * 0.65) + (border_color.astype(np.float32) * 0.35)).astype(np.uint8)

    y = np.linspace(0.0, 1.0, height, dtype=np.float32).reshape(height, 1, 1)
    x = np.linspace(0.0, 1.0, width, dtype=np.float32).reshape(1, width, 1)
    vertical = (top_mix.astype(np.float32) * (1.0 - y)) + (bottom_mix.astype(np.float32) * y)
    horizontal = (left_mix.astype(np.float32) * (1.0 - x)) + (right_mix.astype(np.float32) * x)
    background = (vertical * 0.72) + (horizontal * 0.28)
    background = cv2.GaussianBlur(background, (0, 0), sigmaX=26, sigmaY=26)
    return np.clip(background, 0, 255).astype(np.uint8)


def build_vertical_canvas(image: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    fitted = resize_to_fit(image, TARGET_WIDTH, TARGET_HEIGHT)
    background = create_edge_gradient_background(image, TARGET_WIDTH, TARGET_HEIGHT)
    canvas = background.copy()
    artwork_mask = np.zeros((TARGET_HEIGHT, TARGET_WIDTH), dtype=np.uint8)

    y = (TARGET_HEIGHT - fitted.shape[0]) // 2
    x = (TARGET_WIDTH - fitted.shape[1]) // 2
    canvas[y : y + fitted.shape[0], x : x + fitted.shape[1]] = fitted
    artwork_mask[y : y + fitted.shape[0], x : x + fitted.shape[1]] = 255
    return canvas, background, artwork_mask


def quantize(image: np.ndarray, k: int) -> np.ndarray:
    pixels = image.reshape((-1, 3)).astype(np.float32)
    criteria = (
        cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
        30,
        0.8,
    )
    _compactness, labels, centers = cv2.kmeans(
        pixels,
        k,
        None,
        criteria,
        3,
        cv2.KMEANS_PP_CENTERS,
    )
    centers = np.uint8(centers)
    return centers[labels.flatten()].reshape(image.shape)


def blend(a: np.ndarray, b: np.ndarray, alpha: float) -> np.ndarray:
    return cv2.addWeighted(a, 1.0 - alpha, b, alpha, 0.0)


def save_stage(path: Path, image: np.ndarray):
    cv2.imwrite(str(path), image, [cv2.IMWRITE_JPEG_QUALITY, 96])


def composite_on_mask(base: np.ndarray, overlay: np.ndarray, mask: np.ndarray) -> np.ndarray:
    mask3 = mask[..., None]
    composed = base.astype(np.float32) * (1.0 - mask3) + overlay.astype(np.float32) * mask3
    return np.clip(composed, 0, 255).astype(np.uint8)


def stylize_art(image: np.ndarray, sigma: float, quant_k: int, blend_amount: float) -> np.ndarray:
    smoothed = cv2.bilateralFilter(image, d=0, sigmaColor=sigma, sigmaSpace=max(8, sigma))
    smoothed = cv2.GaussianBlur(smoothed, (0, 0), sigmaX=max(0.1, sigma * 0.35), sigmaY=max(0.1, sigma * 0.35))
    quantized = quantize(smoothed, quant_k)
    return blend(smoothed, quantized, blend_amount)


def create_background_base(final_image: np.ndarray, background: np.ndarray, artwork_mask: np.ndarray) -> np.ndarray:
    base = stylize_art(final_image, sigma=46, quant_k=4, blend_amount=0.82)
    mask3 = (artwork_mask.astype(np.float32) / 255.0)[..., None]
    return np.clip(background.astype(np.float32) * (1.0 - mask3) + base.astype(np.float32) * mask3, 0, 255).astype(np.uint8)


def create_stages(final_image: np.ndarray, background: np.ndarray, artwork_mask: np.ndarray, stage_count: int) -> list[np.ndarray]:
    base0 = create_background_base(final_image, background, artwork_mask)
    base1 = composite_on_mask(background, stylize_art(final_image, sigma=34, quant_k=5, blend_amount=0.78), artwork_mask.astype(np.float32) / 255.0)
    base2 = composite_on_mask(background, stylize_art(final_image, sigma=26, quant_k=6, blend_amount=0.72), artwork_mask.astype(np.float32) / 255.0)
    base3 = composite_on_mask(background, stylize_art(final_image, sigma=20, quant_k=7, blend_amount=0.66), artwork_mask.astype(np.float32) / 255.0)
    base4 = composite_on_mask(background, stylize_art(final_image, sigma=15, quant_k=8, blend_amount=0.58), artwork_mask.astype(np.float32) / 255.0)
    base5 = composite_on_mask(background, stylize_art(final_image, sigma=11, quant_k=10, blend_amount=0.50), artwork_mask.astype(np.float32) / 255.0)
    base6 = composite_on_mask(background, stylize_art(final_image, sigma=8, quant_k=12, blend_amount=0.42), artwork_mask.astype(np.float32) / 255.0)
    base7 = composite_on_mask(background, stylize_art(final_image, sigma=6, quant_k=14, blend_amount=0.34), artwork_mask.astype(np.float32) / 255.0)
    base8 = composite_on_mask(background, stylize_art(final_image, sigma=4, quant_k=16, blend_amount=0.26), artwork_mask.astype(np.float32) / 255.0)
    final_stage = blend(final_image, cv2.detailEnhance(final_image, sigma_s=8, sigma_r=0.12), 0.08)

    anchors = [base0, base1, base2, base3, base4, base5, base6, base7, base8, final_stage]
    if stage_count == len(anchors):
        return anchors
    if stage_count < 2:
        return [anchors[-1]]

    stages: list[np.ndarray] = []
    total_reference = len(anchors) - 1
    for index in range(stage_count):
        pos = (index / max(stage_count - 1, 1)) * total_reference
        left_idx = int(np.floor(pos))
        right_idx = min(left_idx + 1, total_reference)
        alpha = pos - left_idx
        stages.append(blend(anchors[left_idx], anchors[right_idx], alpha))

    stages[0] = anchors[0]
    stages[-1] = anchors[-1]
    return stages


def apply_timelapse_motion(frame: np.ndarray, progress: float) -> np.ndarray:
    h, w = frame.shape[:2]
    progress = float(np.clip(progress, 0.0, 1.0))
    eased = progress * progress * (3.0 - 2.0 * progress)

    zoom = 1.0 + (0.028 * eased)
    scaled = cv2.resize(
        frame,
        (int(round(w * zoom)), int(round(h * zoom))),
        interpolation=cv2.INTER_CUBIC,
    )
    max_x = max(0, scaled.shape[1] - w)
    max_y = max(0, scaled.shape[0] - h)
    offset_x = int(round(max_x * (0.20 + 0.45 * eased)))
    offset_y = int(round(max_y * (0.18 + 0.34 * eased)))
    moved = scaled[offset_y : offset_y + h, offset_x : offset_x + w]
    if moved.shape[:2] != (h, w):
        moved = cv2.resize(moved, (w, h), interpolation=cv2.INTER_CUBIC)
    return moved


def render_transition_frames(stages: list[np.ndarray], frames_dir: Path, total_frames: int):
    frames_dir.mkdir(parents=True, exist_ok=True)

    transitions = len(stages) - 1
    stage_weights = np.array(
        [0.50, 0.70, 0.75, 0.80, 0.95, 1.00, 1.00, 1.05, 1.10, 1.10, 1.15, 1.15, 1.20, 1.25, 1.25, 1.30, 1.35, 1.45, 1.70],
        dtype=np.float32,
    )
    if len(stage_weights) != transitions:
        stage_weights = np.ones(transitions, dtype=np.float32)
    cumulative = np.concatenate([[0.0], np.cumsum(stage_weights)])
    samples = np.linspace(0.0, cumulative[-1], total_frames, endpoint=False)

    for frame_index, sample in enumerate(samples):
        segment = int(np.searchsorted(cumulative, sample, side="right") - 1)
        segment = int(np.clip(segment, 0, transitions - 1))
        local_start = cumulative[segment]
        local_end = cumulative[segment + 1]
        alpha = 0.0 if local_end <= local_start else (sample - local_start) / (local_end - local_start)
        frame = blend(stages[segment], stages[segment + 1], alpha)
        progress = frame_index / max(total_frames - 1, 1)
        frame = apply_timelapse_motion(frame, progress)
        frame = cv2.GaussianBlur(frame, (0, 0), sigmaX=0.2, sigmaY=0.2)
        cv2.imwrite(
            str(frames_dir / f"frame_{frame_index:04d}.jpg"),
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 95],
        )

    final_frame = apply_timelapse_motion(stages[-1], 1.0)
    cv2.imwrite(
        str(frames_dir / f"frame_{total_frames:04d}.jpg"),
        final_frame,
        [cv2.IMWRITE_JPEG_QUALITY, 95],
    )


def encode_video(frames_dir: Path, fps: int, output_video: Path, ffmpeg_bin: str):
    cmd = [
        ffmpeg_bin,
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / "frame_%04d.jpg"),
        "-vf",
        "format=yuv420p",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        str(output_video),
    ]
    subprocess.run(cmd, check=True)


def list_input_images(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        return []
    return sorted(
        path
        for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def safe_stem(path: Path) -> str:
    sanitized = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in path.stem)
    return sanitized.strip("_") or "image"


def clear_matching_files(directory: Path, prefix: str):
    if not directory.exists():
        return
    for file_path in directory.glob(f"{prefix}*"):
        if file_path.is_file():
            file_path.unlink()


def process_image(
    image_path: Path,
    stages_dir: Path,
    frames_root: Path,
    videos_dir: Path,
    fps: int,
    duration: float,
    stage_count: int,
    keep_stages: bool,
    keep_frames: bool,
    stages_only: bool,
    ffmpeg_bin: str | None,
):
    base_name = safe_stem(image_path)
    frame_dir = frames_root / base_name
    video_path = videos_dir / f"{base_name}_video.mp4"

    stages_dir.mkdir(parents=True, exist_ok=True)
    if not stages_only:
        frames_root.mkdir(parents=True, exist_ok=True)
        videos_dir.mkdir(parents=True, exist_ok=True)
        if frame_dir.exists():
            shutil.rmtree(frame_dir)
        frame_dir.mkdir(parents=True, exist_ok=True)

    if not keep_stages:
        clear_matching_files(stages_dir, f"{base_name}_stage_")

    source = read_image(image_path)
    final_image, background, artwork_mask = build_vertical_canvas(source)
    stages = create_stages(final_image, background, artwork_mask, stage_count)

    for index, stage in enumerate(stages, start=1):
        save_stage(stages_dir / f"{base_name}_stage_{index:02d}.jpg", stage)

    if stages_only:
        print(f"Processed stages only: {image_path.name}")
        print(f"Stages saved to: {stages_dir}")
        return

    total_frames = max(2, int(round(duration * fps)) - 1)
    render_transition_frames(stages, frame_dir, total_frames)
    encode_video(frame_dir, fps, video_path, ffmpeg_bin)

    if not keep_frames and frame_dir.exists():
        shutil.rmtree(frame_dir)
    if not keep_stages:
        clear_matching_files(stages_dir, f"{base_name}_stage_")

    print(f"Processed: {image_path.name}")
    print(f"Video saved to: {video_path}")


def main():
    args = parse_args()
    ffmpeg_bin = None
    if not args.stages_only:
        ffmpeg_bin = ensure_ffmpeg(args.ffmpeg_bin)

    stages_dir = Path(args.stages_dir).resolve()
    frames_root = Path(args.frames_dir).resolve()
    videos_dir = Path(args.videos_dir).resolve()

    if args.input_image:
        image_paths = [Path(args.input_image).resolve()]
    else:
        image_paths = list_input_images(Path(args.input_dir).resolve())

    if not image_paths:
        raise FileNotFoundError(
            "No input images found. Use --input <file> or place jpg/jpeg/png files into the input folder."
        )

    for image_path in image_paths:
        process_image(
            image_path=image_path,
            stages_dir=stages_dir,
            frames_root=frames_root,
            videos_dir=videos_dir,
            fps=args.fps,
            duration=args.duration,
            stage_count=args.stage_count,
            keep_stages=args.keep_stages,
            keep_frames=args.keep_frames,
            stages_only=args.stages_only,
            ffmpeg_bin=ffmpeg_bin,
        )


if __name__ == "__main__":
    main()
