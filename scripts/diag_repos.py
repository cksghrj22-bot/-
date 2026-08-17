#!/usr/bin/env python3
"""본진이 몇 개인가 — 홈 밑 git 저장소 전수 조사 (2026-08-17 전략실)
   차노 질문: "그때 만든 본진과 새로 만든 본진의 커밋 개수가 같은지 확인했어?"
   → 저장소가 여러 개면 정본이 갈린다. 실측으로 답한다."""
import subprocess, os
from pathlib import Path

HOME = Path.home()

def sh(args, cwd):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=str(cwd))
        return r.stdout.strip() if r.returncode == 0 else f"(실패:{r.stderr.strip()[:60]})"
    except Exception as e:
        return f"(오류:{e})"

# 홈 바로 밑 + 한 단계 아래까지 .git 찾기
repos = []
for d in sorted(HOME.iterdir()):
    if not d.is_dir() or d.name.startswith((".", "Library")):
        continue
    if (d / ".git").exists():
        repos.append(d)
    else:
        try:
            for sub in sorted(d.iterdir()):
                if sub.is_dir() and (sub / ".git").exists():
                    repos.append(sub)
        except PermissionError:
            pass

print(f"홈에서 찾은 git 저장소: {len(repos)}개\n")
for r in repos:
    cnt = sh(["git", "rev-list", "--count", "HEAD"], r)
    head = sh(["git", "log", "-1", "--format=%h %ad %s", "--date=short"], r)
    rem = sh(["git", "remote", "-v"], r).splitlines()
    rem = rem[0].split()[1] if rem else "(원격 없음)"
    dirty = len(sh(["git", "status", "--short"], r).splitlines())
    star = " ⭐본진" if r.name == "atnown-content-pipeline" else ""
    print(f"■ {r}{star}")
    print(f"   커밋 {cnt}개 · 미커밋 {dirty}개")
    print(f"   HEAD {head[:80]}")
    print(f"   원격 {rem}")
    print()

# 파이프라인 안의 '본진' 폴더 정체
bj = HOME / "atnown-content-pipeline" / "본진"
if bj.exists():
    n = sum(1 for _ in bj.rglob("*") if _.is_file())
    print(f"■ 파이프라인 안의 '본진/' 폴더: 파일 {n}개 · 별도 저장소 아님(.git {'있음' if (bj/'.git').exists() else '없음'})")
