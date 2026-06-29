import os
import sys
import re
import subprocess
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

if hasattr(sys, '_MEIPASS'):
    FFMPEG_PATH = os.path.join(sys._MEIPASS, "ffmpeg.exe")
else:
    FFMPEG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ffmpeg.exe")
_current_process = None


def _format_eta(seconds: int) -> str:
    h, rem = divmod(max(0, seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m}m {s}s" if h else f"{m}m {s}s" if m else f"{s}s"


def get_source_frame(input_path: str) -> Image.Image:
    cap = cv2.VideoCapture(input_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / 2))
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return Image.new('RGB', (1920, 1080), color='black')

    return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))


def _calculate_dynamic_crop(top_space: int) -> tuple:
    target_game_h = int(max(608, 1440 - top_space))
    crop_w = int(1080 * 1080 / target_game_h)
    crop_w -= crop_w % 2
    crop_x = (1920 - crop_w) // 2
    crop_x -= crop_x % 2
    return crop_w, crop_x, target_game_h


def generate_preview(input_path: str, cam_coords: tuple, use_webcam: bool = True, use_subs: bool = True,
                     use_title: bool = False, title_text: str = "") -> Image.Image:
    cap = cv2.VideoCapture(input_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / 2))
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return Image.new('RGB', (1080, 1920), color='black')

    bg_w = int(frame.shape[1] * 1920 / frame.shape[0])
    bg = cv2.resize(frame, (bg_w, 1920))
    start_x = (bg_w - 1080) // 2
    bg_cropped = bg[:, start_x:start_x + 1080]
    bg_blur = cv2.GaussianBlur(bg_cropped, (99, 99), 0)

    cam_h_scaled = 0
    if use_webcam:
        x, y, w, h = cam_coords
        cam_crop = frame[y:y + h, x:x + w]
        cam_h_scaled = min(800, int(h * 1080 / w) if w > 0 else 0)
        if cam_h_scaled > 0:
            cam_resized = cv2.resize(cam_crop, (1080, cam_h_scaled))
            bg_blur[0:cam_h_scaled, 0:1080] = cam_resized

    top_space = cam_h_scaled if use_webcam else 600

    crop_w, crop_x, target_game_h = _calculate_dynamic_crop(top_space)
    game_crop = frame[:, crop_x:crop_x + crop_w]
    game_resized = cv2.resize(game_crop, (1080, target_game_h))
    bg_blur[top_space:top_space + target_game_h, 0:1080] = game_resized

    pil_img = Image.fromarray(cv2.cvtColor(bg_blur, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)

    try:
        font = ImageFont.truetype("impact.ttf", 90)
        title_font = ImageFont.truetype("impact.ttf", 110)
    except:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    if not use_webcam and use_title and title_text:
        text = title_text.upper()
        bbox = draw.textbbox((0, 0), text, font=title_font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = (1080 - tw) // 2
        ty = 250 - (th // 2)

        for adj_x in range(-4, 5):
            for adj_y in range(-4, 5):
                draw.text((tx + adj_x, ty + adj_y), text, font=title_font, fill="black")
        draw.text((tx, ty), text, font=title_font, fill="white")

    if use_subs:
        bottom_space = 1920 - (top_space + target_game_h)
        margin_v = max(80, int(bottom_space / 3))

        text = "SUBTITLES HERE"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = (1080 - tw) // 2
        ty = 1920 - margin_v - th

        for adj_x in range(-3, 4):
            for adj_y in range(-3, 4):
                draw.text((tx + adj_x, ty + adj_y), text, font=font, fill="black")
        draw.text((tx, ty), text, font=font, fill="white")

    return pil_img


def create_short(input_path: str, output_path: str, cam_coords: tuple, ass_path: str = "", use_webcam: bool = True,
                 title_ass_path: str = "", progress_cb=None):
    global _current_process
    cap = cv2.VideoCapture(input_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    cam_h_scaled = 0
    if use_webcam:
        x, y, w, h = cam_coords
        cam_h_scaled = min(800, int(h * 1080 / w) if w > 0 else 0)

    top_space = cam_h_scaled if use_webcam else 600
    crop_w, crop_x, target_game_h = _calculate_dynamic_crop(top_space)

    bottom_space = 1920 - (top_space + target_game_h)
    margin_v = max(80, int(bottom_space / 3))

    if use_webcam:
        filter_complex = (
            "[0:v]scale=-1:1920,crop=1080:1920,boxblur=20:5[bg];"
            f"[0:v]crop={w}:{h}:{x}:{y},scale=1080:-1[cam];"
            f"[0:v]crop={crop_w}:1080:{crop_x}:0,scale=1080:-1[game];"
            "[bg][cam]overlay=0:0[tmp];"
            f"[tmp][game]overlay=0:{top_space}[v1]"
        )
    else:
        filter_complex = (
            "[0:v]scale=-1:1920,crop=1080:1920,boxblur=20:5[bg];"
            f"[0:v]crop={crop_w}:1080:{crop_x}:0,scale=1080:-1[game];"
            f"[bg][game]overlay=0:{top_space}[v1]"
        )

    out_map = "[v1]"

    if title_ass_path and not use_webcam:
        title_escaped = os.path.abspath(title_ass_path).replace('\\', '/').replace(':', '\\:')
        filter_complex += f";{out_map}subtitles='{title_escaped}'[v2]"
        out_map = "[v2]"

    if ass_path:
        ass_escaped = os.path.abspath(ass_path).replace('\\', '/').replace(':', '\\:')
        style = f"FontName=Impact,FontSize=90,Alignment=2,MarginV={margin_v},Outline=3,Shadow=0"
        filter_complex += f";{out_map}subtitles='{ass_escaped}':force_style='{style}'[v3]"
        out_map = "[v3]"

    cmd = [
        FFMPEG_PATH, "-y", "-i", input_path, "-filter_complex", filter_complex,
        "-map", out_map, "-map", "0:a", "-c:v", "libx264", "-preset", "fast",
        "-crf", "23", "-c:a", "aac", output_path
    ]

    _current_process = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace',
                                        creationflags=0x08000000)

    for line in _current_process.stderr:
        if progress_cb and total_frames > 0:
            match = re.search(r"frame=\s*(\d+).*fps=\s*([\d\.]+)", line)
            if match:
                frame, fps = int(match.group(1)), max(float(match.group(2)), 1.0)
                p = min(frame / total_frames, 1.0)
                eta_sec = int((total_frames - frame) / fps)
                progress_cb(p, f"Rendering: {int(p * 100)}% (ETA: {_format_eta(eta_sec)})")

    _current_process.wait()
    _current_process = None


def cancel_render():
    if _current_process is not None:
        _current_process.kill()