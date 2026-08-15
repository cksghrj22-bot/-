#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render v3 5-card perm/dry nakta carousel.

Cloned from render_magic_misunderstanding_nakta_carousel.py and scoped to this
perm/dry B-roll mapping. Publishing is intentionally not part of this script.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import nakta_post


ROOT = SCRIPT_DIR.parents[1]
OUT = ROOT / "_out" / "펌_드라이_낙타_5장v3"
W, H = 1080, 1350

DOWNLOADS = ROOT / "_work" / "broll_drive_scan_20260811" / "downloads"


@dataclass(frozen=True)
class Slide:
    n: int
    src: Path
    lines: tuple[tuple[str, str], ...]
    start: float
    duration: float
    text_top: float
    text_left: float
    crop_y: float = 0.5
    crop_x: float = 0.5
    sizes: dict[str, int] | None = None
    pad_scale: float = 0.82
    gap_scale: float = 0.55
    step_scale: float = 0.45


SLIDES = [
    Slide(
        1,
        DOWNLOADS / "1wMX4Eqq79Wt0U71-QyebaEqo2g7JPs7O_IMG_2052.MP4",
        (
            ("설정", "이 머리는 펌 위에"),
            ("설정", "드라이를 한 모습이에요"),
        ),
        2.80,
        3.20,
        0.610,
        0.050,
        crop_x=0.50,
        crop_y=0.22,
        sizes={"설정": 42},
    ),
    Slide(
        2,
        DOWNLOADS / "1pLxEMsLQDxGMInQ8OyACJrHoP8GOT8sX_dce5e3a8631a47dcb51be1da82a065df.MOV",
        (
            ("설정", "펌은 드라이의 목적과 달리"),
            ("시안", "손질을 편하게 해주는 데 의의가 있어요"),
        ),
        0.00,
        4.00,
        0.600,
        0.035,
        crop_x=0.50,
        crop_y=0.36,
        sizes={"설정": 38, "시안": 34},
        step_scale=0.42,
    ),
    Slide(
        3,
        DOWNLOADS / "19q4mrsadQcDHzgx5VmV09tMb7j72KNGS_IMG_8183 2.MOV",
        (
            ("설정", "펌이 드라이와 같아지려는 순간"),
            ("시안", "오버하게 되고, 모발에 무리가 가요"),
        ),
        0.15,
        4.00,
        0.585,
        0.035,
        crop_x=0.58,
        crop_y=0.50,
        sizes={"설정": 38, "시안": 36},
        step_scale=0.38,
    ),
    Slide(
        4,
        DOWNLOADS / "1HUJzAlwO-9Ve9Yr-V5vqzP742yDxMLnU_IMG_0895.MOV",
        (
            ("설정", "맨 먼저 중요한 것은,"),
            ("설정", "펌의 한계를 명확히 하고"),
            ("시안", "처음 목적으로 돌아가는 거예요"),
        ),
        0.20,
        4.00,
        0.650,
        0.045,
        crop_x=0.42,
        crop_y=0.50,
        sizes={"설정": 39, "시안": 37},
        step_scale=0.42,
    ),
    Slide(
        5,
        DOWNLOADS / "1uwCVGxEsmcoLQNdbF_iwoB2HKbNjvqBp_IMG_1244.MOV",
        (
            ("설정", "펌을 드라이와 같이는 못해도,"),
            ("결론", "지금보다 나은 —"),
            ("시안", "손질 되는 머리로 보답드릴게요"),
        ),
        0.00,
        4.50,
        0.625,
        0.045,
        crop_x=0.50,
        crop_y=0.42,
        sizes={"설정": 38, "결론": 38, "시안": 36},
        step_scale=0.42,
    ),
]


def size_for(slide: Slide, role: str) -> int:
    return (slide.sizes or {}).get(role, 38)


def fit_font(text: str, size: int, x: int, pad_x: int) -> ImageFont.FreeTypeFont:
    font_size = size
    while font_size > 28:
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
    gap = int(nakta_post.GAP * slide.gap_scale)
    step = int(nakta_post.STEP * slide.step_scale)
    pad_x = int(nakta_post.PAD_X * slide.pad_scale)
    pad_y = int(nakta_post.PAD_Y * slide.pad_scale)

    for i, (role, text) in enumerate(slide.lines):
        box, txt = nakta_post.STYLES[role]
        bx = x0 + i * step
        fnt = fit_font(text, size_for(slide, role), bx, pad_x)
        bb = d.textbbox((0, 0), text, font=fnt)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        bw = tw + 2 * pad_x
        bh = th + 2 * pad_y
        d.rectangle([bx, y, bx + bw, y + bh], fill=box)
        d.text((bx + pad_x - bb[0], y + pad_y - bb[1]), text, font=fnt, fill=txt)
        y += bh + gap

    path = OUT / "_overlays" / f"slide_{slide.n}_overlay.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    overlay.save(path)
    return path


def render_video(slide: Slide) -> Path:
    if not slide.src.exists():
        raise FileNotFoundError(f"slide {slide.n} source missing: {slide.src}")
    overlay = make_overlay(slide)
    out = OUT / f"slide_{slide.n}.mp4"
    x_expr = f"(iw-ow)*{slide.crop_x:.4f}"
    y_expr = f"(ih-oh)*{slide.crop_y:.4f}"
    vf = (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H}:{x_expr}:{y_expr},setsar=1[base];"
        "[base][1:v]overlay=0:0:format=auto,format=yuv420p[v]"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{slide.start:.3f}",
        "-t",
        f"{slide.duration:.3f}",
        "-i",
        str(slide.src),
        "-i",
        str(overlay),
        "-filter_complex",
        vf,
        "-map",
        "[v]",
        "-an",
        "-c:v",
        "libx264",
        "-crf",
        "18",
        "-preset",
        "veryfast",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    targets = {int(arg) for arg in sys.argv[1:]} if len(sys.argv) > 1 else {s.n for s in SLIDES}
    for n in targets:
        for old in OUT.glob(f"slide_{n}.*"):
            if old.is_file():
                old.unlink()
    rendered = []
    for slide in SLIDES:
        if slide.n in targets:
            rendered.append(render_video(slide))
    for path in rendered:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
