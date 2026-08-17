#!/usr/bin/env python3
"""
코워크 다방 인박스 감시 — 드라이브 _코워크_<방>_inbox → _terminal_inbox/TASK_*.json

`knowledge/코워크_6방_정본.md`(폐기) 가 이 스크립트를 가리켰지만 파일 자체가 없었다.
2026-08-16 재작성. 방 명부 정본 = `_ROOMS.md`, 폴더 ID = `secrets/cowork_rooms.json`.

  python3 scripts/cowork_multi_watch.py --once     # 한 번만
  python3 scripts/cowork_multi_watch.py --daemon   # 상주 (기본 10초)
  python3 scripts/cowork_multi_watch.py --rooms    # 등록된 방 목록만
"""
import json
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
INBOX = ROOT / "_terminal_inbox"
SECRETS = ROOT / "secrets"
LOGS = ROOT / "logs"
PROCESSED_FILE = ROOT / "data" / "cowork_multi_processed.json"
FAILED_FILE = ROOT / "data" / "cowork_multi_failed.json"
MAX_TRY = 3   # 같은 파일 3회 실패하면 포기 (로그 폭주 방지)
ROOMS_FILE = SECRETS / "cowork_rooms.json"
INTERVAL = 10


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    LOGS.mkdir(exist_ok=True)
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOGS / "cowork_multi.log", "a") as f:
        f.write(line + "\n")


def load_rooms() -> dict:
    if not ROOMS_FILE.exists():
        raise SystemExit(f"방 목록 없음: {ROOMS_FILE}")
    d = json.loads(ROOMS_FILE.read_text())
    return d.get("rooms", d)


def get_token() -> str:
    s = json.loads((SECRETS / "gdrive.json").read_text())
    data = {
        "client_id": s["client_id"],
        "client_secret": s["client_secret"],
        "refresh_token": s["refresh_token"],
        "grant_type": "refresh_token",
    }
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=30).read())["access_token"]


def get_processed() -> set:
    if PROCESSED_FILE.exists():
        try:
            return set(json.loads(PROCESSED_FILE.read_text()))
        except Exception:
            return set()
    return set()


def save_processed(ids: set):
    PROCESSED_FILE.parent.mkdir(exist_ok=True)
    PROCESSED_FILE.write_text(json.dumps(sorted(ids), ensure_ascii=False))


def get_failed() -> dict:
    if FAILED_FILE.exists():
        try:
            return json.loads(FAILED_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_failed(d: dict):
    FAILED_FILE.parent.mkdir(exist_ok=True)
    FAILED_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2))


def list_files(folder_id: str, token: str) -> list:
    q = f"'{folder_id}' in parents and trashed=false"
    url = ("https://www.googleapis.com/drive/v3/files"
           f"?q={urllib.parse.quote(q)}&fields=files(id,name,mimeType,createdTime)")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read()).get("files", [])


def fetch_body(f: dict, token: str):
    """드라이브 파일 본문을 가져온다.

    ⚠️ 2026-08-17 실사고: 예전엔 파일명이 .md 면 무조건 alt=media 로 받았다.
       구글 독스로 만들어진 'TASK_*.md' 는 alt=media 가 403 Forbidden 이라
       형이 넣은 지시 2건이 9시간 동안 4073회 재시도만 하고 못 들어왔다.
       → mimeType 을 먼저 보고, 구글 문서형이면 export 로 받는다.
    """
    mt = f.get("mimeType", "")
    fid = f["id"]
    if mt == "application/vnd.google-apps.folder":
        return None
    if mt.startswith("application/vnd.google-apps."):
        url = (f"https://www.googleapis.com/drive/v3/files/{fid}/export"
               f"?mimeType={urllib.parse.quote('text/plain')}")
    elif mt.startswith("text/") or f["name"].endswith((".txt", ".md", ".json")):
        url = f"https://www.googleapis.com/drive/v3/files/{fid}?alt=media"
    else:
        return f"드라이브 파일: {f['name']} (ID: {fid})"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    return urllib.request.urlopen(req, timeout=60).read().decode("utf-8", errors="ignore")


def create_task(room: str, filename: str, body: str) -> str:
    """CLAUDE.md 규격 {"room","task","timeout"} + 디스패처 호환 필드를 함께 쓴다."""
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    safe = "".join(c for c in Path(filename).stem if c.isalnum() or c in "-_가-힣")[:30]
    task = {
        "room": room,
        "task": body[:4000],
        "timeout": 300,
        "title": filename[:60],
        "request": body[:4000],
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "source": f"cowork_inbox/{room}",
    }
    INBOX.mkdir(exist_ok=True)
    fname = f"TASK_{room}_{safe}_{stamp}.json"
    (INBOX / fname).write_text(json.dumps(task, ensure_ascii=False, indent=2))
    return fname


def check_once() -> int:
    rooms = load_rooms()
    token = get_token()
    processed = get_processed()
    failed = get_failed()
    made = 0

    for room, folder_id in rooms.items():
        if not isinstance(folder_id, str):
            continue
        try:
            files = list_files(folder_id, token)
        except Exception as e:
            log(f"⚠️ {room} 목록 실패: {e}")
            continue

        for f in files:
            fid = f["id"]
            if fid in processed:
                continue
            if failed.get(fid, 0) >= MAX_TRY:
                continue          # 포기한 건 조용히 건너뛴다
            try:
                body = fetch_body(f, token)
                if body is None:
                    processed.add(fid)
                    continue
                fname = create_task(room, f["name"], body)
                processed.add(fid)
                failed.pop(fid, None)
                made += 1
                log(f"📥 {room} ← {f['name']} → {fname}")
            except Exception as e:
                failed[fid] = failed.get(fid, 0) + 1
                n = failed[fid]
                if n == 1 or n >= MAX_TRY:
                    tail = f" — {MAX_TRY}회 실패, 포기함. 형 확인 필요" if n >= MAX_TRY else ""
                    log(f"⚠️ {room}/{f['name']} 처리 실패({n}/{MAX_TRY}): {e}{tail}")

    save_processed(processed)
    save_failed(failed)
    return made


def watch():
    rooms = load_rooms()
    log(f"🚀 코워크 다방 감시 시작 — {len(rooms)}방 / {INTERVAL}초 간격")
    while True:
        try:
            check_once()
        except Exception as e:
            log(f"❌ 사이클 실패: {e}")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    if "--rooms" in sys.argv:
        for r in load_rooms():
            print(" -", r)
    elif "--once" in sys.argv:
        n = check_once()
        log(f"✅ 1회 점검 완료 — 신규 {n}건")
    else:
        watch()
