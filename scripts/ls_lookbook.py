#!/usr/bin/env python3
import subprocess
P = "/Users/chanho/Library/CloudStorage/GoogleDrive-cksghrj22@gmail.com/내 드라이브/앳나운_영상/성희룩북"
r = subprocess.run(["bash","-lc", f'ls -la "{P}" 2>&1 | head -40'], capture_output=True, text=True, timeout=90)
print("=== ls -la ===")
print(r.stdout.strip())
r2 = subprocess.run(["bash","-lc", f'find "{P}" -maxdepth 2 2>&1 | head -40'], capture_output=True, text=True, timeout=90)
print("\n=== find ===")
print(r2.stdout.strip())
r3 = subprocess.run(["bash","-lc", f'xattr -l "{P}" 2>&1 | head -5; stat -f "%z bytes  %N" "{P}" 2>&1'], capture_output=True, text=True, timeout=60)
print("\n=== 속성 ===")
print(r3.stdout.strip())
