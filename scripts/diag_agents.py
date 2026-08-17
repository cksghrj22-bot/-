#!/usr/bin/env python3
"""지금 실제로 떠 있는 LaunchAgent·프로세스 확인 (동결 전 안전점검)"""
import subprocess
def sh(a):
    r=subprocess.run(a,capture_output=True,text=True,timeout=30)
    return r.stdout.strip()
print("=== launchctl atnown ===")
print(sh(["bash","-lc","launchctl list | grep -i atnown || echo '(없음)'"]))
print("\n=== ~/Library/LaunchAgents ===")
print(sh(["bash","-lc","ls ~/Library/LaunchAgents 2>/dev/null || echo '(없음)'"]))
print("\n=== 도는 파이썬/셸 ===")
print(sh(["bash","-lc","pgrep -lf 'render_watch|노션동기|cowork_to_discord|codex_dispatch|cowork_multi|remote_cmd|blog_watcher' || echo '(없음)'"]))
print("\n=== atnown-repo / trunk 원격 ===")
print(sh(["bash","-lc","cd ~/atnown-repo && echo '[repo]' && git remote -v; cd ~/atnown-trunk && echo '[trunk]' && git remote -v"]))
