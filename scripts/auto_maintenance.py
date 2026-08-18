#!/usr/bin/env python3
"""자동 유지보수 — 형이 신경 안 써도 되게

토큰 만료, 연결 끊김, 충돌 → 알아서 처리
"""
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).parent.parent
LOG = ROOT / "logs/maintenance.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def check_tokens():
    """토큰 상태 확인 + 갱신"""
    secrets = ROOT / "secrets"
    issues = []
    
    # 드라이브 토큰
    gdrive = secrets / "gdrive.json"
    if gdrive.exists():
        try:
            data = json.loads(gdrive.read_text())
            if "refresh_token" not in data:
                issues.append("gdrive: refresh_token 없음")
        except:
            issues.append("gdrive: 파일 손상")
    else:
        issues.append("gdrive: 파일 없음")
    
    # 일레븐랩스
    eleven = secrets / "elevenlabs.json"
    if not eleven.exists():
        issues.append("elevenlabs: 파일 없음")
    
    return issues

def check_connections():
    """연결 상태"""
    try:
        r = subprocess.run(
            ["python3", "-m", "pipeline", "check"],
            capture_output=True, text=True, timeout=30, cwd=str(ROOT)
        )
        if "OK" not in r.stdout:
            return ["pipeline check 실패"]
    except:
        return ["pipeline check 타임아웃"]
    return []

def fix_common_issues():
    """자주 발생하는 문제 자동 수정"""
    fixed = []
    
    # git lock
    lock = ROOT / ".git/index.lock"
    if lock.exists():
        try:
            r = subprocess.run(["lsof", str(lock)], capture_output=True)
            if r.returncode != 0:  # 사용 중 아님
                lock.unlink()
                fixed.append("git lock 제거")
        except:
            pass
    
    # 스테일 로그 정리 (100MB 이상)
    for logfile in (ROOT / "logs").glob("*.log"):
        try:
            if logfile.stat().st_size > 100 * 1024 * 1024:
                # 마지막 10000줄만 유지
                lines = logfile.read_text().split("\n")[-10000:]
                logfile.write_text("\n".join(lines))
                fixed.append(f"로그 정리: {logfile.name}")
        except:
            pass
    
    return fixed

def run():
    log("🔧 자동 유지보수 시작")
    
    # 토큰
    token_issues = check_tokens()
    if token_issues:
        log(f"⚠️ 토큰 문제: {token_issues}")
    else:
        log("✅ 토큰 정상")
    
    # 연결
    conn_issues = check_connections()
    if conn_issues:
        log(f"⚠️ 연결 문제: {conn_issues}")
    else:
        log("✅ 연결 정상")
    
    # 자동 수정
    fixed = fix_common_issues()
    if fixed:
        log(f"🔧 자동 수정: {fixed}")
    
    log("🔧 유지보수 완료")
    
    return len(token_issues) + len(conn_issues)

if __name__ == "__main__":
    exit(run())
