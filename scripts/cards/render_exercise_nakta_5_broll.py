#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""운동 낙타 자막바 5장 — B롤 영상 캐러셀 (1080x1350 / 4초 / 무음).
카피: content/nakta/조여가기준비/subtitles.ass 차노 원본 7줄 그대로.
규격: scripts/cards/nakta_post.py 실값 (font58 / PAD 22·16 / GAP 49 / STEP 46 / STYLES).
"""
from __future__ import annotations
import subprocess, sys, json
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageDraw

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import nakta_post

ROOT = SCRIPT_DIR.parents[1]
SRC = ROOT / "_tmp" / "nakta_broll_downloads"
OUT = ROOT / "_out" / "운동_낙타_5장__N"
FFMPEG, FFPROBE = "ffmpeg", "ffprobe"
W, H = nakta_post.W, nakta_post.H


@dataclass(frozen=True)
class Slide:
    n: int
    src: str
    label: str
    lines: tuple
    start: float
    duration: float
    top: float
    left: float
    crop_y: float = 0.46


SLIDES = (
    Slide(1, "1wFuo7aO4M99ojcBHV1A7sfGWaOetOkMW_IMG_1174.MOV", "IMG_1174 / 한강 새벽 러닝",
          (("설정", "죽지 않으려고 하는 것"),
           ("결론", "약해져가는 나를 보면서 아쉬움에 하는 것")), 2.0, 4.0, 0.07, 0.055),
    Slide(2, "1N0TTvQsmF7gmQmgNuHZLuIHe-zAk9WAq_temp_video_1782487588019.mp4", "temp_video / 메디신볼",
          (("설정", "쓸데없이 고민할 바에는"),
           ("시안", "그냥 뛰자, 로 하는 것")), 38.0, 4.0, 0.045, 0.045),
    Slide(3, "1TrGVeIBz6oVJRRBEagrIiH-zYoq0epWU_IMG_2644.MOV", "IMG_2644 / 덤벨 세팅",
          (("설정", "영감이 어딘가 떨어지길 기도하다"),
           ("결론", "마지막에 하는 것")), 0.0, 4.0, 0.040, 0.060, crop_y=0.0),
    Slide(4, "1FAVAdAZ979OJzioA7sXn-77y_VCocGbm_IMG_2139.MOV", "IMG_2139 / 핸드스탠드",
          (("설정", "그나마 내 삶 중에"),
           ("결론", "쉬운 난이도라 하는 것")), 24.0, 4.0, 0.790, 0.130),
    Slide(5, "1HnQLaWOf_6xqwZ3VIoA3k-TzIpOgQTNa_IMG_1496.MOV", "IMG_1496 / 수영",
          (("설정", "그냥 오기로 하는 것"),
           ("시안", "수영은 박태환을 상상하며 하는 것")), 3.0, 4.0, 0.62, 0.05),
)


def make_overlay(s: Slide) -> Path:
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    x0, y = int(W * s.left), int(H * s.top)
    for i, (role, text) in enumerate(s.lines):
        x = x0 + i * nakta_post.STEP
        box, txt = nakta_post.STYLES[role]
        fnt = nakta_post._fit_font(text, role, 58, x)
        bb = d.textbbox((0, 0), text, font=fnt)
        bw = bb[2] - bb[0] + 2 * nakta_post.PAD_X
        bh = bb[3] - bb[1] + 2 * nakta_post.PAD_Y
        d.rectangle([x, y, x + bw, y + bh], fill=box)
        d.text((x + nakta_post.PAD_X - bb[0], y + nakta_post.PAD_Y - bb[1]), text, font=fnt, fill=txt)
        y += bh + nakta_post.GAP
    p = OUT / "_overlays" / f"slide_{s.n}_overlay.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    ov.save(p)
    return p


VF_BASE = ("scale={w}:{h}:force_original_aspect_ratio=increase,"
           "crop={w}:{h}:(iw-ow)*0.5:(ih-oh)*{cy:.4f},setsar=1")


def render(s: Slide) -> Path:
    src = SRC / s.src
    if not src.exists():
        raise FileNotFoundError(src)
    ov = make_overlay(s)
    out = OUT / f"slide_{s.n}.mp4"
    base = VF_BASE.format(w=W, h=H, cy=s.crop_y)
    vf = f"[0:v]{base}[b];[b][1:v]overlay=0:0:format=auto,fps=30,format=yuv420p[v]"
    subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                    "-ss", f"{s.start:.3f}", "-t", f"{s.duration + 0.2:.3f}", "-i", str(src),
                    "-i", str(ov), "-filter_complex", vf, "-map", "[v]", "-an", "-frames:v", "120",
                    "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)], check=True)
    # 검수 프레임 (중간)
    rv = OUT / "_review"; rv.mkdir(parents=True, exist_ok=True)
    subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
                    "-ss", f"{s.duration/2:.2f}", "-i", str(out), "-frames:v", "1",
                    "-q:v", "3", str(rv / f"slide_{s.n}_mid.jpg")], check=True)
    return out


def probe(p: Path) -> dict:
    v = subprocess.check_output([FFPROBE, "-v", "error", "-select_streams", "v:0",
                                 "-show_entries", "stream=width,height,avg_frame_rate,nb_frames,duration",
                                 "-of", "json", p.as_posix()], text=True)
    a = subprocess.check_output([FFPROBE, "-v", "error", "-select_streams", "a",
                                 "-show_entries", "stream=index", "-of", "csv=p=0", p.as_posix()], text=True)
    d = json.loads(v)["streams"][0]
    d["audio_streams"] = len([x for x in a.strip().split("\n") if x])
    return d


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    want = [int(x) for x in sys.argv[1:]] or [s.n for s in SLIDES]
    for s in SLIDES:
        if s.n in want:
            p = render(s)
            print(f"slide_{s.n}  {s.label}  ->  {probe(p)}")
