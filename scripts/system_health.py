#!/usr/bin/env python3
"""시스템 헬스체크 — 부팅 시 + 정기 실행
모든 의존성·데몬·연결 상태를 한 번에 검증하고 문제 있으면 자동 복구 시도.
"""
import subprocess
import json
import os
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
LOGS = ROOT / "logs"
LOGS.mkdir(exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOGS / "health.log", "a") as f:
        f.write(line + "\n")

def check_command(name, cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return True, result.stdout.strip()[:50]
        return False, result.stderr.strip()[:50]
    except FileNotFoundError:
        return False, "명령 없음"
    except Exception as e:
        return False, str(e)[:50]

def check_dependencies():
    deps = [
        ("python3", ["python3", "--version"]),
        ("node", ["/opt/homebrew/bin/node", "--version"]),
        ("ffmpeg", ["/opt/homebrew/bin/ffmpeg", "-version"]),
        ("git", ["git", "--version"]),
        ("faster-whisper", ["python3", "-c", "from faster_whisper import WhisperModel; print('OK')"]),
    ]
    results = []
    for name, cmd in deps:
        ok, msg = check_command(name, cmd)
        results.append((name, ok, msg))
        log(f"{'✅' if ok else '⛔'} {name}: {msg}")
    return results

def check_daemons():
    result = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    lines = [l for l in result.stdout.split("\n") if "atnown" in l]
    
    critical = ["codex-dispatch", "blogwatch", "renderwatch2", "cowork-multi"]
    results = []
    for daemon in critical:
        found = [l for l in lines if daemon in l]
        if found:
            parts = found[0].split()
            pid = parts[0] if parts[0] != "-" else None
            status = "running" if pid else "stopped"
            results.append((daemon, status == "running", f"PID {pid}" if pid else "stopped"))
        else:
            results.append((daemon, False, "not loaded"))
    
    for name, ok, msg in results:
        log(f"{'✅' if ok else '⛔'} daemon:{name}: {msg}")
    return results

def clean_stale_locks():
    cleaned = 0
    # git lock
    git_lock = ROOT / ".git/index.lock"
    if git_lock.exists():
        try:
            result = subprocess.run(["lsof", str(git_lock)], capture_output=True)
            if result.returncode != 0:  # no process using it
                git_lock.unlink()
                log("🧹 .git/index.lock 제거")
                cleaned += 1
        except:
            pass
    
    # other stale locks (0-byte, older than 5 minutes)
    for lock in ROOT.glob("**/*.lock"):
        if lock.stat().st_size == 0:
            age = datetime.now().timestamp() - lock.stat().st_mtime
            if age > 300:  # 5 minutes
                try:
                    lock.unlink()
                    log(f"🧹 스테일 락 제거: {lock.name}")
                    cleaned += 1
                except:
                    pass
    return cleaned

def check_connections():
    try:
        result = subprocess.run(
            ["python3", "-m", "pipeline", "check"],
            capture_output=True, text=True, timeout=30, cwd=str(ROOT)
        )
        ok = "OK" in result.stdout or result.returncode == 0
        log(f"{'✅' if ok else '⛔'} 연결 진단: {'통과' if ok else '실패'}")
        return ok
    except Exception as e:
        log(f"⛔ 연결 진단 실패: {e}")
        return False

def main():
    log("=" * 50)
    log("🏥 시스템 헬스체크 시작")
    
    # 1. 의존성
    log("--- 의존성 검사 ---")
    deps = check_dependencies()
    
    # 2. 데몬
    log("--- 데몬 검사 ---")
    daemons = check_daemons()
    
    # 3. 락 정리
    log("--- 락 정리 ---")
    cleaned = clean_stale_locks()
    log(f"락 {cleaned}개 정리")
    
    # 4. 연결
    log("--- 연결 검사 ---")
    conn_ok = check_connections()
    
    # 요약
    dep_ok = sum(1 for _, ok, _ in deps if ok)
    daemon_ok = sum(1 for _, ok, _ in daemons if ok)
    
    log("--- 요약 ---")
    log(f"의존성: {dep_ok}/{len(deps)}, 데몬: {daemon_ok}/{len(daemons)}, 연결: {'OK' if conn_ok else 'FAIL'}")
    
    all_ok = dep_ok == len(deps) and daemon_ok == len(daemons) and conn_ok
    log(f"{'✅ 전체 정상' if all_ok else '⛔ 문제 있음'}")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    exit(main())
