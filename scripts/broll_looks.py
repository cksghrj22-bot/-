#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B롤 재고를 **서로 다른 그림(look) 수**로 센다.
롱테이크는 장면전환이 없지만 카메라가 움직이며 그림이 바뀐다.
1초 간격 지문(색분포+세로구도)을 묶어 「몇 가지 그림이 몇 초씩 있나」를 뽑는다."""
import json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shot_variety import SIM_LIMIT, cos

ROOT = Path(__file__).resolve().parent.parent
POOL = ROOT / "_clips_pool/senior_new"
FPS  = 1.0
W, H = 24, 42

def frames(p):
    raw = subprocess.run(["ffmpeg","-v","error","-i",str(p),"-vf",
        f"fps={FPS},scale={W}:{H},format=gray","-f","rawvideo","-"],
        capture_output=True).stdout
    n = W*H
    return [list(raw[i:i+n]) for i in range(0, len(raw)-n+1, n)]

def main():
    only = sys.argv[1:] or None
    out = []
    for f in sorted(POOL.iterdir()):
        if f.suffix.lower() not in (".mov",".mp4"): continue
        if only and f.name not in only: continue
        fr = frames(f)
        if not fr: continue
        reps, spans = [], []
        for i, x in enumerate(fr):
            hit = None
            for k, r in enumerate(reps):
                if cos(r, x) >= SIM_LIMIT: hit = k; break
            if hit is None:
                reps.append(x); spans.append([i, i])
            else:
                spans[hit][1] = i
        looks = len(reps)
        out.append({"file": f.name, "sec": round(len(fr)/FPS,1), "looks": looks})
        print("%-38s %6.1fs  서로 다른 그림 %3d가지  (그림당 %4.1f초)"
              % (f.name, len(fr)/FPS, looks, (len(fr)/FPS)/max(1,looks)), flush=True)
    tot_s = sum(o["sec"] for o in out); tot_l = sum(o["looks"] for o in out)
    print("\n합계 %.0f초 · 서로 다른 그림 %d가지" % (tot_s, tot_l))
    print("→ 한 편(40초·장면 10개)당 그림 10가지 필요 → **최대 %d편**까지 안 겹친다" % (tot_l // 10))
    (ROOT/"_out/shorts/_broll_looks.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    return 0
sys.exit(main())
