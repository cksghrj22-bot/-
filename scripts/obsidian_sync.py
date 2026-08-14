#!/usr/bin/env python3
"""옵시디언 볼트 자동 동기화 - 30분마다"""
import subprocess
import sys
from pathlib import Path
from datetime import datetime

VAULTS = [
    Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/앳나운_옵시디언_볼트",
    Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/차노스브레인",
]

def sync():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 옵시디언 동기화 시작")
    for vault in VAULTS:
        if vault.exists():
            result = subprocess.run(
                ["python3", "-m", "pipeline", "add-vault", str(vault)],
                cwd=Path.home() / "atnown-content-pipeline",
                capture_output=True, text=True
            )
            print(f"  {vault.name}: {result.stdout.strip()}")
    print("동기화 완료")

if __name__ == "__main__":
    sync()
