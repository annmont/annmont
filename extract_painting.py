import argparse
from pathlib import Path

import cv2
import numpy as np


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract the painting/canvas from a photo and save the crop."
    )
    parser.add_argument(
        "--input",
        dest="input_image",
        help="Path to one source image.",
    )
    parser.add_argument(
        "--input-dir",
        default="in",
        help="Directory with source images for batch processing.",
    )
    parser.add_argument(
        "--output-dir",
        default="cut_paintings",
        help="Directory for cropped painting images.",
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=18,
        help="Extra pixels around the detected painting.",
    )
    parser.add_argument(
        "--debug-dir",
        default=None,
        help="Optional directory to save debug masks and previews.",
    )
    return parser.parse_args()


def read_image(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return image


def safe_stem(path: Path) -> str:
    sanitized = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in path.stem)
    return sanitized.strip("_") or "image"


def list_input_images(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        return []
    return sorted(
        path
        for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def detect_painting_mask(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Try both dark-on-light and light-on-dark assumptions.
    otsu_inv = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    candidates = [otsu_inv, otsu]
    best_mask = None
    best_area = -1
    image_area = image.shape[0] * image.shape[1]

    kernel_close = np.ones((11, 11), np.uint8)
    kernel_open = np.ones((5, 5), np.uint8)

    for candidate in candidates:
        cleaned = cv2.morphologyEx(candidate, cv2.MORPH_CLOSE, kernel_close, iterations=2)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel_open, iterations=1)

        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < image_area * 0.08:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            rect_area = w * h
            fill_ratio = area / max(rect_area, 1)
            if fill_ratio < 0.45:
                continue

            mask = np.zeros_like(gray)
            cv2.drawContours(mask, [contour], -1, 255, thickness=-1)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close, iterations=2)

            if area > best_area:
                best_area = area
                best_mask = mask

    if best_mask is not None:
        return best_mask

    # Fallback: GrabCut with a centered rectangle.
    h, w = image.shape[:2]
    rect = (
        int(w * 0.08),
        int(h * 0.08),
        int(w * 0.84),
        int(h * 0.84),
    )
    grabcut_mask = np.zeros((h, w), np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    cv2.grabCut(image, grabcut_mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
    result_mask = np.where(
        (grabcut_mask == cv2.GC_FGD) | (grabcut_mask == cv2.GC_PR_FGD),
        255,
        0,
    ).astype(np.uint8)
    result_mask = cv2.morphologyEx(result_mask, cv2.MORPH_CLOSE, kernel_close, iterations=2)
    return result_mask


def crop_from_mask(image: np.ndarray, mask: np.ndarray, padding: int) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    ys, xs = np.where(mask > 0)
    if len(xs) == 0 or len(ys) == 0:
        raise RuntimeError("Painting was not detected in the image.")

    h, w = image.shape[:2]
    x0 = max(0, int(xs.min()) - padding)
    y0 = max(0, int(ys.min()) - padding)
    x1 = min(w, int(xs.max()) + padding + 1)
    y1 = min(h, int(ys.max()) + padding + 1)

    return image[y0:y1, x0:x1].copy(), (x0, y0, x1, y1)


def save_debug(debug_dir: Path, stem: str, image: np.ndarray, mask: np.ndarray, bbox: tuple[int, int, int, int]):
    debug_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(debug_dir / f"{stem}_mask.png"), mask)

    preview = image.copy()
    x0, y0, x1, y1 = bbox
    cv2.rectangle(preview, (x0, y0), (x1 - 1, y1 - 1), (0, 255, 0), 4)
    cv2.imwrite(str(debug_dir / f"{stem}_preview.jpg"), preview, [cv2.IMWRITE_JPEG_QUALITY, 95])


def process_one(image_path: Path, output_dir: Path, padding: int, debug_dir: Path | None):
    image = read_image(image_path)
    mask = detect_painting_mask(image)
    crop, bbox = crop_from_mask(image, mask, padding)

    output_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_stem(image_path)
    output_path = output_dir / f"{stem}_painting.png"
    cv2.imwrite(str(output_path), crop)

    if debug_dir is not None:
        save_debug(debug_dir, stem, image, mask, bbox)

    print(f"Processed: {image_path.name}")
    print(f"Saved: {output_path}")


def main():
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    debug_dir = Path(args.debug_dir).resolve() if args.debug_dir else None

    if args.input_image:
        image_paths = [Path(args.input_image).resolve()]
    else:
        image_paths = list_input_images(Path(args.input_dir).resolve())

    if not image_paths:
        raise FileNotFoundError(
            "No input images found. Use --input <file> or place images into the input folder."
        )

    for image_path in image_paths:
        process_one(
            image_path=image_path,
            output_dir=output_dir,
            padding=args.padding,
            debug_dir=debug_dir,
        )


if __name__ == "__main__":
    main()
