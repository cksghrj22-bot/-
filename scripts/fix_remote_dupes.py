#!/usr/bin/env python3
"""긴급 복구 (2026-08-17 21:4x 전략실)
 ① git 원격이 SSH(git@github.com)로 바뀌었다. 키가 GitHub 에 없어서 push 전부 실패한다.
    → 원래 HTTPS 로 되돌린다. (자동커밋·render_watch.sh 가 push 함)
 ② cowork_multi_watch 가 2개 떠 있다(수동 nohup + launchd KeepAlive).
    → 전부 죽이고 launchd 가 하나만 되살리게 둔다.
"""
import subprocess, time
from pathlib import Path
ROOT = Path.home() / "atnown-content-pipeline"
HTTPS = "https://github.com/cksghrj22-bot/-.git"

def sh(a, cwd=ROOT):
    r = subprocess.run(a, capture_output=True, text=True, timeout=60, cwd=str(cwd))
    return (r.stdout + r.stderr).strip()

print("=== ① 원격 복구 ===")
before = sh(["git", "remote", "get-url", "origin"])
print("  전:", before)
if before.startswith("git@"):
    sh(["git", "remote", "set-url", "origin", HTTPS])
    print("  후:", sh(["git", "remote", "get-url", "origin"]))
else:
    print("  이미 HTTPS — 손대지 않음")

print("\n=== ② 중복 데몬 정리 ===")
print("  전:", sh(["bash","-lc","pgrep -f cowork_multi_watch.py | wc -l"]).strip(), "개")
sh(["bash", "-lc", "pkill -f cowork_multi_watch.py"])
time.sleep(20)   # launchd KeepAlive 가 하나 되살릴 시간
n = sh(["bash","-lc","pgrep -f cowork_multi_watch.py | wc -l"]).strip()
print("  후:", n, "개  (1개면 정상 — launchd 가 되살림)")

print("\n=== 전체 데몬 ===")
print(sh(["bash","-lc","pgrep -lf 'codex_dispatch|cowork_multi|remote_cmd|render_watch' | sed 's|/opt/homebrew.*MacOS/Python ||' | sed 's|/Library/Developer.*MacOS/Python ||'"]))
