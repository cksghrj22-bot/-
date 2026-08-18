#!/usr/bin/env python3
import subprocess
def sh(c, t=180):
    r = subprocess.run(["bash","-lc",c], capture_output=True, text=True, timeout=t)
    return (r.stdout or "").strip()
GD = '$HOME/Library/CloudStorage/"GoogleDrive-cksghrj22@gmail.com (2026. 8. 2. 오전 2:08)"/"내 드라이브"/앳나운_영상'
print("=== 앳나운_영상 안 ===")
print(sh(f'ls "{GD}" 2>/dev/null'.replace('"$HOME','$HOME').replace('앳나운_영상"','앳나운_영상')) or sh(f"ls {GD} 2>/dev/null") or "  (못 읽음)")
print("\n=== 그 안에서 성희/룩북 ===")
print(sh(f"find {GD} -maxdepth 3 -iname '*성희*' -o -path '*앳나운_영상*' -maxdepth 3 -iname '*룩북*' 2>/dev/null | head -20") or "  (없음)")
print("\n=== 하위 폴더별 파일수 ===")
print(sh(f"for d in {GD}/*/; do echo \"$(basename \\\"$d\\\")  →  $(ls \\\"$d\\\" 2>/dev/null | wc -l)개\"; done 2>/dev/null | head -30") or "  (없음)")
