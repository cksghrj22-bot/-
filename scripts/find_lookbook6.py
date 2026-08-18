#!/usr/bin/env python3
import os
from pathlib import Path
HOME = Path.home()
roots = [p for p in (HOME/"Library"/"CloudStorage").glob("GoogleDrive-*")]
target = None
for r in roots:
    for base in r.glob("*/앳나운_영상"):
        print("■", base)
        try:
            for x in sorted(base.iterdir()):
                print("   -", x.name, "(폴더)" if x.is_dir() else "")
                if "성희" in x.name or "룩북" in x.name:
                    target = x
        except Exception as e:
            print("   읽기 실패:", e)
if not target:
    print("\n=== 전 마운트 깊이8 성희 검색 ===")
    for r in roots:
        for dp, dn, fn in os.walk(r):
            if len(Path(dp).relative_to(r).parts) > 6:
                dn[:] = []; continue
            for n in list(dn)+list(fn):
                if "성희" in n or "룩북" in n:
                    print("  ", Path(dp)/n)
                    if (Path(dp)/n).is_dir(): target = Path(dp)/n
if target:
    print("\n✅ 찾음:", target)
    imgs = [p for p in sorted(target.rglob("*")) if p.suffix.lower() in
            (".jpg",".jpeg",".png",".heic",".webp",".gif",".tif",".tiff")]
    print(f"이미지 {len(imgs)}개")
    for p in imgs[:60]:
        print(f"   {p.stat().st_size//1024:>6}KB  {p.relative_to(target)}")
    others = [p for p in sorted(target.rglob("*")) if p.is_file() and p not in imgs]
    if others:
        print(f"\n기타 파일 {len(others)}개")
        for p in others[:15]: print("   ", p.relative_to(target))
