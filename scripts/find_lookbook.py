#!/usr/bin/env python3
"""성희 룩북 폴더 찾기 — 홈 전역(깊이 4)"""
import os
from pathlib import Path
HOME = Path.home()
SKIP = {".git","node_modules","Library",".Trash","_clips_pool",".npm",".cache"}
KEY = ("성희","룩북","lookbook","look book","무드","mood")
hits=[]
for root, dirs, files in os.walk(HOME):
    d = Path(root)
    try:
        if len(d.relative_to(HOME).parts) > 4: dirs[:] = []; continue
    except Exception: pass
    dirs[:] = [x for x in dirs if x not in SKIP and not x.startswith(".")]
    for name in dirs + files:
        low = name.lower()
        if any(k in name or k in low for k in KEY):
            p = d / name
            n = 0
            if p.is_dir():
                try: n = sum(1 for f in p.rglob("*") if f.is_file())
                except Exception: pass
            hits.append((str(p), "폴더" if p.is_dir() else "파일", n))
for h in sorted(set(hits))[:40]:
    print(f"  [{h[1]}] {h[0]}" + (f"  · 파일 {h[2]}개" if h[2] else ""))
if not hits: print("  (못 찾음)")
