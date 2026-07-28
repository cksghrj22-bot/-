#!/usr/bin/env python3
"""볼륨매직 S2(쇼츠 올린 정본)의 도식에 '네이프'만 얹는 수술적 패치.

형 2026-07-28: "쇼츠에 올린 S2(실사+도식+실사)가 제일 좋았고, 거기 도식 애니에서
네이프만 빠졌으니 그것만 추가하라." → S2를 통째로 다시 만들지 않고(순수 애니 재빌드는
오답), S2 원본 위에 네이프(주황) 박스+호+연결선만 오버레이하고 오디오는 그대로 둔다.

- 입력: S2 완성본 mp4(실사+도식+실사, 도식 구간 ~13.5~22.2s), 도식 원 위치는 프레임에서 검출.
- 네이프: 톱10/페이스30/백15 옆에 네이프 70%(형 구술값) 하단 추가. 도식 끝 ~2.4s 페이드인.
- 실사·나레이션·BGM·길이 전부 원본 유지(-map 0:a -c:a copy).

사용: python3 -m shorts.patch_nape <s2.mp4> <out.mp4> [--nape-pct 70] [--enable 19.8,22.25]
"""
import argparse, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

NS = "/root/.fonts/nsqr_eb.ttf"
ORG = (255, 140, 60); WH = (235, 238, 245)


def _detect_circle(frame_png: str):
    """도식 프레임에서 두상 원의 (cx, cy, r) 검출. 좌우(중앙행)+하단 밝은 스트로크 기준."""
    img = Image.open(frame_png).convert("RGB"); px = img.load()
    def bright(x, y):
        r, g, b = px[x, y]; return (r + g + b) > 430
    xs = [x for x in range(150, 930) if bright(x, 915)]
    left, right = min(xs), max(xs); cx = (left + right) // 2; r = (right - left) // 2
    ys = [y for y in range(700, 1285) if bright(cx, y)]
    bottom = max(ys); cy = bottom - r
    return cx, cy, r


def _nape_frames(fdir: Path, cx: int, cy: int, r: int, pct: int, dur=2.45, fps=30):
    fdir.mkdir(parents=True, exist_ok=True)
    L, T, R, B = cx - r, cy - r, cx + r, cy + r
    fl = ImageFont.truetype(NS, 34); fp = ImageFont.truetype(NS, 60); fm = ImageFont.truetype(NS, 22)
    def ease(t): t = max(0, min(1, t)); return t * t * (3 - 2 * t)
    N = int(dur * fps)
    for i in range(N):
        t = i / fps; fade = ease(t / 0.45); cnt = int(pct * ease(t / 0.7)); A = int(255 * fade)
        ov = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        oc = lambda c, a=A: (c[0], c[1], c[2], a)
        d.arc([L, T, R, B], 74, 106, fill=oc(ORG), width=10)
        d.line([(cx, B), (cx, B + 20)], fill=oc(ORG), width=3)
        d.ellipse([cx - 7, B - 7, cx + 7, B + 7], fill=oc(ORG))
        bw, bh = 430, 124; bx0 = cx - bw // 2; by0 = B + 20
        d.rounded_rectangle([bx0, by0, bx0 + bw, by0 + bh], radius=16,
                            fill=(20, 22, 28, int(240 * fade)), outline=oc(ORG), width=3)
        d.text((bx0 + 24, by0 + 14), "네이프라인", font=fl, fill=oc(WH))
        d.text((bx0 + 24, by0 + 54), f"{cnt}%", font=fp, fill=oc(ORG))
        d.text((bx0 + 250, by0 + 24), "펴는 정도", font=fm, fill=(150, 155, 165, A))
        d.rounded_rectangle([bx0 + 250, by0 + 66, bx0 + 380, by0 + 82], radius=8, fill=(60, 64, 72, A))
        d.rounded_rectangle([bx0 + 250, by0 + 66, bx0 + 250 + int(130 * pct / 100 * ease(t / 0.7)), by0 + 82],
                            radius=8, fill=oc(ORG))
        ov.save(fdir / f"n{i:04d}.png")
    return N


def patch(s2: str, out: str, nape_pct=70, enable=(19.8, 22.25)):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp); fr = tmp / "dosik.jpg"
        mid = (enable[0] + enable[1]) / 2 - 0.7
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{mid:.2f}", "-i", s2,
                        "-frames:v", "1", str(fr)], check=True)
        cx, cy, r = _detect_circle(str(fr))
        fdir = tmp / "nape"; _nape_frames(fdir, cx, cy, r, nape_pct)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", s2,
                        "-itsoffset", f"{enable[0]}", "-framerate", "30", "-i", str(fdir / "n%04d.png"),
                        "-filter_complex",
                        f"[0:v][1:v]overlay=0:0:enable='between(t,{enable[0]},{enable[1]})':format=auto[v]",
                        "-map", "[v]", "-map", "0:a", "-c:a", "copy",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out], check=True)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("s2"); ap.add_argument("out")
    ap.add_argument("--nape-pct", type=int, default=70)
    ap.add_argument("--enable", default="19.8,22.25")
    a = ap.parse_args()
    e = tuple(float(x) for x in a.enable.split(","))
    print("완료:", patch(a.s2, a.out, a.nape_pct, e))
