"""
painting_timelapse_v2.py
========================
Генерирует таймлапс рисования картины через Paint Transformer.

Структура проекта:
    C:\\AIpr\\Art video Insta\\
        in\\                  ← сюда кладёшь картины
        output_videos\\       ← сюда сохраняются видео
        PaintTransformer\\inference\\PaintTransformerPT\\inference\\
            inference_run.py  ← Paint Transformer
            model.pth         ← модель

Использование в Claude Code:
    python painting_timelapse_v2.py --input "trace #06.jpg"
    python painting_timelapse_v2.py --input "моя_картина.jpg" --fps 24 --duration 10
"""

import cv2
import numpy as np
import os
import sys
import glob
import shutil
import subprocess
import argparse

# ── Пути ─────────────────────────────────────────────────────
BASE_DIR       = r"C:\AIpr\Art video Insta"
INPUT_DIR      = os.path.join(BASE_DIR, "in")
OUTPUT_DIR     = os.path.join(BASE_DIR, "output_videos")
PT_DIR         = os.path.join(BASE_DIR, "PaintTransformer", "inference",
                               "PaintTransformerPT", "inference")
PT_SCRIPT      = os.path.join(PT_DIR, "inference_run.py")

# ── Параметры видео ───────────────────────────────────────────
FPS       = 24
DURATION  = 10   # секунд
FW, FH    = 1080, 1920


def crop_canvas(img):
    """Вырезает холст из фото — убирает белый/серый фон."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY_INV)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, np.ones((15,15), np.uint8))
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print("  Фон не найден — используем всё изображение")
        return img
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    x, y, w, h = cv2.boundingRect(contours[0])
    print(f"  Холст найден: {w}×{h} px (из {img.shape[1]}×{img.shape[0]})")
    return img[y:y+h, x:x+w]


def letterbox(src, tw, th, bg=(255, 255, 255)):
    """Вписывает изображение в кадр с сохранением пропорций."""
    hh, ww = src.shape[:2]
    sc = min(tw/ww, th/hh)
    nw, nh = int(ww*sc), int(hh*sc)
    r = cv2.resize(src, (nw, nh), interpolation=cv2.INTER_LANCZOS4)
    c = np.full((th, tw, 3), bg, dtype=np.uint8)
    y0, x0 = (th-nh)//2, (tw-nw)//2
    c[y0:y0+nh, x0:x0+nw] = r
    return c


def run_paint_transformer(input_path, frames_dir):
    """Запускает Paint Transformer и возвращает папку с кадрами."""
    print("  Запускаю Paint Transformer...")
    os.makedirs(frames_dir, exist_ok=True)

    result = subprocess.run(
        ["python", PT_SCRIPT],
        capture_output=True, text=True,
        cwd=PT_DIR
    )

    if result.returncode != 0:
        print("  ОШИБКА:")
        print(result.stderr[-1000:])
        return None

    print("  Paint Transformer готов")
    return frames_dir


def build_video(frames_dir, output_path, canvas_final):
    """Собирает видео из кадров + финальный кадр оригинала."""
    # Находим кадры
    frames = sorted(glob.glob(os.path.join(frames_dir, "*.jpg")))
    if not frames:
        frames = sorted(glob.glob(os.path.join(frames_dir, "*.png")))

    if not frames:
        print("  Кадры не найдены!")
        return False

    print(f"  Кадров: {len(frames)}")

    # Читаем первый кадр для размера
    first = cv2.imread(frames[0])
    fh, fw = first.shape[:2]

    total_frames = FPS * DURATION
    hold_end     = FPS * 2  # 2 сек финального кадра
    paint_frames = total_frames - hold_end

    wr = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), FPS, (FW, FH))

    # Растягиваем кадры Paint Transformer на paint_frames
    for i in range(paint_frames):
        idx = int(i / paint_frames * len(frames))
        idx = min(idx, len(frames)-1)
        frame = cv2.imread(frames[idx])
        # Меняем чёрный фон на белый
        mask = (frame[:,:,0] < 10) & (frame[:,:,1] < 10) & (frame[:,:,2] < 10)
        frame[mask] = [255, 255, 255]
        # Вписываем в вертикальный кадр
        frame_lb = letterbox(frame, FW, FH)
        wr.write(frame_lb)

    # Плавный переход в оригинал
    last_frame = cv2.imread(frames[-1])
    last_frame[mask] = [255, 255, 255]
    last_lb = letterbox(last_frame, FW, FH)
    orig_lb  = letterbox(canvas_final, FW, FH)

    for i in range(hold_end):
        t = i / hold_end
        t = t*t*(3-2*t)
        frame = cv2.addWeighted(orig_lb, t, last_lb, 1-t, 0)
        wr.write(frame)

    wr.release()
    print(f"  ✅ Видео: {output_path}")
    return True


def process(input_filename, fps=FPS, duration=DURATION):
    """Основная функция — обрабатывает одну картину."""
    input_path = os.path.join(INPUT_DIR, input_filename)

    if not os.path.exists(input_path):
        print(f"❌ Файл не найден: {input_path}")
        return

    name = os.path.splitext(input_filename)[0]
    print(f"\n🎨 Обрабатываю: {input_filename}")

    # 1. Загружаем и вырезаем холст
    print("1. Вырезаю холст...")
    img = cv2.imread(input_path)
    canvas = crop_canvas(img)

    # Сохраняем вырезанный холст для Paint Transformer
    temp_input = os.path.join(PT_DIR, "input", "canvas.jpg")
    os.makedirs(os.path.dirname(temp_input), exist_ok=True)
    cv2.imwrite(temp_input, canvas)

    # 2. Обновляем inference_run.py с правильными путями
    print("2. Настраиваю Paint Transformer...")
    frames_dir = os.path.join(OUTPUT_DIR, name)
    os.makedirs(frames_dir, exist_ok=True)

    with open(os.path.join(PT_DIR, "inference_run.py"), "r") as f:
        code = f.read()

    # Обновляем пути в скрипте
    import re
    code = re.sub(
        r"main\(input_path=.*?\)",
        f"main(input_path='input/canvas.jpg', "
        f"model_path='model.pth', "
        f"output_dir=r'{frames_dir}', "
        f"need_animation=True, "
        f"resize_h=512, resize_w=512, serial=True)",
        code, flags=re.DOTALL
    )

    with open(os.path.join(PT_DIR, "inference_run.py"), "w") as f:
        f.write(code)

    # 3. Запускаем Paint Transformer
    print("3. Генерирую мазки (3-5 мин)...")
    result = subprocess.run(
        ["python", "inference_run.py"],
        capture_output=True, text=True, cwd=PT_DIR
    )

    if result.returncode != 0:
        print("❌ Ошибка Paint Transformer:")
        print(result.stderr[-500:])
        return

    # 4. Собираем видео
    print("4. Собираю видео...")
    output_path = os.path.join(OUTPUT_DIR, f"{name}_timelapse.mp4")
    build_video(frames_dir, output_path, canvas)

    print(f"\n✅ Готово! Видео: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Painting timelapse generator")
    parser.add_argument("--input", "-i", required=True,
                        help="Имя файла картины в папке 'in' (например: trace #06.jpg)")
    parser.add_argument("--fps",      type=int, default=24)
    parser.add_argument("--duration", type=int, default=10)
    args = parser.parse_args()

    process(args.input, args.fps, args.duration)
