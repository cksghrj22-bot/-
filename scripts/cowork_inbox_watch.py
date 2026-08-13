#!/usr/bin/env python3
"""
코워크 연결폴더 감시 — 드라이브 _코워크_inbox → 터미널 inbox
10초마다 체크
"""
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
INBOX = ROOT / "_terminal_inbox"
SECRETS = ROOT / "secrets"
PROCESSED_FILE = ROOT / "data/cowork_processed.json"

COWORK_INBOX_ID = Path(SECRETS / "cowork_inbox_id.txt").read_text().strip()

def get_token():
    secrets = json.loads((SECRETS / "gdrive.json").read_text())
    data = {
        "client_id": secrets["client_id"],
        "client_secret": secrets["client_secret"],
        "refresh_token": secrets["refresh_token"],
        "grant_type": "refresh_token"
    }
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"}
    )
    return json.loads(urllib.request.urlopen(req).read())["access_token"]

def get_processed():
    if PROCESSED_FILE.exists():
        return set(json.loads(PROCESSED_FILE.read_text()))
    return set()

def save_processed(ids):
    PROCESSED_FILE.parent.mkdir(exist_ok=True)
    PROCESSED_FILE.write_text(json.dumps(list(ids)))

def list_inbox_files(token):
    query = f"'{COWORK_INBOX_ID}' in parents and trashed=false"
    url = f"https://www.googleapis.com/drive/v3/files?q={urllib.parse.quote(query)}&fields=files(id,name,mimeType,createdTime)"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    return json.loads(urllib.request.urlopen(req).read()).get("files", [])

def download_file(file_id, token):
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    return urllib.request.urlopen(req).read().decode("utf-8", errors="ignore")

def create_task(filename, content):
    task = {
        "id": f"cowork_{datetime.now().strftime('%Y%m%dT%H%M%S')}",
        "room": "코워크",
        "title": filename[:50],
        "request": content[:2000],
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "source": "cowork_inbox"
    }
    INBOX.mkdir(exist_ok=True)
    fname = f"TASK_cowork_{datetime.now().strftime('%Y%m%dT%H%M%S')}.json"
    (INBOX / fname).write_text(json.dumps(task, ensure_ascii=False, indent=2))
    print(f"✅ {fname}")

def check_inbox():
    try:
        token = get_token()
        files = list_inbox_files(token)
        processed = get_processed()
        
        new_files = [f for f in files if f["id"] not in processed]
        
        for f in new_files:
            if f["mimeType"].startswith("text/") or f["name"].endswith((".txt", ".md", ".json")):
                content = download_file(f["id"], token)
                create_task(f["name"], content)
                processed.add(f["id"])
            else:
                # 텍스트 아닌 파일은 경로만 전달
                create_task(f["name"], f"드라이브 파일: {f['name']} (ID: {f['id']})")
                processed.add(f["id"])
        
        save_processed(processed)
        
        if new_files:
            print(f"📥 {len(new_files)}개 파일 처리")
        
    except Exception as e:
        print(f"❌ 체크 실패: {e}")

def watch():
    print("🚀 코워크 inbox 감시 시작 (10초 간격)")
    while True:
        check_inbox()
        time.sleep(10)

if __name__ == "__main__":
    import sys
    if "--daemon" in sys.argv:
        watch()
    elif "--once" in sys.argv:
        check_inbox()
    else:
        watch()
