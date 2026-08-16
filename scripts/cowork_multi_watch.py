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


def list_files(folder_id: str, token: str) -> list:
    q = f"'{folder_id}' in parents and trashed=false"
    url = ("https://www.googleapis.com/drive/v3/files"
           f"?q={urllib.parse.quote(q)}&fields=files(id,name,mimeType,createdTime)")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read()).get("files", [])


def download(file_id: str, token: str) -> str:
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
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
            if f["id"] in processed:
                continue
            try:
                is_text = f["mimeType"].startswith("text/") or f["name"].endswith((".txt", ".md", ".json"))
                body = download(f["id"], token) if is_text else f"드라이브 파일: {f['name']} (ID: {f['id']})"
                fname = create_task(room, f["name"], body)
                processed.add(f["id"])
                made += 1
                log(f"📥 {room} ← {f['name']} → {fname}")
            except Exception as e:
                log(f"⚠️ {room}/{f['name']} 처리 실패: {e}")

    save_processed(processed)
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
