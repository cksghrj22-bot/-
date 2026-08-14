#!/usr/bin/env python3
"""
일일 시스템 체크 — 매일 자동 실행
문제 발견 시 _ALERT.md에 기록

2026-08-14 생성
"""
import json
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).parent.parent
SECRETS = ROOT / "secrets"
ALERT_FILE = ROOT / "_ALERT.md"
LOG_FILE = ROOT / "data/daily_check.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def alert(msg):
    """문제 발견 시 _ALERT.md에 기록"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ALERT_FILE, "a") as f:
        f.write(f"\n## ⚠️ {ts}\n{msg}\n")
    log(f"⚠️ ALERT: {msg}")

# === 체크 함수들 ===

def check_instagram():
    """인스타 토큰 체크"""
    try:
        token_file = SECRETS / "instagram.json"
        if not token_file.exists():
            return False, "토큰 파일 없음"

        data = json.loads(token_file.read_text())
        token = data.get("access_token", "")

        url = f"https://graph.facebook.com/v26.0/me?fields=id,name&access_token={token}"
        resp = urllib.request.urlopen(url, timeout=10)
        result = json.loads(resp.read())
        return True, f"연결됨 ({result.get('name', '?')})"
    except urllib.error.HTTPError as e:
        return False, f"만료됨 (HTTP {e.code})"
    except Exception as e:
        return False, str(e)

def check_elevenlabs():
    """ElevenLabs 잔여량 체크"""
    try:
        key_file = SECRETS / "elevenlabs.json"
        if not key_file.exists():
            return False, "키 없음"

        key = json.loads(key_file.read_text()).get("api_key", "")
        req = urllib.request.Request(
            "https://api.elevenlabs.io/v1/user",
            headers={"xi-api-key": key}
        )
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())

        sub = data.get("subscription", {})
        used = sub.get("character_count", 0)
        limit = sub.get("character_limit", 1)
        pct = round(used / limit * 100, 1) if limit else 0

        if pct > 90:
            return False, f"{pct}% 사용 — 거의 소진!"
        elif pct > 70:
            return True, f"{pct}% 사용 — 주의"
        return True, f"{pct}% 사용"
    except Exception as e:
        return False, str(e)

def check_daemons():
    """데몬 프로세스 체크"""
    daemons = {
        "cowork_multi_watch": "cowork_multi_watch.py",
        "task_executor": "task_executor.py",
        "render_watch": "render",
    }
    results = []
    for name, pattern in daemons.items():
        try:
            r = subprocess.run(["pgrep", "-f", pattern], capture_output=True)
            if r.returncode == 0:
                results.append((name, True, "실행 중"))
            else:
                results.append((name, False, "안 돌고 있음"))
        except:
            results.append((name, False, "확인 실패"))
    return results

def check_ffmpeg():
    """ffmpeg 확인"""
    try:
        r = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True,
            env={"PATH": "/Users/chanho/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin"}
        )
        if r.returncode == 0:
            return True, "설치됨"
        return False, "없음"
    except:
        return False, "없음"

def check_drive_token():
    """구글 드라이브 토큰 체크"""
    try:
        token_file = SECRETS / "gdrive.json"
        if not token_file.exists():
            return False, "토큰 파일 없음"
        return True, "있음"
    except Exception as e:
        return False, str(e)

def check_threads_token():
    """스레드 토큰 체크"""
    try:
        token_file = SECRETS / "threads.json"
        if not token_file.exists():
            return False, "토큰 파일 없음"
        return True, "있음"
    except Exception as e:
        return False, str(e)

# === 메인 ===

def run_daily():
    """일일 체크 실행"""
    log("=" * 50)
    log("🔄 일일 시스템 체크 시작")

    problems = []

    # 인스타
    ok, msg = check_instagram()
    log(f"  인스타그램: {'✅' if ok else '❌'} {msg}")
    if not ok:
        problems.append(f"인스타그램: {msg}")

    # ElevenLabs
    ok, msg = check_elevenlabs()
    log(f"  ElevenLabs: {'✅' if ok else '❌'} {msg}")
    if not ok:
        problems.append(f"ElevenLabs: {msg}")

    # ffmpeg
    ok, msg = check_ffmpeg()
    log(f"  ffmpeg: {'✅' if ok else '❌'} {msg}")
    if not ok:
        problems.append(f"ffmpeg: {msg}")

    # 드라이브
    ok, msg = check_drive_token()
    log(f"  Google Drive: {'✅' if ok else '❌'} {msg}")
    if not ok:
        problems.append(f"Google Drive: {msg}")

    # 스레드
    ok, msg = check_threads_token()
    log(f"  스레드: {'✅' if ok else '❌'} {msg}")
    if not ok:
        problems.append(f"스레드: {msg}")

    # 데몬
    for name, ok, msg in check_daemons():
        log(f"  {name}: {'✅' if ok else '❌'} {msg}")
        if not ok:
            problems.append(f"{name}: {msg}")

    # 결과
    if problems:
        log(f"⚠️ 문제 {len(problems)}건 발견")
        alert("\n".join([f"- {p}" for p in problems]))
    else:
        log("✅ 전체 정상")

    log("=" * 50)
    return len(problems) == 0

if __name__ == "__main__":
    import sys
    success = run_daily()
    sys.exit(0 if success else 1)
