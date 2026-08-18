#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B롤 톤 지수 — 클립마다 R-B 평균을 재서 기록한다.

차노 08-06 규약: **자동 톤보정으로 억지로 맞추지 않는다.** 톤이 튀면 눈이 불편해 재미로 못 본다.
→ 보정하지 말고 **톤이 맞는 클립만 골라 쓴다.** 그러려면 먼저 재야 한다.
차노 2026-08-18: "중간부터 끝까지 너무 빨간톤인데" (ep07 실측 R-B +20~+30)

출력: _out/shorts/_broll_tone.json  {"풀상대경로": R-B값}
"""
import json, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parent.parent
POOLS = [ROOT/"_clips_pool/senior_new", ROOT/"_clips_pool/문방구"]
OUT = ROOT/"_out/shorts/_broll_tone.json"

def dur(p):
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(p)],
                     capture_output=True,text=True)
    try: return float(r.stdout)
    except: return 0.0

def tone(p):
    d=dur(p)
    if d<=0: return None
    vals=[]
    with tempfile.TemporaryDirectory() as td:
        for frac in (0.25,0.5,0.75):
            png="%s/t.png"%td
            subprocess.run(["ffmpeg","-v","error","-ss","%.2f"%(d*frac),"-i",str(p),"-frames:v","1",
                            "-vf","scale=64:-2",png,"-y"],capture_output=True)
            if not Path(png).exists(): continue
            im=Image.open(png).convert("RGB"); px=list(im.getdata()); n=len(px)
            r=sum(q[0] for q in px)/n; b=sum(q[2] for q in px)/n
            vals.append(r-b)
    return round(sum(vals)/len(vals),1) if vals else None

def main():
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    for pool in POOLS:
        if not pool.exists(): continue
        for f in sorted(pool.iterdir()):
            if f.suffix.lower() not in (".mov",".mp4"): continue
            key = "%s/%s"%(pool.name, f.name)
            if key in res: continue
            t = tone(f)
            if t is None: continue
            res[key]=t
            print("%-46s R-B %+6.1f  %s"%(f.name[:44], t,
                  "🔴" if t>20 else ("🟡" if t>13 else "OK")), flush=True)
    OUT.write_text(json.dumps(res,ensure_ascii=False,indent=1))
    v=sorted(res.values())
    print("\n%d개 · 중앙 %+.1f · OK(≤13) %d개 · 따뜻 %d개 · 빨감(>20) %d개"
          %(len(v), v[len(v)//2], sum(1 for x in v if x<=13), sum(1 for x in v if 13<x<=20), sum(1 for x in v if x>20)))
    return 0
sys.exit(main())
