#!/usr/bin/env python3
"""유튜브 최종 볼륨매직 S2 위에 오버레이만: 도식 이름 변경(톱→정수리, 백→뒤통수) + 뒷목 삽입 + 뒷목 설명.

형 2026-07-28: "유튜브 최종 업로드한 매직영상에 두상 구조 이름만 바꾸고 네이프 껴넣고
네이프 설명 껴넣으면 완성이야." → S2를 다시 만들지 않는다. 실사·오디오·BGM·나레이션
전부 그대로 두고, 도식 구간(~14~22.2s)에 오버레이만 얹는다.

- 정수리 패치: 톱 등장(~14s)부터 톱 라벨 위 '정수리'
- 뒤통수 패치: 백 등장(~17s)부터 백 라벨 위 '뒤통수'
- 뒷목: 백 등장 뒤(~18s) 원 하단에 주황 박스+호+'뒷목 70%'+설명
좌표는 S2 도식 프레임(1080x1920) 기준 하드코딩.
"""
import argparse, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

NS = "/root/.fonts/nsqr_eb.ttf"
KY = "/root/.fonts/KyoboHandwriting2019.ttf"
DARK = (20, 23, 28); LAB = (228, 231, 238); ORG = (255, 140, 60)
# 하단 자막 패치(교보 이름도 바꿔야 — 박스만 바꾸고 자막 놔두면 반쪽). (창=[시작,끝], 한1, 한2, 영)
CAP_PATCHES = [
    ((14.0, 16.0), "정수리는 십 퍼센트만", "살짝 볼륨을 살리고", "Crown: only 10%, keep the volume"),
    ((20.0, 22.3), "뒤통수는 십오 퍼센트", "자연스럽게 연결해요", "Back of head: 15%, blend it naturally"),
]


def _frames(fdir: Path, win, top_t, back_t, nape_t, cx, cy, r, fps=30):
    fdir.mkdir(parents=True, exist_ok=True)
    for p in fdir.glob("*.png"):
        p.unlink()
    W, H = 1080, 1920
    f_lab = ImageFont.truetype(NS, 36); f_pct = ImageFont.truetype(NS, 60); f_exp = ImageFont.truetype(NS, 26)
    f_ck = ImageFont.truetype(KY, 60); f_ce = ImageFont.truetype(KY, 40)
    B = cy + r
    def ease(t): t = max(0, min(1, t)); return t * t * (3 - 2 * t)
    N = int((win[1] - win[0]) * fps)
    for i in range(N):
        t = win[0] + i / fps
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
        def kct(cx0, y, txt, fnt, fill):
            ws = txt.split(" "); gap = fnt.size * 0.26; wd = [d.textlength(w, font=fnt) for w in ws]
            x = cx0 - (sum(wd) + gap * (len(ws) - 1)) / 2
            for w, ww in zip(ws, wd):
                d.text((x, y), w, font=fnt, fill=fill); x += ww + gap
        # 하단 자막 패치(교보 이름 정합)
        for (cs, ce), k1, k2, en in CAP_PATCHES:
            if cs <= t < ce:
                d.rectangle([222, 1286, 858, 1520], fill=(0, 0, 0, 255))
                kct(W / 2, 1298, k1, f_ck, (245, 245, 245, 255))
                kct(W / 2, 1372, k2, f_ck, (245, 245, 245, 255))
                kct(W / 2, 1452, en, f_ce, (238, 238, 238, 255))
        # 톱→정수리
        if t >= top_t:
            d.rectangle([352, 320, 556, 374], fill=(*DARK, 255)); d.text((360, 322), "정수리", font=f_lab, fill=LAB)
        # 백→뒤통수 (백 잔상 완전히 덮게 y683부터)
        if t >= back_t:
            d.rectangle([653, 683, 886, 744], fill=(*DARK, 255)); d.text((662, 690), "뒤통수", font=f_lab, fill=LAB)
        # 뒷목
        if t >= nape_t:
            a = int(255 * ease((t - nape_t) / 0.45)); cnt = int(70 * ease((t - nape_t) / 0.7))
            oc = lambda c: (c[0], c[1], c[2], a)
            d.arc([cx - r, cy - r, cx + r, cy + r], 74, 106, fill=oc(ORG), width=10)
            d.line([(cx, B), (cx, B + 20)], fill=oc(ORG), width=3); d.ellipse([cx - 7, B - 7, cx + 7, B + 7], fill=oc(ORG))
            bw, bh = 430, 124; bx0 = cx - bw // 2; by0 = B + 20
            d.rounded_rectangle([bx0, by0, bx0 + bw, by0 + bh], radius=16,
                                fill=(20, 22, 28, int(240 * a / 255)), outline=oc(ORG), width=3)
            d.text((bx0 + 24, by0 + 14), "뒷목", font=f_lab, fill=(235, 238, 245, a))
            d.text((bx0 + 24, by0 + 54), f"{cnt}%", font=f_pct, fill=oc(ORG))
            d.text((bx0 + 210, by0 + 22), "확실히 눌러", font=f_exp, fill=(210, 214, 222, a))
            d.text((bx0 + 210, by0 + 58), "정리해요", font=f_exp, fill=(210, 214, 222, a))
        img.save(fdir / f"o{i:04d}.png")
    return N


def _detect_circle(frame_png):
    img = Image.open(frame_png).convert("RGB"); px = img.load()
    b = lambda x, y: sum(px[x, y]) > 430
    xs = [x for x in range(150, 930) if b(x, 915)]
    left, right = min(xs), max(xs); cx = (left + right) // 2; r = (right - left) // 2
    ys = [y for y in range(700, 1285) if b(cx, y)]; cy = max(ys) - r
    return cx, cy, r


def finalize(s2, out, win=(14.0, 22.3), top_t=14.0, back_t=17.0, nape_t=18.0):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp); fr = tmp / "d.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "21.5", "-i", s2, "-frames:v", "1", str(fr)], check=True)
        cx, cy, r = _detect_circle(str(fr))
        fdir = tmp / "ov"; _frames(fdir, win, top_t, back_t, nape_t, cx, cy, r)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", s2,
                        "-itsoffset", f"{win[0]}", "-framerate", "30", "-i", str(fdir / "o%04d.png"),
                        "-filter_complex",
                        f"[0:v][1:v]overlay=0:0:enable='between(t,{win[0]},{win[1]})':format=auto[v]",
                        "-map", "[v]", "-map", "0:a", "-c:a", "copy",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out], check=True)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("s2"); ap.add_argument("out")
    a = ap.parse_args(); print("완료:", finalize(a.s2, a.out))
