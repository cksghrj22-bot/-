#!/usr/bin/env python3
"""헬스체크 데몬 — 5분마다 시스템 상태 확인, 죽은 것 자동 재시작"""
import subprocess
import time
import os
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
INTERVAL = 300  # 5분

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

def restart_daemon(name):
    try:
        uid = os.getuid()
        subprocess.run(
            ["launchctl", "kickstart", "-k", f"gui/{uid}/com.atnown.{name}"],
            capture_output=True, timeout=30
        )
        log(f"🔄 {name} 재시작됨")
        return True
    except Exception as e:
        log(f"⛔ {name} 재시작 실패: {e}")
        return False

def check_and_fix():
    result = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    lines = result.stdout.split("\n")
    
    critical = {
        "codex-dispatch": True,
        "blogwatch": True,
        "renderwatch2": True,
        "cowork-multi": True,
        "task-executor": True,
    }
    
    for daemon, required in critical.items():
        found = [l for l in lines if f"com.atnown.{daemon}" in l]
        if found:
            parts = found[0].split()
            pid = parts[0]
            if pid == "-":
                log(f"⚠️ {daemon} 멈춤 — 재시작 시도")
                restart_daemon(daemon)
        elif required:
            log(f"⚠️ {daemon} 로드 안 됨")

def main():
    log("🏥 헬스 데몬 시작")
    while True:
        try:
            check_and_fix()
        except Exception as e:
            log(f"⛔ 체크 실패: {e}")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
