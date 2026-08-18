#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B롤 실사용 가능 분량 분석 — 긴 클립 안의 **컷(샷)** 을 잘라 센다.
파일 개수가 아니라 **서로 다른 그림이 몇 초나 있는가**가 진짜 재고다."""
import json, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
POOL = ROOT / "_clips_pool/senior_new"
MIN_SHOT = 1.6

def dur(p):
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(p)],
                     capture_output=True,text=True)
    try: return float(r.stdout)
    except: return 0.0

def shots(p, thr=0.28):
    """장면 전환 시각 목록"""
    r=subprocess.run(["ffmpeg","-v","info","-i",str(p),"-vf",
        "select='gt(scene,%s)',showinfo"%thr,"-an","-f","null","-"],capture_output=True,text=True)
    ts=[float(x) for x in re.findall(r"pts_time:([0-9.]+)", r.stderr)]
    return sorted(set(round(t,2) for t in ts))

def main():
    rows=[]; total=0.0; usable=0.0
    for f in sorted(POOL.iterdir()):
        if f.suffix.lower() not in (".mov",".mp4"): continue
        d=dur(f); total+=d
        cuts=[0.0]+shots(f)+[d]
        segs=[(cuts[i],cuts[i+1]) for i in range(len(cuts)-1) if cuts[i+1]-cuts[i]>=MIN_SHOT]
        u=sum(b-a for a,b in segs); usable+=u
        rows.append({"file":f.name,"sec":round(d,1),"shots":len(segs),"usable":round(u,1),
                     "segs":[[round(a,2),round(b,2)] for a,b in segs]})
        print("%-38s %6.1fs  샷 %3d개  쓸수있는 %6.1fs"%(f.name,d,len(segs),u),flush=True)
    (ROOT/"_out/shorts/_broll_index.json").write_text(json.dumps(rows,ensure_ascii=False,indent=1))
    print("\n총 %.1f초 · 1.6초 이상 샷 %d개 · 실사용 가능 %.1f초"
          %(total,sum(r["shots"] for r in rows),usable))
    return 0
sys.exit(main())
