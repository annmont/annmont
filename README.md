# Art Video Insta

Python tools for preparing artwork photos and generating vertical timelapse-style videos for short-form social content.

## What Is In This Repo

This repository contains several experimental scripts for turning a finished painting/photo of a painting into a vertical video that imitates a drawing or painting process.

Current main utility scripts:

- `extract_painting.py`
  Extracts only the painting/canvas from a source photo so you can review crop quality separately before generating video.
- `draw_process_video.py`
  Generates a vertical `1080x1920` video from one image using staged simplification/detail restoration.
- `timelapse.py`
  A simpler rule-based timelapse prototype.
- `painting_timelapse_v2.py`
  An alternative pipeline intended to work with PaintTransformer.

## Recommended Workflow

1. Put source photos into `in/`
2. Run `extract_painting.py`
3. Check crop quality in `cut_paintings/`
4. Use the cropped result in a video-generation script if needed

This keeps the crop/segmentation step independent from the video step, which is useful for quality control.

## Project Structure

```text
Art video Insta/
├── in/                     # source images
├── cut_paintings/          # cropped paintings
├── cut_paintings_debug/    # optional crop debug outputs
├── output_videos/          # generated videos
├── temp_frames/            # temporary rendered frames
├── temp_stages/            # temporary stage images
├── PaintTransformer/       # optional external painting-model pipeline
├── extract_painting.py
├── draw_process_video.py
├── timelapse.py
├── painting_timelapse_v2.py
└── requirements.txt
```

## Requirements

- Windows 10/11
- Python 3.10+
- `ffmpeg` available in PATH or passed explicitly to scripts that export MP4

Install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Script: extract_painting.py

Purpose:
- detect the painting/canvas in a photo
- crop it out
- save it as a separate image

Single file:

```powershell
python extract_painting.py --input "in\trace #06.jpg"
```

Batch mode:

```powershell
python extract_painting.py
```

With debug output:

```powershell
python extract_painting.py --input "in\trace #06.jpg" --debug-dir cut_paintings_debug
```

Output:
- cropped files go to `cut_paintings/`
- debug masks/previews go to `cut_paintings_debug/`

## Script: draw_process_video.py

Purpose:
- build a vertical timelapse-style video from one finished image
- save intermediate stages
- export final MP4

Example:

```powershell
python draw_process_video.py --input "in\trace #06.jpg" --stage-count 20 --ffmpeg-bin "C:\path\to\ffmpeg.exe"
```

## Notes About The Repo

- This repo currently mixes several experimental approaches.
- Some scripts are prototypes and may need cleanup before production use.
- Generated outputs and temporary files should not be committed to GitHub.
- Large model files such as `.pth` weights should usually be distributed separately or via release assets/cloud storage.

## Suggested GitHub Positioning

Good repository description:

> Tools for extracting paintings from photos and generating vertical timelapse-style art videos in Python.

Suggested tags:

- `python`
- `opencv`
- `ffmpeg`
- `timelapse`
- `art`
- `video-generation`
- `image-processing`

## Next Cleanup Ideas

- separate stable scripts from experiments
- move generated outputs fully out of the repo or ignore them
- add example input/output screenshots or GIF previews
- document which script is currently the preferred pipeline
