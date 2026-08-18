#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B롤 자동 갱신 — 차노 2026-08-18 "앳나운영상 폴더에 계속 올리고 있으니 계속 확인해서 새 B롤 계속 써"

  ① 앳나운영상 하위 전 폴더에서 **새 파일만** 수거
  ② 새 파일만 톤(R-B) 측정
  ③ 새 파일만 구운자막 스캔
  ④ 승인목록 갱신 (폴더 규칙 — 남의 살롱·세미나·회식 제외)

⚠️ 샌드박스 밖(remote_cmd_watch)에서 실행할 것.
"""
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
POOL = ROOT/"_clips_pool/senior_new"
MUN  = ROOT/"_clips_pool/문방구"
OKJ  = ROOT/"_out/shorts/_문방구_승인.json"
IDXJ = ROOT/"_out/shorts/_문방구_재고.json"

# 폴더 규칙 — 차노 승인 기준
OK = ["머리하는장면","애프터영상","/상담","프레임펌","여름에 레이어드","미용실 원장의 아침","사모님"]
NG = ["회식","세미나","외부활동","낙타캐러셀","3일차 마무리","기타","성희 부원장","차홍슈"]

def run(name, *args):
    print("\n── %s ──"%name, flush=True)
    r = subprocess.run([sys.executable, str(ROOT/"scripts"/name)] + list(args),
                       capture_output=True, text=True, cwd=str(ROOT), timeout=540)
    out = (r.stdout or "")[-1200:]
    print(out, flush=True)
    if r.returncode: print("(rc=%d) %s"%(r.returncode, (r.stderr or "")[-200:]), flush=True)
    return r.returncode

def main():
    before = {p.name for p in list(POOL.glob("*")) + list(MUN.glob("*"))}
    run("drive_pull_broll.py")
    after = {p.name for p in list(POOL.glob("*")) + list(MUN.glob("*"))}
    new = sorted(after - before)
    print("\n=== 새 B롤 %d개 ==="%len(new), flush=True)
    for n in new[:30]: print("  +", n, flush=True)
    # 톤·자막 스캔은 스크립트 자체가 이미 있는 항목을 건너뛴다
    run("broll_tone.py")
    if new: run("broll_dirty_scan.py", *new[:40])
    # 승인목록 갱신
    idx = {x["name"].replace("/","_"):(x.get("path") or "") for x in json.loads(IDXJ.read_text())} if IDXJ.exists() else {}
    use = []
    for p in sorted(MUN.iterdir()):
        if p.suffix.lower() not in (".mov",".mp4"): continue
        path = idx.get(p.name, "")
        if any(n in path for n in NG): continue
        if path and not any(o in path for o in OK): continue
        use.append(p.name)
    OKJ.write_text(json.dumps(use, ensure_ascii=False, indent=1))
    print("\n승인 클립 %d개 · 풀 전체 %d개"%(len(use), len(after)), flush=True)
    return 0
sys.exit(main())
