#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""운동 낙타 자막바 6장 v2 — 표지 + 5장, 각 5초, 글자 위계 적용.
차노 지시(2026-08-13): 표지 「나에게 운동이란?」 맨앞 / 첫장 멘트 2·3으로 분리 /
4번 문장 「영감이 떨어지면 채우려고 마지막에 하는것」으로 교정 / 컷 지정 / 5초 / 글자 작게.
글자 위계 정본: knowledge/규격_낙타형자막바_컨텐츠_정본.md 「글자 크기 위계 개정2」
"""
from __future__ import annotations
import subprocess, sys, json
from dataclasses import dataclass, field
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import nakta_post

ROOT = SCRIPT_DIR.parents[1]
SRC = ROOT / "_tmp" / "nakta_broll_downloads"
OUT = ROOT / "_out" / "운동_낙타_5장_v2__N"
W, H = nakta_post.W, nakta_post.H

RUN   = "1wFuo7aO4M99ojcBHV1A7sfGWaOetOkMW_IMG_1174.MOV"
GYM   = "1N0TTvQsmF7gmQmgNuHZLuIHe-zAk9WAq_temp_video_1782487588019.mp4"
HAND  = "1FAVAdAZ979OJzioA7sXn-77y_VCocGbm_IMG_2139.MOV"
SWIM  = "1HnQLaWOf_6xqwZ3VIoA3k-TzIpOgQTNa_IMG_1496.MOV"
BIKE  = "IMG_2683.MOV"   # 짐 에어바이크(형광 연두티) — 2026-08-14 신규
TRACK = "VID_20260626_074320_153_16_16.mp4"   # 형광조끼 트랙 러닝 (본진 수급 완료)


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
    sizes: dict = field(default_factory=lambda: {"설정": 44, "결론": 34, "시안": 36})
    pad_scale: float = 0.82
    gap_scale: float = 0.55
    step_scale: float = 0.45


SLIDES = (
    # 1 = 표지. 트랙(형광) 영상 오면 src=TRACK 으로 교체. 지금은 임시로 한강 러닝.
    Slide(1, TRACK, "표지 — 형광조끼 트랙 러닝 80~85s (자막 하단)",
          (("설정", "미용 13년차에게"),
           ("결론", "운동이란?")), 80.0, 5.0, 0.680, 0.450,
          sizes={"설정": 44, "결론": 58}),
    Slide(11, TRACK, "표지안B — 116~121s (자막 상단)",
          (("설정", "미용 13년차에게"),
           ("결론", "운동이란?")), 116.0, 5.0, 0.045, 0.055,
          sizes={"설정": 44, "결론": 58}),
    # 2번 = (구)3번 슬라이드 통째로 이동 — 차노 지시 2026-08-14
    Slide(2, GYM, "temp_video 5~10s / 형광티 스쿼트  ←(구)3번",
          (("설정", "약해져가는 나를 보면서 아쉬움에 하는 것"),
           ("결론", "그나마 내 삶 중에 쉬운 난이도라 하는 것")), 5.0, 5.0, 0.030, 0.045),
    # 3번 = 신규 클립 IMG_2683(에어바이크) + (구)2번 자막
    Slide(3, BIKE, "IMG_2683 33~38s / 에어바이크(형광 연두티)  ←신규",
          (("설정", "죽지 않으려고 하는 것"),
           ("시안", "쓸데없이 고민할 바에는 그냥 뛰자")), 33.0, 5.0, 0.720, 0.050),
    Slide(4, HAND, "IMG_2139 20~25s / 물구나무 팔굽혀펴기",
          (("설정", "영감이 떨어지면 채우려고 마지막에 하는것"),
           ("결론", "그냥 오기로 하는 것")), 20.0, 5.0, 0.800, 0.100),
    Slide(5, SWIM, "IMG_1496 11~16s / 평영 뒷모습(더 뒤)",
          (("시안", "수영은 박태환을 상상하며 하는 것"),), 11.0, 5.0, 0.780, 0.055,
          sizes={"시안": 44}),
)


def fit_font(text, size, x, pad_x):
    fs = size
    while fs > 26:
        f = nakta_post.F("NanumSquareRoundEB.ttf", fs)
        bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), text, font=f)
        if x + (bb[2] - bb[0]) + 2 * pad_x <= W - 36:
            return f
        fs -= 2
    return nakta_post.F("NanumSquareRoundEB.ttf", fs)


def make_overlay(s: Slide) -> Path:
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    gap = int(nakta_post.GAP * s.gap_scale)
    step = int(nakta_post.STEP * s.step_scale)
    px = int(nakta_post.PAD_X * s.pad_scale)
    py = int(nakta_post.PAD_Y * s.pad_scale)
    x0, y = int(W * s.left), int(H * s.top)
    for i, (role, text) in enumerate(s.lines):
        box, txt = nakta_post.STYLES[role]
        bx = x0 + i * step
        f = fit_font(text, s.sizes.get(role, 34), bx, px)
        bb = d.textbbox((0, 0), text, font=f)
        bw, bh = bb[2] - bb[0] + 2 * px, bb[3] - bb[1] + 2 * py
        d.rectangle([bx, y, bx + bw, y + bh], fill=box)
        d.text((bx + px - bb[0], y + py - bb[1]), text, font=f, fill=txt)
        y += bh + gap
    p = OUT / "_overlays" / f"slide_{s.n}_overlay.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    ov.save(p)
    return p


def render(s: Slide) -> Path:
    src = SRC / s.src
    if not src.exists():
        raise FileNotFoundError(src)
    ov = make_overlay(s)
    out = OUT / f"slide_{s.n}.mp4"
    vf = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H}:(iw-ow)*0.5:(ih-oh)*{s.crop_y:.4f},setsar=1[b];"
          "[b][1:v]overlay=0:0:format=auto,fps=30,format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-ss", f"{s.start:.3f}", "-t", f"{s.duration + 0.2:.3f}", "-i", str(src),
                    "-i", str(ov), "-filter_complex", vf, "-map", "[v]", "-an",
                    "-frames:v", str(int(s.duration * 30)),
                    "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)], check=True)
    rv = OUT / "_review"; rv.mkdir(parents=True, exist_ok=True)
    for t in (0.2, s.duration / 2, s.duration - 0.2):
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.2f}",
                        "-i", str(out), "-frames:v", "1", "-q:v", "4",
                        str(rv / f"s{s.n}_{t:.1f}.jpg")], check=True)
    return out


def probe(p: Path) -> str:
    v = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,avg_frame_rate,nb_frames,duration", "-of", "json",
        str(p)], text=True))["streams"][0]
    a = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "a",
        "-show_entries", "stream=index", "-of", "csv=p=0", str(p)], text=True).strip()
    return (f"{v['width']}x{v['height']} {v['avg_frame_rate']} "
            f"{float(v['duration']):.3f}s {v['nb_frames']}f audio={len([x for x in a.split(chr(10)) if x])}")


def run_gate() -> int:
    """렌더가 끝나면 게이트를 반드시 통과해야 한다. 건너뛰기 금지."""
    g = SCRIPT_DIR / "nakta_gate.py"
    print("\n" + "=" * 60)
    r = subprocess.run([sys.executable, str(g), str(OUT)])
    if r.returncode != 0:
        print("\n[게이트 탈락] 이건 산출물이 아니다. 고치고 다시 렌더할 것.")
    return r.returncode


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    want = [int(x) for x in sys.argv[1:]] or [s.n for s in SLIDES]
    for s in SLIDES:
        if s.n not in want:
            continue
        try:
            print(f"slide_{s.n}  {s.label}  ->  {probe(render(s))}")
        except FileNotFoundError as e:
            print(f"slide_{s.n}  대기: {e.args[0].name}")
    raise SystemExit(run_gate())
