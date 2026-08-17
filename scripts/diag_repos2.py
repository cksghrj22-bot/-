#!/usr/bin/env python3
"""세 저장소가 같은 계보인가? 뿌리 커밋·최근 활동·원격 비교"""
import subprocess
from pathlib import Path
HOME = Path.home()
REPOS = ["atnown-content-pipeline", "atnown-trunk", "atnown-repo"]

def sh(a, c):
    r = subprocess.run(a, capture_output=True, text=True, timeout=40, cwd=str(c))
    return r.stdout.strip() if r.returncode == 0 else f"(실패)"

info = {}
for name in REPOS:
    p = HOME / name
    root = sh(["git", "rev-list", "--max-parents=0", "HEAD"], p).splitlines()
    recent = sh(["git", "log", "-1", "--format=%ad", "--date=short"], p)
    n90 = sh(["git", "rev-list", "--count", "--since=90.days", "HEAD"], p)
    info[name] = (root[-1][:10] if root else "?", recent, n90)
    print(f"■ {name}")
    print(f"   뿌리커밋 {info[name][0]} · 최근커밋 {recent} · 최근90일 {n90}건")

print("\n=== 계보 판정 ===")
roots = {k: v[0] for k, v in info.items()}
uniq = set(roots.values())
if len(uniq) == 1:
    print("  같은 뿌리 → 한 계보에서 갈라진 것. 병합 가능")
else:
    print("  뿌리가 다름 → 서로 다른 저장소")
    for k, v in roots.items():
        print(f"    {k}: {v}")

print("\n=== 파이프라인에만 있는 최신 정본 파일이 트렁크에도 있나 ===")
for f in ["_ROOMS.md", "knowledge/방_공유_작업로그.md",
          "_strategy/전략기획및개인업무_전용규약.md", "scripts/remote_cmd_watch.py"]:
    a = (HOME / "atnown-content-pipeline" / f).exists()
    b = (HOME / "atnown-trunk" / f).exists()
    c = (HOME / "atnown-repo" / f).exists()
    print(f"  {f:48s} 파이프라인 {'O' if a else 'X'} · 트렁크 {'O' if b else 'X'} · repo {'O' if c else 'X'}")
