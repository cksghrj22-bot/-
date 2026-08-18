#!/usr/bin/env python3
"""성희 무드 소재 후보 실측"""
import subprocess
from pathlib import Path
HOME = Path.home()
cands = [HOME/"Downloads/moodboard_성희.pdf",
         HOME/"Desktop/타인의책장_성희_썸네일_2026-07-13.jpg",
         HOME/"Documents/ATNOWN_ref/mood-card.html",
         HOME/"Downloads/앳나운_룩북베이스_교육영상_10편구성안.pdf"]
for c in cands:
    if c.exists():
        print(f"✅ {c}  ({c.stat().st_size//1024}KB)")
    else:
        print(f"⛔ 없음: {c}")
print("\n=== '성희' 들어간 폴더 (홈 깊이6) ===")
r = subprocess.run(["bash","-lc",
  "find ~ -maxdepth 6 -type d \\( -iname '*성희*' -o -iname '*룩북*' -o -iname '*lookbook*' \\) "
  "-not -path '*/Library/*' -not -path '*/.git/*' 2>/dev/null | head -20"],
  capture_output=True, text=True, timeout=60)
print(r.stdout.strip() or "  (없음)")
print("\n=== Desktop / Downloads 최근 폴더 ===")
r2 = subprocess.run(["bash","-lc","ls -dt ~/Desktop/*/ ~/Downloads/*/ 2>/dev/null | head -14"],
  capture_output=True, text=True, timeout=30)
print(r2.stdout.strip() or "  (없음)")
