#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""쇼츠 화면시안 빌더 — 유튜브쇼츠방 (2026-08-17)
매니페스트 JSON(cuts)만 있으면 1080x1920 시안을 굽는다. 중단돼도 다시 돌리면 이어서 한다.
사용: python3 rooms/유튜브쇼츠방/build_shorts_sian.py <매니페스트.json> <출력.mp4> [작업폴더]
"""
import json, subprocess, os, sys
from PIL import Image, ImageDraw, ImageFont

R = os.getcwd()
KYOBO = os.path.join(R, "assets/fonts/KyoboHandwriting2019.ttf")
SRC   = os.path.join(R, "_clips_pool/senior_new")
CAP_Y = 1436          # 자막 아랫선 (UI존 1540 위)
FS    = 62

def cap_png(text, path, size=FS, maxw=940):
    """⚠️ 교보손글씨에는 공백 글리프가 없다 — 폰트에 맡기면 □로 깨진다(2026-08-17 실사고).
    어절을 따로 그리고 간격은 직접 준다."""
    f = ImageFont.truetype(KYOBO, size)
    d0 = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    GAP = int(size * 0.32)
    words = [w for w in text.split(" ") if w]
    wl = [d0.textlength(w, font=f) for w in words]
    lines, cur, curw = [], [], 0.0
    for w, l in zip(words, wl):
        add = l if not cur else GAP + l
        if curw + add <= maxw or not cur:
            cur.append((w, l)); curw += add
        else:
            lines.append((cur, curw)); cur = [(w, l)]; curw = l
    if cur: lines.append((cur, curw))
    lh = int(size * 1.38); W = maxw + 60; H = lh * len(lines) + 30
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for li, (ws, tw) in enumerate(lines):
        x = (W - tw) / 2; y = 15 + li * lh
        for w, l in ws:
            for dx in (-3, 0, 3):
                for dy in (-3, 0, 3):
                    if dx or dy: d.text((x + dx, y + dy), w, font=f, fill=(0, 0, 0, 235))
            d.text((x, y), w, font=f, fill=(255, 255, 255, 255))
            x += l + GAP
    im.save(path); return W, H

def dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    try: return float(r.stdout)
    except: return -1.0

def main():
    man, out_mp4 = sys.argv[1], sys.argv[2]
    WK = sys.argv[3] if len(sys.argv) > 3 else os.path.join(R, "_out/shorts/_build")
    os.makedirs(WK, exist_ok=True)
    cuts = json.load(open(man))["cuts"]
    ptr, parts = {}, []
    for i, c in enumerate(cuts):
        d = round(c["end"] - c["start"], 2)
        out = "%s/v%02d.mp4" % (WK, i)
        black = not c["clip"]
        if not black:
            src = os.path.join(SRC, c["clip"])
            tot = dur(src)
            ss = float(c["in"]) if c.get("in") is not None else ptr.get(c["clip"], 0.2)
            if ss + d > tot - 0.05: ss = max(0.0, tot - d - 0.1)
            ptr[c["clip"]] = ss + d + 0.1
        # 이미 제대로 구워졌으면 건너뛴다 (길이까지 확인 — 잘린 파일 재사용 방지)
        if os.path.exists(out) and abs(dur(out) - d) < 0.25:
            parts.append(out); continue
        png = "%s/c%02d.png" % (WK, i)
        w, h = cap_png(c["말"], png)
        # ⭐ 검정 카드는 화면 정중앙 / 영상 위 자막은 하단 CAP_Y 기준 (차노 2026-08-17)
        y = int((1920 - h) / 2) if black else CAP_Y - h + 12
        if black:
            cmd = ["ffmpeg", "-v", "error", "-f", "lavfi",
                   "-i", "color=c=black:s=1080x1920:r=30:d=%.2f" % d, "-i", png,
                   "-filter_complex", "[0][1]overlay=(W-w)/2:%d" % y,
                   "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                   "-r", "30", "-t", "%.2f" % d, out, "-y"]
        else:
            cmd = ["ffmpeg", "-v", "error", "-ss", "%.2f" % ss, "-t", "%.2f" % d,
                   "-i", src, "-i", png, "-an", "-filter_complex",
                   "[0]scale=-2:1920,crop=1080:1920,setsar=1,fps=30[v];[v][1]overlay=(W-w)/2:%d" % y,
                   "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                   "-r", "30", "-t", "%.2f" % d, out, "-y"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            print("FAIL", i, r.stderr[:300], flush=True); return 1
        parts.append(out); print("cut %02d ok%s" % (i, " (검정 중앙)" if black else ""), flush=True)
    lst = WK + "/list.txt"
    open(lst, "w").write("\n".join("file '%s'" % os.path.abspath(p) for p in parts))
    r = subprocess.run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0",
                        "-i", lst, "-c", "copy", out_mp4, "-y"], capture_output=True, text=True)
    print("concat", r.returncode, r.stderr[:200], flush=True)
    print("결과 %.2f초" % dur(out_mp4), flush=True)
    return 0

sys.exit(main())
