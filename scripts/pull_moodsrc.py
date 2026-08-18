#!/usr/bin/env python3
"""성희 무드 소재를 파이프라인 안으로 복사 + 실측"""
import shutil, subprocess
from pathlib import Path
HOME = Path.home()
DST = HOME / "atnown-content-pipeline" / "_intray_무드보드_보이드태그"
DST.mkdir(parents=True, exist_ok=True)
srcs = [HOME/"Downloads/moodboard_성희.pdf",
        HOME/"Desktop/타인의책장_성희_썸네일_2026-07-13.jpg",
        HOME/"Downloads/앳나운_룩북베이스_교육영상_10편구성안.pdf"]
for s in srcs:
    if s.exists():
        shutil.copy2(s, DST / s.name)
        print(f"복사 {s.name} ({s.stat().st_size//1024}KB)")
pdf = DST / "moodboard_성희.pdf"
if pdf.exists():
    r = subprocess.run(["bash","-lc",
        f"mdls -name kMDItemNumberOfPages '{pdf}' 2>/dev/null; "
        f"python3 -c \"import zlib,re,sys;d=open('{pdf}','rb').read();"
        f"print('페이지수(추정)', d.count(b'/Type/Page')-d.count(b'/Type/Pages'));"
        f"print('이미지객체(추정)', d.count(b'/Subtype/Image'))\""],
        capture_output=True, text=True, timeout=60)
    print(r.stdout.strip() or r.stderr.strip()[:200])
print("\n대상 폴더:", DST)
