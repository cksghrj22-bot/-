#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render the confirmed magic nakta carousel."""

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
OUT = ROOT / "_out" / "매직_낙타캐러셀"
W, H = 1080, 1350


@dataclass(frozen=True)
class Slide:
    n: int
    kind: str
    file: str
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


SLIDES = [
    Slide(1, "video", "IMG_1092.MOV", "매직은 무조건 잘 펴는 것?", None, None, 0.0, 4.0, 0.12, 0.055, 0.20, 66, 44),
    Slide(2, "photo", "IMG_0415.jpg", "고유명사처럼 굳었을 뿐이고,", "안에 시술이 무수히 많거든요.", "결론", 0.0, 0.0, 0.70, 0.055, 0.45, 58, 44),
    Slide(3, "video", "IMG_1244.MOV", "뿌리매직 아니면 전체매직···?", "겉만, 라인만, 30%만, 10%만.", "시안", 0.0, 4.5, 0.075, 0.055, 0.18, 56, 42),
    Slide(4, "photo", "KakaoTalk_Photo_2023-05-19-12-08-51 008.jpeg", "잘 펴는 게 매직인가···?", "불편한 데를 펴는 겁니다.", "결론", 0.0, 0.0, 0.13, 0.055, 0.33, 58, 46),
    Slide(5, "video", "IMG_1245.MOV", "곱슬은 무조건 없애야 하나···?", "착한 곱슬은 오히려 볼륨을 채워주고 있어요.", "시안", 0.0, 4.1, 0.10, 0.045, 0.22, 52, 38),
    Slide(6, "video", "IMG_0709.MOV", "너네 내 사진첩에···?", "왜 자꾸 나오니.", "시안", 0.0, 4.0, 0.09, 0.44, 0.16, 56, 46),
]


def cover_crop(im: Image.Image, crop_y: float) -> Image.Image:
    im = ImageOps.exif_transpose(im).convert("RGB")
    scale = max(W / im.width, H / im.height)
    nw, nh = round(im.width * scale), round(im.height * scale)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, round((nw - W) / 2))
    top = max(0, round((nh - H) * crop_y))
    return im.crop((left, top, left + W, top + H))


def make_overlay(slide: Slide) -> Path:
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    x0 = int(W * slide.text_left)
    y = int(H * slide.text_top)
    lines = [("설정", slide.top_text, slide.top_size)]
    if slide.bottom_text and slide.bottom_role:
        lines.append((slide.bottom_role, slide.bottom_text, slide.bottom_size))
    for i, (role, text, size) in enumerate(lines):
        box, txt = nakta_post.STYLES[role]
        bx = x0 + i * nakta_post.STEP
        fnt = fit_font(text, size, bx)
        bb = d.textbbox((0, 0), text, font=fnt)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        bw = tw + 2 * nakta_post.PAD_X
        bh = th + 2 * nakta_post.PAD_Y
        d.rectangle([bx, y, bx + bw, y + bh], fill=box)
        d.text((bx + nakta_post.PAD_X - bb[0], y + nakta_post.PAD_Y - bb[1]), text, font=fnt, fill=txt)
        y += bh + nakta_post.GAP
    path = OUT / "_overlays" / f"slide_{slide.n}_overlay.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    overlay.save(path)
    return path


def fit_font(text: str, size: int, x: int) -> ImageFont.FreeTypeFont:
    font_size = size
    while font_size > 30:
        fnt = nakta_post.F("NanumSquareRoundEB.ttf", font_size)
        bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), text, font=fnt)
        if x + (bb[2] - bb[0]) + 2 * nakta_post.PAD_X <= W - 36:
            return fnt
        font_size -= 2
    return nakta_post.F("NanumSquareRoundEB.ttf", font_size)


def render_photo(slide: Slide) -> Path:
    base = cover_crop(Image.open(SRC / slide.file), slide.crop_y).convert("RGBA")
    overlay = Image.open(make_overlay(slide)).convert("RGBA")
    out = OUT / f"slide_{slide.n}.jpg"
    Image.alpha_composite(base, overlay).convert("RGB").save(out, quality=92, optimize=True)
    return out


def render_video(slide: Slide) -> Path:
    overlay = make_overlay(slide)
    out = OUT / f"slide_{slide.n}.mp4"
    y_expr = f"(ih-oh)*{slide.crop_y:.4f}"
    vf = (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H}:(iw-ow)/2:{y_expr},setsar=1[base];"
        f"[base][1:v]overlay=0:0:format=auto,format=yuv420p[v]"
    )
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-ss", f"{slide.start:.3f}", "-t", f"{slide.duration:.3f}",
        "-i", str(SRC / slide.file),
        "-i", str(overlay),
        "-filter_complex", vf,
        "-map", "[v]",
        "-an",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-movflags", "+faststart",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rendered = []
    for slide in SLIDES:
        rendered.append(render_video(slide) if slide.kind == "video" else render_photo(slide))
    for path in rendered:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
