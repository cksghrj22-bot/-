#!/usr/bin/env python3
"""로컬 파일 → 인스타가 받아갈 수 있는 공개 URL

방법: 구글드라이브에 업로드 + 공개 권한 + 직접 다운로드 URL 반환

인스타 Graph API는 HTML 페이지가 아니라 **바이너리를 직접 내려주는 URL**을 원한다.
드라이브 공유링크(drive.google.com/file/d/...)는 HTML이라 거부된다.

직접 다운로드 URL:
  https://drive.google.com/uc?export=download&id={FILE_ID}
  (작은 파일만. 큰 파일은 확인 페이지가 뜸)
"""
import json
import sys
import urllib.request
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from shorts.gdrive import upload_file, access_token, load_secrets

DEFAULT_SECRETS = ROOT / "secrets/gdrive.json"
GRAPH_API = "https://www.googleapis.com/drive/v3"


def set_public_permission(file_id: str, token: str) -> None:
    """파일에 공개 읽기 권한 부여 (anyone can view)"""
    url = f"{GRAPH_API}/files/{file_id}/permissions"
    body = json.dumps({"type": "anyone", "role": "reader"}).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        r.read()


def make_public_url(local_path: str | Path, folder_id: str = None,
                    secrets_path: str | Path = DEFAULT_SECRETS) -> str:
    """로컬 파일을 드라이브에 업로드하고 공개 URL을 반환한다.

    folder_id: 업로드할 드라이브 폴더 ID (없으면 기본 폴더)

    Returns: 공개 다운로드 URL
    """
    local_path = Path(local_path)
    if not local_path.exists():
        raise FileNotFoundError(f"파일 없음: {local_path}")

    # 1) 업로드
    result = upload_file(local_path, folder_id=folder_id, secrets_path=secrets_path)
    file_id = result["id"]

    # 2) 공개 권한 부여
    creds = load_secrets(secrets_path)
    token = access_token(creds)
    set_public_permission(file_id, token)

    # 3) 직접 다운로드 URL
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def make_public_urls(local_paths: list[str | Path], folder_id: str = None,
                     secrets_path: str | Path = DEFAULT_SECRETS) -> list[str]:
    """여러 파일을 업로드하고 URL 목록 반환"""
    return [make_public_url(p, folder_id, secrets_path) for p in local_paths]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용: make_public_url.py <파일1> [파일2 ...] [--folder <폴더ID>]")
        sys.exit(1)

    folder_id = None
    files = []

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--folder" and i + 1 < len(sys.argv):
            folder_id = sys.argv[i + 1]
            i += 2
        else:
            files.append(sys.argv[i])
            i += 1

    for f in files:
        url = make_public_url(f, folder_id)
        print(f"{f} → {url}")
