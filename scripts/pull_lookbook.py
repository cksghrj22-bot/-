#!/usr/bin/env python3
import shutil
from pathlib import Path
SRC = Path("/Users/chanho/Library/CloudStorage/GoogleDrive-cksghrj22@gmail.com/내 드라이브/앳나운_영상/성희룩북")
DST = Path.home()/"atnown-content-pipeline"/"_intray_무드보드_보이드태그"/"성희룩북"
DST.mkdir(parents=True, exist_ok=True)
EXT = {".jpg",".jpeg",".png",".heic",".webp",".gif",".tif",".tiff"}
if not SRC.exists():
    print("⛔ 경로 없음:", SRC); raise SystemExit(1)
items = sorted(SRC.rglob("*"))
imgs = [p for p in items if p.is_file() and p.suffix.lower() in EXT]
others = [p for p in items if p.is_file() and p.suffix.lower() not in EXT]
print(f"원본: 이미지 {len(imgs)}개 · 기타 {len(others)}개")
ok = 0
for p in imgs:
    rel = p.relative_to(SRC)
    out = DST / rel.name if len(rel.parts)==1 else DST / ("_".join(rel.parts))
    try:
        shutil.copy2(p, out); ok += 1
        print(f"  ✅ {out.name}  ({out.stat().st_size//1024}KB)")
    except Exception as e:
        print(f"  ⛔ {rel}  {e}")
print(f"\n복사 완료 {ok}/{len(imgs)}  →  {DST}")
if others:
    print("\n[이미지 아닌 파일]")
    for p in others[:20]: print("  ", p.relative_to(SRC))
