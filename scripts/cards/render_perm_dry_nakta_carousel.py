#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render perm/dry nakta carousel stills."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import nakta_post


ROOT = SCRIPT_DIR.parents[1]
SRC = ROOT / "_clips_job" / "magic" / "_pick6"
OUT = ROOT / "_out" / "펌_드라이_낙타캐러셀"
W, H = 1080, 1350


@dataclass(frozen=True)
class Slide:
    n: int
    file: str
    role: str
    text: str
    text_top: float
    text_left: float
    crop_x: float
    crop_y: float
    zoom: float
    size: int


SLIDES = [
    Slide(
        1,
        "01_중단발_IMG1092.jpg",
        "설정",
        "펌은 드라이처럼 만드는 거다…?",
        0.620,
        0.050,
        0.45,
        0.26,
        1.035,
        72,
    ),
    Slide(
        2,
        "06_웃는포트레이트_사랑해.jpg",
        "결론",
        "아니요, 당신의 드라이를 편하게 하려는 거예요.",
        0.790,
        0.055,
        0.50,
        0.12,
        1.025,
        44,
    ),
    Slide(
        3,
        "03_단발_IMG8571.jpg",
        "설정",
        "깨끗한 C컬 하러 왔는데…?",
        0.105,
        0.050,
        0.51,
        0.05,
        1.030,
        64,
    ),
    Slide(
        4,
        "02_긴생머리_IMG4393.jpg",
        "시안",
        "사진처럼 똑같이 이것저것 넣으면, 안 한 것보다 못해져요.",
        0.720,
        0.045,
        0.49,
        0.20,
        1.040,
        43,
    ),
    Slide(
        5,
        "04_발레아쥬_밸런스베이지.jpg",
        "설정",
        "그럼 편한 머리는 어떻게 나올까요?",
        0.115,
        0.055,
        0.50,
        0.08,
        1.030,
        58,
    ),
    Slide(
        6,
        "05_완성포트레이트_IMG1245.jpg",
        "시안",
        "한계를 인정하고 그 안에서 최대치. 그래야 손질 편한 머리가 돼요.",
        0.610,
        0.050,
        0.47,
        0.15,
        1.035,
        39,
    ),
]


def cover_crop(im: Image.Image, crop_x: float, crop_y: float, zoom: float) -> Image.Image:
    im = ImageOps.exif_transpose(im).convert("RGB")
    scale = max(W / im.width, H / im.height) * zoom
    nw, nh = round(im.width * scale), round(im.height * scale)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, min(nw - W, round((nw - W) * crop_x)))
    top = max(0, min(nh - H, round((nh - H) * crop_y)))
    return im.crop((left, top, left + W, top + H))


def fit_font(text: str, role: str, size: int, x: int) -> ImageFont.FreeTypeFont:
    font_size = size
    while font_size > 30:
        fnt = nakta_post.F("NanumSquareRoundEB.ttf", font_size)
        bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), text, font=fnt)
        if x + (bb[2] - bb[0]) + 2 * nakta_post.PAD_X <= W - 36:
            return fnt
        font_size -= 1
    return nakta_post.F("NanumSquareRoundEB.ttf", font_size)


def draw_bar(base: Image.Image, slide: Slide) -> Image.Image:
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    x = int(W * slide.text_left)
    y = int(H * slide.text_top)
    box, txt = nakta_post.STYLES[slide.role]
    fnt = fit_font(slide.text, slide.role, slide.size, x)
    bb = d.textbbox((0, 0), slide.text, font=fnt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    bw = tw + 2 * nakta_post.PAD_X
    bh = th + 2 * nakta_post.PAD_Y
    d.rectangle([x, y, x + bw, y + bh], fill=box)
    d.text((x + nakta_post.PAD_X - bb[0], y + nakta_post.PAD_Y - bb[1]), text=slide.text, font=fnt, fill=txt)
    return Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")


def render_slide(slide: Slide) -> Path:
    base = cover_crop(Image.open(SRC / slide.file), slide.crop_x, slide.crop_y, slide.zoom)
    out = OUT / f"slide_{slide.n}.jpg"
    draw_bar(base, slide).save(out, quality=92, optimize=True)
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    targets = {int(arg) for arg in sys.argv[1:]} if len(sys.argv) > 1 else {slide.n for slide in SLIDES}
    rendered = []
    for n in targets:
        old = OUT / f"slide_{n}.jpg"
        if old.exists():
            old.unlink()
    for slide in SLIDES:
        if slide.n in targets:
            rendered.append(render_slide(slide))
    for path in rendered:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
