#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""장면 단위 쇼츠 빌더 — 유튜브쇼츠방 (2026-08-17)

⭐ 차노 지시: "커트가 하다 말다 하다 말다 정신이 없다. 커트는 딱 보여줬으면
   그게 다 옷 보여줘서 뭘 하는지는 보여줘야 된다."
→ 한 시술은 **끊지 않고 통으로** 간다. 자막만 그 위에서 바뀐다.
   매니페스트의 `scene` 값이 같은 연속 컷 = 소스 한 구간을 이어서 쓴다.

사용: python3 rooms/유튜브쇼츠방/build_scene_sian.py <매니페스트.json> <출력.mp4> [작업폴더]
"""
import json, subprocess, os, sys
from PIL import Image, ImageDraw, ImageFont

R = os.getcwd()
KYOBO = os.path.join(R, "assets/fonts/KyoboHandwriting2019.ttf")
SRC   = os.path.join(R, "_clips_pool/senior_new")
CAP_Y = 1436
FS    = 62

def cap_png(text, path, size=FS, maxw=940):
    """⚠️ 교보손글씨에 공백 글리프가 없다 — 어절별로 그리고 간격은 코드가 준다."""
    f = ImageFont.truetype(KYOBO, size)
    d0 = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    GAP = int(size * 0.32)
    words = [w for w in text.split(" ") if w]
    wl = [d0.textlength(w, font=f) for w in words]
    lines, cur, curw = [], [], 0.0
    for w, l in zip(words, wl):
        add = l if not cur else GAP + l
        if curw + add <= maxw or not cur: cur.append((w, l)); curw += add
        else: lines.append((cur, curw)); cur = [(w, l)]; curw = l
    if cur: lines.append((cur, curw))
    lh = int(size * 1.38); W = maxw + 60; H = lh * len(lines) + 30
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for li, (ws, tw) in enumerate(lines):
        x = (W - tw) / 2; y = 15 + li * lh
        for w, l in ws:
            for dx in (-3, 0, 3):
                for dy in (-3, 0, 3):
                    if dx or dy: d.text((x+dx, y+dy), w, font=f, fill=(0, 0, 0, 235))
            d.text((x, y), w, font=f, fill=(255, 255, 255, 255))
            x += l + GAP
    im.save(path); return W, H

def dur(path):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(path)],
                       capture_output=True, text=True)
    try: return float(r.stdout)
    except: return -1.0

def main():
    man, out_mp4 = sys.argv[1], sys.argv[2]
    WK = sys.argv[3] if len(sys.argv) > 3 else os.path.join(R, "_out/shorts/_build_scene")
    os.makedirs(WK, exist_ok=True)
    cuts = json.load(open(man))["cuts"]

    # scene 이 같은 연속 컷을 한 덩어리로 묶는다
    scenes, cur = [], []
    for c in cuts:
        if cur and c.get("scene") == cur[-1].get("scene"): cur.append(c)
        else:
            if cur: scenes.append(cur)
            cur = [c]
    if cur: scenes.append(cur)

    parts = []
    for si, sc in enumerate(scenes):
        t0, t1 = sc[0]["start"], sc[-1]["end"]
        seg = round(t1 - t0, 2)
        out = "%s/s%02d.mp4" % (WK, si)
        black = not sc[0]["clip"]
        if abs(dur(out) - seg) < 0.25:
            parts.append(out); continue
        # 자막 PNG + 노출 구간(장면 시작 기준 상대시간)
        inputs, filt, cur_lbl, idx = [], [], "[v]", 1
        for ci, c in enumerate(sc):
            png = "%s/s%02d_c%d.png" % (WK, si, ci)
            w, h = cap_png(c["말"], png)
            y = int((1920 - h) / 2) if black else CAP_Y - h + 12
            a = round(c["start"] - t0, 2); b = round(c["end"] - t0, 2)
            inputs += ["-i", png]
            nxt = "[o%d]" % idx
            filt.append("%s[%d]overlay=(W-w)/2:%d:enable='between(t,%.2f,%.2f)'%s"
                        % (cur_lbl, idx, y, a, b - 0.02, nxt))
            cur_lbl = nxt; idx += 1
        if black:
            base = ["-f", "lavfi", "-i", "color=c=black:s=1080x1920:r=30:d=%.2f" % seg]
            pre = "[0]null[v]"
        else:
            src = os.path.join(SRC, sc[0]["clip"])
            tot = dur(src); ss = float(sc[0].get("in", 0.2))
            if ss + seg > tot - 0.05: ss = max(0.0, tot - seg - 0.05)
            base = ["-ss", "%.2f" % ss, "-t", "%.2f" % seg, "-i", src]
            pre = "[0]scale=-2:1920,crop=1080:1920,setsar=1,fps=30[v]"
        fc = pre + ";" + ";".join(filt)
        cmd = ["ffmpeg","-v","error"] + base + inputs + ["-an","-filter_complex", fc,
               "-map", cur_lbl, "-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p",
               "-r","30","-t","%.2f" % seg, out, "-y"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            print("FAIL scene", si, r.stderr[:400], flush=True); return 1
        parts.append(out)
        print("장면 %02d  %s  %.2f초  자막 %d개%s"
              % (si, sc[0]["clip"] or "검정카드", seg, len(sc), " (통컷)" if len(sc) > 1 else ""), flush=True)

    lst = WK + "/list.txt"
    open(lst, "w").write("\n".join("file '%s'" % os.path.abspath(p) for p in parts))
    r = subprocess.run(["ffmpeg","-v","error","-f","concat","-safe","0","-i",lst,
                        "-c","copy",out_mp4,"-y"], capture_output=True, text=True)
    print("concat", r.returncode, r.stderr[:200], flush=True)
    print("장면 %d개 · 결과 %.2f초" % (len(scenes), dur(out_mp4)), flush=True)
    return 0

sys.exit(main())
