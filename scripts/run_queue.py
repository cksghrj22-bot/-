#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""큐에 담긴 편들을 순서대로 끝까지 제작한다. (차노 2026-08-18 "결과물을 만들어내")
사용: {"cmd":"python_script","args":["run_queue.py","<slug>","<slug>",...]}"""
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
MAN  = ROOT / "content/manifests"
OUT  = ROOT / "_out/shorts"
res = []
for slug in sys.argv[1:]:
    man = MAN / ("쇼츠_%s_20260818.json" % slug)
    out = OUT / ("%s_20260818.mp4" % slug)
    if not man.exists():
        res.append((slug, "매니페스트 없음")); print("⛔ %s 매니페스트 없음" % slug, flush=True); continue
    print("\n=== %s ===" % slug, flush=True)
    r = subprocess.run([sys.executable, str(ROOT/"rooms/유튜브쇼츠방/make_short.py"), str(man), str(out)],
                       capture_output=True, text=True, cwd=str(ROOT))
    tail = (r.stdout or "")[-900:]
    ok = "[통과]" in (r.stdout or "")
    print(tail, flush=True)
    if not ok and (r.stderr or ""): print("stderr:", r.stderr[-400:], flush=True)
    res.append((slug, "통과" if ok else "탈락/오류"))
print("\n===== 요약 =====", flush=True)
for s, v in res: print("  %-14s %s" % (s, v), flush=True)
sys.exit(0)
