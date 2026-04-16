"""
timelapse.py
============
Генерирует видео-таймлапс "процесса рисования" из готовой картины.

Использование:
    python3 timelapse.py моя_картина.jpg

Требования:
    pip install opencv-python

Выходной файл:
    моя_картина_timelapse.mp4
"""

import cv2
import numpy as np
import sys
import os

# ── Параметры ────────────────────────────────────────────────
FPS       = 24
HOLD_SEC  = 0.15   # пауза на каждой стадии
FADE_SEC  = 0.35   # длина перехода между стадиями
N_STAGES  = 20     # количество стадий
FW, FH    = 1080, 1920  # размер видео (вертикальное)


def letterbox(src, tw, th):
    """Вписывает картину в кадр с сохранением пропорций."""
    h, w = src.shape[:2]
    sc = min(tw / w, th / h)
    nw, nh = int(w * sc), int(h * sc)
    r = cv2.resize(src, (nw, nh), interpolation=cv2.INTER_LANCZOS4)
    c = np.full((th, tw, 3), (20, 18, 16), dtype=np.uint8)
    y0, x0 = (th - nh) // 2, (tw - nw) // 2
    c[y0:y0+nh, x0:x0+nw] = r
    return c


def build_stages(canvas):
    """Строит 5 опорных стадий по цветовым зонам."""
    hsv  = cv2.cvtColor(canvas, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    h, w = canvas.shape[:2]

    # Зоны по цвету
    m_dark  = (gray < 55)
    m_green = (hsv[:,:,0]>35)&(hsv[:,:,0]<85)&(hsv[:,:,1]>40)&(gray<120)
    m_blue  = (hsv[:,:,0]>85)&(hsv[:,:,0]<130)&(hsv[:,:,1]>50)&(gray>60)
    m_white = (gray > 180)

    # 5 стадий накопительно
    s0 = np.full((h,w,3), (20,18,16), dtype=np.uint8)  # чистый холст

    s1 = s0.copy()
    s1[m_dark] = canvas[m_dark]                          # + тёмный фон

    s2 = s1.copy()
    s2[m_green] = canvas[m_green]                        # + ваза/зелень

    s3 = s2.copy()
    s3[m_blue] = canvas[m_blue]                          # + основные цветы

    s4 = s3.copy()
    s4[m_white] = canvas[m_white]                        # + блики

    s5 = canvas.copy()                                   # оригинал

    return [s0, s1, s2, s3, s4, s5]


def interpolate(img_a, img_b, t):
    """Плавный crossfade между двумя кадрами."""
    t = t * t * (3 - 2 * t)  # smoothstep
    return cv2.addWeighted(img_b, t, img_a, 1 - t, 0)


def generate_video(input_path):
    # Загружаем картину
    img = cv2.imread(input_path)
    if img is None:
        print(f"Ошибка: не могу открыть {input_path}")
        sys.exit(1)

    print(f"Картина: {img.shape[1]}×{img.shape[0]}")

    canvas = letterbox(img, FW, FH)
    print(f"Холст: {FW}×{FH}")

    # 5 опорных стадий
    keyframes = build_stages(canvas)

    # Раскладываем 5 стадий на N_STAGES равномерно
    # Пропорции: фон быстро (2), ваза (3), цветы (7), блики (5), финал (3)
    checkpoints = [
        (keyframes[0], keyframes[1],  0,  2),
        (keyframes[1], keyframes[2],  2,  5),
        (keyframes[2], keyframes[3],  5, 12),
        (keyframes[3], keyframes[4], 12, 17),
        (keyframes[4], keyframes[5], 17, 20),
    ]

    stages = []
    for si in range(N_STAGES):
        for (img_a, img_b, s_start, s_end) in checkpoints:
            if s_start <= si < s_end:
                t = (si - s_start) / (s_end - s_start)
                stages.append(interpolate(img_a, img_b, t))
                break
    stages.append(canvas.copy())  # последняя стадия = оригинал

    print(f"Стадий: {len(stages)}")

    # Анимация: crossfade между стадиями
    hold_f = max(1, int(FPS * HOLD_SEC))
    fade_f = max(1, int(FPS * FADE_SEC))

    frames = []
    for i, stage in enumerate(stages):
        for _ in range(hold_f):
            frames.append(stage)
        if i < len(stages) - 1:
            nxt = stages[i + 1]
            for fi in range(fade_f):
                t = fi / fade_f
                frames.append(interpolate(stage, nxt, t))

    total = len(frames)
    duration = total / FPS
    print(f"Кадров: {total} ({duration:.1f} сек)")

    # Сохраняем видео
    base = os.path.splitext(input_path)[0]
    out_path = base + "_timelapse.mp4"

    wr = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*'mp4v'), FPS, (FW, FH))
    for i, f in enumerate(frames):
        wr.write(f)
        if i % (FPS * 2) == 0:
            p = i * 100 // total
            bar = "█" * (p // 5) + "░" * (20 - p // 5)
            print(f"  [{bar}] {p}%", end="\r", flush=True)
    wr.release()

    print(f"\n✅ Готово: {out_path}")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python3 timelapse.py моя_картина.jpg")
        sys.exit(1)

    generate_video(sys.argv[1])
