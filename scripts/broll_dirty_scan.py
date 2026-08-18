#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B롤에서 **자막이 이미 구워진 구간**을 찾아 표시한다.

2026-08-18 실사고: send_유행 을 뺐는데도 S5(UI존 자막 침범)가 났다.
video-1949 / 1961 안에도 완성본에서 딴 구간이 섞여 있어 원본 자막이 화면에 남아 있었다.
→ 1초 간격으로 훑어 **흰 글씨+검은 테두리 획**이 있는 구간을 장부에 미리 예약해 못 쓰게 만든다.

출력: _out/shorts/_broll_dirty.json  {파일명: [[시작,끝], ...]}
"""
import json, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
POOL = ROOT / "_clips_pool/senior_new"
OUT  = ROOT / "_out/shorts/_broll_dirty.json"
STEP = 1.0
BAND = (0.55, 1.00)     # 세로 55%~바닥 — 자막이 있을 수 있는 영역 전부
RATIO = 0.0012          # 2026-08-18: 0.0035 로는 1949·1961 안의 구운 자막을 놓쳤다

def dur(p):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(p)],
                       capture_output=True, text=True)
    try: return float(r.stdout)
    except: return 0.0

def size(p):
    r = subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries",
                        "stream=width,height","-of","csv=p=0",str(p)], capture_output=True, text=True)
    try:
        w,h = r.stdout.strip().split(","); return int(w), int(h)
    except: return 0,0

def has_text(img):
    im = Image.open(img).convert("L")
    nd = im.filter(ImageFilter.MinFilter(5))
    px, q = im.load(), nd.load()
    W, H = im.size; tot = out = 0
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            tot += 1
            if px[x,y] > 235 and q[x,y] < 60: out += 1
    return (out / max(1,tot)) > RATIO

def main():
    only = sys.argv[1:] or None
    res = {}
    for f in sorted(POOL.iterdir()):
        if f.suffix.lower() not in (".mov",".mp4"): continue
        if only and f.name not in only: continue
        d = dur(f); w,h = size(f)
        if d <= 0 or not w: continue
        # ⚠️ 렌더와 **같은 변환**을 거친 뒤 재야 한다 (2026-08-18):
        #    원본 4K 가로 프레임 전체를 보면 자막이 작아 비율에 안 걸린다.
        #    실제로는 scale=-2:1920, crop=1080:1920 로 가운데를 따므로 자막이 크게 들어온다.
        VF = "scale=-2:1920,crop=1080:1920,crop=1080:%d:0:%d" % (int(1920*(BAND[1]-BAND[0])), int(1920*BAND[0]))
        dirty, t = [], 0.0
        with tempfile.TemporaryDirectory() as td:
            while t < d - 0.2:
                png = str(Path(td)/"f.png")
                subprocess.run(["ffmpeg","-v","error","-ss","%.2f"%t,"-i",str(f),"-frames:v","1",
                                "-vf", VF + ",scale=240:-2", png, "-y"],
                               capture_output=True)
                if Path(png).exists() and has_text(png):
                    if dirty and t - dirty[-1][1] <= STEP*1.5: dirty[-1][1] = t + STEP
                    else: dirty.append([t, t + STEP])
                t += STEP
        if dirty:
            dirty = [[round(max(0,a-0.5),2), round(min(d,b+0.5),2)] for a,b in dirty]
            res[f.name] = dirty
        bad = sum(b-a for a,b in dirty)
        print("%-38s %6.1fs  자막구간 %5.1fs (%2d곳)%s"
              % (f.name, d, bad, len(dirty), "  ⚠️" if bad > d*0.5 else ""), flush=True)
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print("\n→ %s 에 기록. gen_manifest 가 이 구간을 피한다." % OUT.name)
    return 0

sys.exit(main())
