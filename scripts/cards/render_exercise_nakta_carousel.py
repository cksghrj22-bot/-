#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render 1080x1350 exercise nakta carousel clips."""

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
DRIVE = Path.home() / "Library/CloudStorage/GoogleDrive-cksghrj22@gmail.com/내 드라이브"
SRC = DRIVE / "운동"
OUT = ROOT / "_out" / "운동_낙타캐러셀_정본_20260813"
FFMPEG = Path("/Applications/Creator OS.app/Contents/Resources/vendor/ffmpeg/ffmpeg")
FFPROBE = Path("/Applications/Creator OS.app/Contents/Resources/vendor/ffmpeg/ffprobe")
W, H = nakta_post.W, nakta_post.H


@dataclass(frozen=True)
class Slide:
    n: int
    src: Path
    lines: tuple[tuple[str, str], ...]
    start: float
    duration: float
    top: float
    left: float
    crop_x: float = 0.5
    crop_y: float = 0.5


SLIDES = (
    Slide(
        1,
        SRC / "IMG_1174.MOV",
        (
            ("설정", "멈추면 다시 시작하기 어려워"),
            ("결론", "그래서 천천히라도 계속 간다"),
        ),
        2.0,
        4.0,
        0.08,
        0.07,
        crop_y=0.46,
    ),
    Slide(
        2,
        SRC / "IMG_2644.MOV",
        (
            ("설정", "힘들면 쉬어도 돼"),
            ("시안", "대신 포기는 하지 마"),
        ),
        0.0,
        4.0,
        0.18,
        0.08,
        crop_y=0.46,
    ),
)


def fit_font(text: str, role: str, x: int) -> ImageFont.FreeTypeFont:
    return nakta_post._fit_font(text, role, 58, x)


def make_overlay(slide: Slide) -> Path:
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    x0 = int(W * slide.left)
    y = int(H * slide.top)
    for i, (role, text) in enumerate(slide.lines):
        x = x0 + i * nakta_post.STEP
        box, txt = nakta_post.STYLES[role]
        fnt = fit_font(text, role, x)
        bb = d.textbbox((0, 0), text, font=fnt)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        bw = tw + 2 * nakta_post.PAD_X
        bh = th + 2 * nakta_post.PAD_Y
        d.rectangle([x, y, x + bw, y + bh], fill=box)
        d.text(
            (x + nakta_post.PAD_X - bb[0], y + nakta_post.PAD_Y - bb[1]),
            text,
            font=fnt,
            fill=txt,
        )
        y += bh + nakta_post.GAP
    path = OUT / "_overlays" / f"slide_{slide.n}_overlay.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    overlay.save(path)
    return path


def render_reference_frame(slide: Slide) -> Path:
    frame = OUT / "_review" / f"slide_{slide.n}_source.jpg"
    rendered = OUT / "_review" / f"slide_{slide.n}_rendered.jpg"
    frame.parent.mkdir(parents=True, exist_ok=True)
    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H}:(iw-ow)*{slide.crop_x:.4f}:(ih-oh)*{slide.crop_y:.4f},setsar=1"
    )
    subprocess.run(
        [
            str(FFMPEG),
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{slide.start + 0.4:.3f}",
            "-i",
            str(slide.src),
            "-frames:v",
            "1",
            "-vf",
            vf,
            "-q:v",
            "2",
            str(frame),
        ],
        check=True,
    )
    nakta_post.render(Image.open(frame), slide.lines, str(rendered), top=slide.top, left=slide.left)
    return rendered


def render_video(slide: Slide) -> Path:
    if not slide.src.exists():
        raise FileNotFoundError(slide.src)
    overlay = make_overlay(slide)
    out = OUT / f"slide_{slide.n}.mp4"
    vf = (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H}:(iw-ow)*{slide.crop_x:.4f}:(ih-oh)*{slide.crop_y:.4f},"
        "setsar=1[base];"
        "[base][1:v]overlay=0:0:format=auto,format=yuv420p[v]"
    )
    subprocess.run(
        [
            str(FFMPEG),
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
        ],
        check=True,
    )
    return out


def probe(path: Path) -> str:
    return subprocess.check_output(
        [
            str(FFPROBE),
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,avg_frame_rate,duration",
            "-of",
            "csv=p=0",
            str(path),
        ],
        text=True,
    ).strip()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rendered = []
    for slide in SLIDES:
        render_reference_frame(slide)
        rendered.append(render_video(slide))
    for path in rendered:
        print(path)
        print(probe(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
