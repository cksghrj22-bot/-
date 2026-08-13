#!/usr/bin/env python3
"""
토큰/OAuth 만료 사전 체크 — 매일 실행
만료 임박하면 알림
"""
import json
import urllib.request
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
SECRETS = ROOT / "secrets"
LOGS = ROOT / "logs"

def check_gdrive():
    try:
        secrets = json.loads((SECRETS / "gdrive.json").read_text())
        data = {"client_id": secrets["client_id"], "client_secret": secrets["client_secret"],
                "refresh_token": secrets["refresh_token"], "grant_type": "refresh_token"}
        req = urllib.request.Request("https://oauth2.googleapis.com/token",
            data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return "access_token" in resp, "OK"
    except Exception as e:
        return False, str(e)

def check_elevenlabs():
    try:
        el = json.loads((SECRETS / "elevenlabs.json").read_text())
        req = urllib.request.Request("https://api.elevenlabs.io/v1/user",
            headers={"xi-api-key": el.get("api_key", "")})
        urllib.request.urlopen(req, timeout=10)
        return True, "OK"
    except Exception as e:
        return False, str(e)

def check_cowork_folders():
    try:
        rooms = json.loads((SECRETS / "cowork_rooms.json").read_text())
        return True, f"{len(rooms)}개 방"
    except:
        return False, "파일 없음"

def run_check():
    results = []
    
    ok, msg = check_gdrive()
    results.append(("드라이브", "✅" if ok else "❌", msg))
    
    ok, msg = check_elevenlabs()
    results.append(("일레븐랩스", "✅" if ok else "❌", msg))
    
    ok, msg = check_cowork_folders()
    results.append(("6방 폴더", "✅" if ok else "❌", msg))
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 토큰 헬스체크")
    for name, status, msg in results:
        print(f"  {status} {name}: {msg}")
    
    # 문제 있으면 로그
    problems = [r for r in results if "❌" in r[1]]
    if problems:
        with open(LOGS / "token_alert.log", "a") as f:
            f.write(f"[{datetime.now().isoformat()}] 문제 발견: {problems}\n")
        return False
    return True

if __name__ == "__main__":
    run_check()
