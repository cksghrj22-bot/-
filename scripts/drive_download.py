#!/usr/bin/env python3
"""드라이브 파일 직접 다운로드 (대용량 지원)

사용법:
    python3 scripts/drive_download.py <file_id> <output_path>
"""
import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).parent.parent
CREDS = ROOT / "secrets/gdrive.json"

def get_access_token():
    """refresh_token으로 access_token 발급"""
    creds = json.loads(CREDS.read_text())
    data = urllib.parse.urlencode({
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": creds["refresh_token"],
        "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]

def download_file(file_id: str, output: Path, token: str):
    """파일 다운로드 (스트리밍)"""
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

    print(f"다운로드 시작: {file_id} → {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(req) as resp:
        total = int(resp.headers.get('Content-Length', 0))
        downloaded = 0
        with open(output, 'wb') as f:
            while True:
                chunk = resp.read(8192*16)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 // total
                    print(f"\r{downloaded // (1024*1024)}MB / {total // (1024*1024)}MB ({pct}%)", end="", flush=True)
    print(f"\n완료: {output} ({output.stat().st_size // (1024*1024)}MB)")

def main():
    if len(sys.argv) < 3:
        print("사용법: drive_download.py <file_id> <output_path>")
        return 1

    file_id = sys.argv[1]
    output = Path(sys.argv[2])

    token = get_access_token()
    download_file(file_id, output, token)
    return 0

if __name__ == "__main__":
    sys.exit(main() or 0)
