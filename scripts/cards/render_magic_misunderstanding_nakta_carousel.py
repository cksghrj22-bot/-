#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render magic misunderstanding nakta carousel."""

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
OUT = ROOT / "_out" / "매직_오해_낙타캐러셀"
W, H = 1080, 1350

# 슬라이드1: 줌 풀고 가운데(블러 배경으로 원본 통째 담기)
CONTAIN_BLUR = ("[0:v]split[a][b];[a]scale=1080:1350:force_original_aspect_ratio=increase,"
                "crop=1080:1350,boxblur=26:2,eq=brightness=-0.05[bg];"
                "[b]scale=1080:1350:force_original_aspect_ratio=decrease[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[base]")
# 슬라이드4: 줌+왼쪽 크롭으로 옆 남자스탭 얼굴 프레임에서 빼기
ZOOM_LEFT = "[0:v]scale=1700:-2,crop=1080:1350:0:640,setsar=1[base]"


@dataclass(frozen=True)
class Slide:
    n: int
    kind: str
    file: str | None
    top_text: str
    bottom_text: str | None
    bottom_role: str | None
    start: float
    duration: float
    text_top: float
    text_left: float
    crop_y: float
    top_size: int
    bottom_size: int
    base_vf: str | None = None
    pad_scale: float = 1.0
    mid_text: str | None = None
    mid_role: str | None = None
    mid_size: int = 0


SLIDES = [
    Slide(1, "video", "사랑해.MOV", "여름철 곱슬 때문에 힘드시죠?", None, None, 0.0, 4.0, 0.070, 0.050, 0.18, 66, 0),
    Slide(2, "video", "IMG_1092.MOV", "매직에 대한\n흔한 오해와 진실", "1탄", "시안", 17.0, 4.0, 0.520, 0.075, 0.16, 66, 44),
    Slide(3, "video", "밸런스베이지.MOV", "매직은 무조건 잘 펴는 거다?", "불필요한 곱슬을 찾는 거예요.", "결론", 1.2, 5.0, 0.090, 0.045, 0.05, 62, 44, mid_text="No!!", mid_role="노", mid_size=52),
    Slide(4, "kenburns", "IMG_0601.jpg", "전체매직, 뿌리매직만 있다?", "갯수가 수만 가지예요. 사람마다 다르니까요.", "시안", 0.0, 5.0, 0.045, 0.050, 0.08, 44, 32, pad_scale=0.45),
    Slide(5, "video", "IMG_1245.MOV", "곱슬은 무조건 나쁘다?", "착한 곱슬도 있어요.", "시안", 0.0, 4.0, 0.600, 0.055, 0.18, 58, 56),
]


def cover_crop(im: Image.Image, crop_y: float) -> Image.Image:
    im = ImageOps.exif_transpose(im).convert("RGB")
    scale = max(W / im.width, H / im.height)
    nw, nh = round(im.width * scale), round(im.height * scale)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, round((nw - W) / 2))
    top = max(0, round((nh - H) * crop_y))
    return im.crop((left, top, left + W, top + H))


def fit_font(text: str, size: int, x: int) -> ImageFont.FreeTypeFont:
    font_size = size
    while font_size > 30:
        fnt = nakta_post.F("NanumSquareRoundEB.ttf", font_size)
        bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), text, font=fnt)
        if x + (bb[2] - bb[0]) + 2 * nakta_post.PAD_X <= W - 36:
            return fnt
        font_size -= 2
    return nakta_post.F("NanumSquareRoundEB.ttf", font_size)


def make_overlay(slide: Slide) -> Path:
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    x0 = int(W * slide.text_left)
    y = int(H * slide.text_top)
    gap = 8 if slide.n == 4 else nakta_post.GAP
    step = 0 if slide.n == 4 else nakta_post.STEP
    lines = [("설정", text, slide.top_size) for text in slide.top_text.splitlines()]
    if slide.mid_text and slide.mid_role:
        lines.append((slide.mid_role, slide.mid_text, slide.mid_size))
    if slide.bottom_text and slide.bottom_role:
        lines.extend((slide.bottom_role, text, slide.bottom_size) for text in slide.bottom_text.splitlines())
    for i, (role, text, size) in enumerate(lines):
        _styles = {**nakta_post.STYLES, "노": ((214, 45, 45, 235), (255, 255, 255))}
        box, txt = _styles[role]
        bx = x0 + i * step
        fnt = fit_font(text, size, bx)
        bb = d.textbbox((0, 0), text, font=fnt)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        _px = int(nakta_post.PAD_X * slide.pad_scale)
        _py = int(nakta_post.PAD_Y * slide.pad_scale)
        bw = tw + 2 * _px
        bh = th + 2 * _py
        d.rectangle([bx, y, bx + bw, y + bh], fill=box)
        d.text((bx + _px - bb[0], y + _py - bb[1]), text, font=fnt, fill=txt)
        y += bh + gap
    path = OUT / "_overlays" / f"slide_{slide.n}_overlay.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    overlay.save(path)
    return path


def render_photo(slide: Slide) -> Path:
    if slide.file is None:
        raise ValueError(f"slide {slide.n} photo source is missing")
    base = cover_crop(Image.open(SRC / slide.file), slide.crop_y).convert("RGBA")
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
    fnt = fit_font(slide.top_text, slide.top_size, int(W * slide.text_left))
    bb = d.textbbox((0, 0), slide.top_text, font=fnt)
    x = int(W * slide.text_left)
    y = int(H * slide.text_top)
    d.text((x - bb[0], y - bb[1]), slide.top_text, font=fnt, fill=(255, 255, 255))
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
