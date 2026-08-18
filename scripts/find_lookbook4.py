#!/usr/bin/env python3
import subprocess
def sh(c, t=180):
    r = subprocess.run(["bash","-lc",c], capture_output=True, text=True, timeout=t)
    return (r.stdout or "").strip()
print("=== One Touch 전체 목록 ===")
print(sh('ls "/Volumes/One Touch" 2>/dev/null'))
print("\n=== 앳나운 들어간 폴더 (외장·드라이브, 띄어쓰기 무관) ===")
print(sh('find "/Volumes/One Touch" "$HOME/Library/CloudStorage" -maxdepth 5 -type d -iname "*앳나운*" 2>/dev/null | head -25') or "  (없음)")
print("\n=== 성희 (파일·폴더 전부, 외장 깊이8) ===")
print(sh('find "/Volumes/One Touch" -maxdepth 8 -iname "*성희*" 2>/dev/null | head -25') or "  (없음)")
print("\n=== 룩북 (전 볼륨) ===")
print(sh('find "/Volumes/One Touch" "$HOME/Library/CloudStorage" -maxdepth 6 -iname "*룩북*" -o -maxdepth 6 -iname "*look*book*" 2>/dev/null | head -20') or "  (없음)")
