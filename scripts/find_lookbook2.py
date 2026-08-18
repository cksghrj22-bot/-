#!/usr/bin/env python3
"""앳나운영상폴더 / 성희룩북 찾기 — 클라우드 마운트·외장 포함"""
import subprocess
def sh(c, t=90):
    r = subprocess.run(["bash","-lc",c], capture_output=True, text=True, timeout=t)
    return (r.stdout or "").strip()

print("=== 클라우드 마운트 ===")
print(sh("ls ~/Library/CloudStorage 2>/dev/null || echo '(없음)'"))
print("\n=== 외장/볼륨 ===")
print(sh("ls /Volumes 2>/dev/null"))
print("\n=== '앳나운영상' 폴더 ===")
print(sh("find ~/Library/CloudStorage /Volumes ~/Desktop ~/Documents ~/Downloads -maxdepth 5 -type d -iname '*앳나운영상*' 2>/dev/null | head -10") or "  (없음)")
print("\n=== '성희' 폴더 (클라우드·외장 포함) ===")
print(sh("find ~/Library/CloudStorage /Volumes -maxdepth 7 -type d \\( -iname '*성희*' -o -iname '*룩북*' \\) 2>/dev/null | head -15") or "  (없음)")
print("\n=== 구글드라이브 최상위 ===")
print(sh("for d in ~/Library/CloudStorage/*/; do echo \"[$d]\"; ls \"$d\" 2>/dev/null | head -12; done") or "  (없음)")
