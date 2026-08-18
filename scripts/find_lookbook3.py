#!/usr/bin/env python3
import subprocess
def sh(c, t=120):
    r = subprocess.run(["bash","-lc",c], capture_output=True, text=True, timeout=t)
    return (r.stdout or "").strip()

GD = "$HOME/Library/CloudStorage/GoogleDrive-cksghrj22@gmail.com/내 드라이브"
print("=== 구글드라이브 「내 드라이브」 최상위 ===")
print(sh(f'ls "{GD}" 2>/dev/null | head -40') or "  (못 읽음)")
print("\n=== 드라이브에서 영상/룩북/성희 ===")
print(sh(f'find "{GD}" -maxdepth 3 -type d \\( -iname "*영상*" -o -iname "*룩북*" -o -iname "*성희*" -o -iname "*앳나운*" \\) 2>/dev/null | head -20') or "  (없음)")
print("\n=== 외장 Creator OS ===")
print(sh('ls "/Volumes/Creator OS" 2>/dev/null | head -20') or "  (못 읽음)")
print("\n=== 외장 One Touch ===")
print(sh('ls "/Volumes/One Touch" 2>/dev/null | head -20') or "  (못 읽음)")
print("\n=== 외장에서 성희/룩북/영상 ===")
print(sh('find "/Volumes/Creator OS" "/Volumes/One Touch" -maxdepth 4 -type d \\( -iname "*성희*" -o -iname "*룩북*" -o -iname "*앳나운영상*" \\) 2>/dev/null | head -20') or "  (없음)")
