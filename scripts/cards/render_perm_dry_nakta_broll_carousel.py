#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render perm/dry nakta carousel with fresh B-roll only."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import nakta_post


ROOT = SCRIPT_DIR.parents[1]
SRC = ROOT / "_clips_job" / "magic"
OUT = ROOT / "_out" / "펌_드라이_낙타_B롤"
W, H = 1080, 1350


@dataclass(frozen=True)
class Slide:
    n: int
    kind: str
    file: str | None
    lines: tuple[tuple[str, str], ...]
    start: float
    duration: float
    text_top: float
    text_left: float
    crop_y: float
    size: int | dict[str, int]
    base_vf: str | None = None
    pad_scale: float = 1.0
    frame_time: float | None = None
    step_scale: float = 1.0


SLIDES = [
    Slide(1, "video", "IMG_8571.MOV", (
        ("설정", "이 머리, 드라이 안 한 것 같죠?"),
        ("결론", "사실 제가 드라이 한 거예요."),
        ("결론", "다들 '안 한 척' 올리지만,"),
        ("시안", "저는 드라이했다고 말해요."),
    ), 0.2, 4.0, 0.585, 0.025, 0.06, {"설정": 54, "결론": 42, "시안": 46}, step_scale=0.18),
    Slide(2, "photo_frame", "IMG_8565 2.MOV", (
        ("설정", "그럼 펌은 이 드라이처럼 만드는 걸까요?"),
        ("결론", "아니에요. 펌은 머리를 '만드는' 게 아니라,"),
        ("시안", "당신의 드라이를 '편하게' 해주는 거예요."),
    ), 0.0, 0.0, 0.555, 0.045, 0.16, {"설정": 42, "결론": 35, "시안": 34}, frame_time=3.2, step_scale=0.45),
    Slide(3, "video", "IMG_5853.MOV", (
        ("설정", "근데 펌엔 한계가 있어요."),
        ("결론", "무시하고 다 만들려다 오버하면"),
        ("결론", "툭 했을 때보다 못해져요."),
        ("결론", "깨끗한 C컬만 하면 될 걸"),
        ("결론", "'사진처럼 똑같이' 넣으면 어색해지죠."),
        ("시안", "오버는, 한계를 인정 안 해서 생겨요."),
    ), 3.8, 4.8, 0.070, 0.405, 0.08, {"설정": 42, "결론": 30, "시안": 30}, pad_scale=0.72, step_scale=0.20),
    Slide(4, "photo_frame", "IMG_1244.MOV", (
        ("설정", "그래서 어떻게 해야 편할까요?"),
        ("결론", "펌의 한계를 인정하고"),
        ("결론", "그 안에서 최대치를 해드려야,"),
        ("시안", "집에서 손질이 편한 머리가 나와요."),
    ), 0.0, 0.0, 0.055, 0.050, 0.02, {"설정": 43, "결론": 36, "시안": 35}, frame_time=2.8, step_scale=0.35),
    Slide(5, "video", "IMG_8221 4.MOV", (
        ("설정", "왜 그렇게까지 할까요?"),
        ("결론", "펌은 결국 당신 손질을 편하게 하는 게"),
        ("결론", "첫 번째니까요."),
        ("시안", "당신 펌은, 사진을 따라간 건가요"),
        ("시안", "당신 아침을 편하게 한 건가요?"),
    ), 4.0, 4.8, 0.585, 0.045, 0.08, {"설정": 46, "결론": 32, "시안": 33}, pad_scale=0.80, step_scale=0.30),
]


def cover_crop(im: Image.Image, crop_y: float) -> Image.Image:
    im = ImageOps.exif_transpose(im).convert("RGB")
    scale = max(W / im.width, H / im.height)
    nw, nh = round(im.width * scale), round(im.height * scale)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, round((nw - W) / 2))
    top = max(0, round((nh - H) * crop_y))
    return im.crop((left, top, left + W, top + H))


def role_size(size: int | dict[str, int], role: str) -> int:
    if isinstance(size, dict):
        return size.get(role, size.get("default", 44))
    return size


def fit_font(text: str, size: int | dict[str, int], role: str, x: int, pad_x: int) -> ImageFont.FreeTypeFont:
    font_size = role_size(size, role)
    while font_size > 30:
        fnt = nakta_post.F("NanumSquareRoundEB.ttf", font_size)
        bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), text, font=fnt)
        if x + (bb[2] - bb[0]) + 2 * pad_x <= W - 36:
            return fnt
        font_size -= 2
    return nakta_post.F("NanumSquareRoundEB.ttf", font_size)


def make_overlay(slide: Slide) -> Path:
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    x0 = int(W * slide.text_left)
    y = int(H * slide.text_top)
    gap = int(nakta_post.GAP * slide.pad_scale)
    step = int(nakta_post.STEP * slide.pad_scale * slide.step_scale)
    for i, (role, text) in enumerate(slide.lines):
        box, txt = nakta_post.STYLES[role]
        bx = x0 + i * step
        _px = int(nakta_post.PAD_X * slide.pad_scale)
        _py = int(nakta_post.PAD_Y * slide.pad_scale)
        fnt = fit_font(text, slide.size, role, bx, _px)
        bb = d.textbbox((0, 0), text, font=fnt)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        bw = tw + 2 * _px
        bh = th + 2 * _py
        d.rectangle([bx, y, bx + bw, y + bh], fill=box)
        d.text((bx + _px - bb[0], y + _py - bb[1]), text, font=fnt, fill=txt)
        y += bh + gap
    path = OUT / "_overlays" / f"slide_{slide.n}_overlay.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    overlay.save(path)
    return path


def capture_frame(slide: Slide) -> Image.Image:
    if slide.file is None or slide.frame_time is None:
        raise ValueError(f"slide {slide.n} frame source is missing")
    tmp = OUT / "_frames" / f"slide_{slide.n}_frame.jpg"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-ss", f"{slide.frame_time:.3f}",
        "-i", str(SRC / slide.file),
        "-frames:v", "1",
        "-q:v", "2",
        str(tmp),
    ]
    subprocess.run(cmd, check=True)
    return Image.open(tmp)


def render_photo(slide: Slide, frame: Image.Image | None = None) -> Path:
    if slide.file is None:
        raise ValueError(f"slide {slide.n} photo source is missing")
    src = frame if frame is not None else Image.open(SRC / slide.file)
    base = cover_crop(src, slide.crop_y).convert("RGBA")
    overlay = Image.open(make_overlay(slide)).convert("RGBA")
    out = OUT / f"slide_{slide.n}.jpg"
    Image.alpha_composite(base, overlay).convert("RGB").save(out, quality=92, optimize=True)
    return out


def render_video(slide: Slide) -> Path:
    if slide.file is None:
        raise ValueError(f"slide {slide.n} video source is missing")
    overlay = make_overlay(slide)
    out = OUT / f"slide_{slide.n}.mp4"
    y_expr = f"(ih-oh)*{slide.crop_y:.4f}"
    base = slide.base_vf or (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H}:(iw-ow)/2:{y_expr},setsar=1[base]"
    )
    vf = base + ";[base][1:v]overlay=0:0:format=auto,format=yuv420p[v]"
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-ss", f"{slide.start:.3f}", "-t", f"{slide.duration:.3f}",
        "-i", str(SRC / slide.file),
        "-i", str(overlay),
        "-filter_complex", vf,
        "-map", "[v]",
        "-an",
        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
        "-movflags", "+faststart",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    return out


def render_black(slide: Slide) -> Path:
    im = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    text = slide.lines[0][1]
    fnt = fit_font(text, slide.size, slide.lines[0][0], int(W * slide.text_left), nakta_post.PAD_X)
    bb = d.textbbox((0, 0), text, font=fnt)
    x = int(W * slide.text_left)
    y = int(H * slide.text_top)
    d.text((x - bb[0], y - bb[1]), text, font=fnt, fill=(255, 255, 255))
    out = OUT / f"slide_{slide.n}.jpg"
    im.save(out, quality=95, optimize=True)
    return out


def render_kenburns(slide: Slide) -> Path:
    if slide.file is None:
        raise ValueError(f"slide {slide.n} kenburns source is missing")
    overlay = make_overlay(slide)
    out = OUT / f"slide_{slide.n}.mp4"
    cy = slide.crop_y
    base = (
        f"[0:v]scale=2160:2700:force_original_aspect_ratio=increase,"
        f"crop=2160:2700:(iw-ow)/2:(ih-oh)*{cy:.4f},"
        f"zoompan=z='min(1.0+0.0016*on,1.24)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1350:fps=30,setsar=1[base]"
    )
    vf = base + ";[base][1:v]overlay=0:0:format=auto,format=yuv420p[v]"
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-framerate", "30", "-loop", "1", "-t", f"{slide.duration:.3f}",
        "-i", str(SRC / slide.file),
        "-i", str(overlay),
        "-filter_complex", vf,
        "-map", "[v]", "-an",
        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
        "-pix_fmt", "yuv420p", "-profile:v", "main", "-g", "60",
        "-movflags", "+faststart",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    targets = {int(arg) for arg in sys.argv[1:]} if len(sys.argv) > 1 else {slide.n for slide in SLIDES}
    for n in targets:
        for old in OUT.glob(f"slide_{n}.*"):
            if old.is_file():
                old.unlink()
    rendered = []
    for slide in SLIDES:
        if slide.n not in targets:
            continue
        if slide.kind == "video":
            rendered.append(render_video(slide))
        elif slide.kind == "photo":
            rendered.append(render_photo(slide))
        elif slide.kind == "photo_frame":
            rendered.append(render_photo(slide, capture_frame(slide)))
        elif slide.kind == "kenburns":
            rendered.append(render_kenburns(slide))
        elif slide.kind == "black":
            rendered.append(render_black(slide))
        else:
            raise ValueError(f"unknown slide kind: {slide.kind}")
    for path in rendered:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
