#!/usr/bin/env python3
"""매일 자동 시스템 체크 — 트리거 없이 혼자 돌아감

매일 09:00 자동 실행 (LaunchAgent)
결과: _status/daily_check.json + 문제 있으면 알림
"""
import json
import subprocess
import os
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
STATUS_FILE = ROOT / "_status/daily_check.json"
LOG_FILE = ROOT / "logs/daily_check.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def check_daemons():
    """데몬 상태"""
    r = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    daemons = {}
    expected = [
        "cowork-multi-watch", "renderwatch2", "codex-dispatch",
        "blogwatch", "health-check", "master-pipeline",
        "remote-cmd", "task-executor", "cowork-multi"
    ]
    for name in expected:
        running = f"com.atnown.{name}" in r.stdout
        daemons[name] = "✅" if running else "❌"
    return daemons

def check_tokens():
    """토큰 상태"""
    secrets = ROOT / "secrets"
    tokens = {}
    
    for name in ["gdrive", "elevenlabs", "youtube"]:
        f = secrets / f"{name}.json"
        if f.exists():
            try:
                data = json.loads(f.read_text())
                if name == "gdrive" and "refresh_token" in data:
                    tokens[name] = "✅"
                elif name == "elevenlabs" and "api_key" in data:
                    tokens[name] = "✅"
                elif name == "youtube" and "refresh_token" in data:
                    tokens[name] = "✅"
                else:
                    tokens[name] = "⚠️ 불완전"
            except:
                tokens[name] = "❌ 파싱실패"
        else:
            tokens[name] = "❌ 없음"
    
    return tokens

def check_git():
    """git 상태"""
    issues = []
    
    # lock 파일
    lock = ROOT / ".git/index.lock"
    if lock.exists():
        issues.append("index.lock 존재")
    
    # 원격 연결
    r = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True, cwd=str(ROOT))
    if "github.com" not in r.stdout:
        issues.append("원격 연결 없음")
    
    # 미푸시 커밋
    r = subprocess.run(["git", "status", "-sb"], capture_output=True, text=True, cwd=str(ROOT))
    if "ahead" in r.stdout:
        issues.append("미푸시 커밋 있음")
    
    return "✅" if not issues else f"⚠️ {', '.join(issues)}"

def check_disk():
    """디스크 상태"""
    import shutil
    total, used, free = shutil.disk_usage("/")
    free_gb = free // (1024**3)
    if free_gb < 10:
        return f"❌ {free_gb}GB 남음"
    elif free_gb < 50:
        return f"⚠️ {free_gb}GB 남음"
    return f"✅ {free_gb}GB 여유"

def check_queues():
    """작업 대기열"""
    queues = {}
    
    # 터미널 인박스
    inbox = ROOT / "_terminal_inbox"
    if inbox.exists():
        pending = len(list(inbox.glob("TASK_*.json")))
        queues["터미널인박스"] = f"{pending}건 대기"
    
    # 콘텐츠 큐
    q_file = ROOT / "data/content_queue.json"
    if q_file.exists():
        q = json.loads(q_file.read_text())
        queues["콘텐츠큐"] = f"{len(q.get('pending', []))}건 대기"
    
    return queues

def run_check():
    log("🔍 매일 시스템 체크 시작")
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "daemons": check_daemons(),
        "tokens": check_tokens(),
        "git": check_git(),
        "disk": check_disk(),
        "queues": check_queues(),
        "issues": []
    }
    
    # 문제 수집
    for name, status in result["daemons"].items():
        if status != "✅":
            result["issues"].append(f"데몬 {name} 중지")
    
    for name, status in result["tokens"].items():
        if "❌" in status:
            result["issues"].append(f"토큰 {name} 문제")
    
    if "❌" in result["disk"]:
        result["issues"].append("디스크 부족")
    
    # 저장
    STATUS_FILE.parent.mkdir(exist_ok=True)
    STATUS_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 요약 로그
    daemon_ok = sum(1 for s in result["daemons"].values() if s == "✅")
    daemon_total = len(result["daemons"])
    log(f"데몬: {daemon_ok}/{daemon_total}")
    log(f"토큰: {result['tokens']}")
    log(f"Git: {result['git']}")
    log(f"디스크: {result['disk']}")
    
    if result["issues"]:
        log(f"⚠️ 문제 {len(result['issues'])}건: {result['issues']}")
    else:
        log("✅ 전체 정상")
    
    return result

if __name__ == "__main__":
    import sys
    result = run_check()
    
    # --json 플래그면 JSON 출력
    if "--json" in sys.argv:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 사람용 요약
        print(f"\n{'='*50}")
        print(f"📊 시스템 체크 — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*50}")
        
        print("\n🖥️ 데몬:")
        for name, status in result["daemons"].items():
            print(f"  {status} {name}")
        
        print("\n🔑 토큰:")
        for name, status in result["tokens"].items():
            print(f"  {status} {name}")
        
        print(f"\n📁 Git: {result['git']}")
        print(f"💾 디스크: {result['disk']}")
        
        if result["queues"]:
            print("\n📋 대기열:")
            for name, count in result["queues"].items():
                print(f"  • {name}: {count}")
        
        if result["issues"]:
            print(f"\n⚠️ 문제점:")
            for issue in result["issues"]:
                print(f"  • {issue}")
        else:
            print("\n✅ 전체 정상")
        
        print(f"\n{'='*50}")
