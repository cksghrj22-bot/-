#!/usr/bin/env python3
"""실시간 감시 + 알림 — 실패 즉시 감지"""
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
ALERT_FILE = ROOT / "data/alerts.json"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def check_logs_for_errors():
    """최근 로그에서 에러 감지"""
    alerts = []
    log_files = [
        ("blog", ROOT / "data/blog_watcher.log"),
        ("codex", ROOT / "logs/codex_dispatch.log"),
        ("health", ROOT / "logs/health.log"),
    ]
    
    for name, path in log_files:
        if not path.exists():
            continue
        try:
            lines = path.read_text().split("\n")[-20:]
            for line in lines:
                if "⛔" in line or "에러" in line or "실패" in line:
                    alerts.append({"source": name, "msg": line[:100]})
        except:
            pass
    
    return alerts

def check_daemons():
    """데몬 상태 확인"""
    result = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    critical = ["codex-dispatch", "blogwatch", "renderwatch2", "health-check"]
    down = []
    
    for d in critical:
        if f"com.atnown.{d}" not in result.stdout:
            down.append(d)
        else:
            for line in result.stdout.split("\n"):
                if f"com.atnown.{d}" in line and line.startswith("-"):
                    down.append(d)
    
    return down

def main():
    log("👁️ 실시간 감시 시작")
    
    while True:
        # 에러 감지
        alerts = check_logs_for_errors()
        if alerts:
            log(f"⚠️ 에러 {len(alerts)}개 감지")
        
        # 데몬 확인
        down = check_daemons()
        if down:
            log(f"⛔ 데몬 다운: {down}")
        
        # 저장
        status = {
            "checked": datetime.now().isoformat(),
            "alerts": alerts[-10:],
            "daemons_down": down
        }
        ALERT_FILE.parent.mkdir(exist_ok=True)
        ALERT_FILE.write_text(json.dumps(status, ensure_ascii=False, indent=2))
        
        time.sleep(60)

if __name__ == "__main__":
    main()
