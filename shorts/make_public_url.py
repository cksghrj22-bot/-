#!/usr/bin/env python3
"""로컬 파일 → 인스타가 받아갈 수 있는 공개 URL

방법: 구글드라이브에 업로드 + 공개 권한 + 직접 다운로드 URL 반환

인스타 Graph API는 HTML 페이지가 아니라 **바이너리를 직접 내려주는 URL**을 원한다.
드라이브 공유링크(drive.google.com/file/d/...)는 HTML이라 거부된다.

직접 다운로드 URL:
  https://www.googleapis.com/drive/v3/files/{FILE_ID}?alt=media&key={API_KEY}
  또는 OAuth로 인증된 요청

이 스크립트는:
1. 로컬 파일을 드라이브 특정 폴더에 업로드
2. 공개 읽기 권한 부여 (anyone can view)
3. 직접 다운로드 URL 반환
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from shorts.gdrive import upload_file, get_service


def make_public_url(local_path: str | Path, folder_id: str = None) -> str:
    """로컬 파일을 드라이브에 업로드하고 공개 URL을 반환한다.
    
    folder_id: 업로드할 드라이브 폴더 ID (없으면 루트)
    
    Returns: 공개 다운로드 URL
    """
    local_path = Path(local_path)
    if not local_path.exists():
        raise FileNotFoundError(f"파일 없음: {local_path}")
    
    service = get_service()
    
    # 1) 업로드
    from googleapiclient.http import MediaFileUpload
    
    metadata = {"name": local_path.name}
    if folder_id:
        metadata["parents"] = [folder_id]
    
    media = MediaFileUpload(str(local_path), resumable=True)
    file = service.files().create(
        body=metadata,
        media_body=media,
        fields="id,webContentLink"
    ).execute()
    
    file_id = file["id"]
    
    # 2) 공개 권한 부여
    service.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"}
    ).execute()
    
    # 3) 직접 다운로드 URL
    # webContentLink가 있으면 사용, 없으면 직접 구성
    if "webContentLink" in file:
        return file["webContentLink"]
    
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def make_public_urls(local_paths: list[str | Path], folder_id: str = None) -> list[str]:
    """여러 파일을 업로드하고 URL 목록 반환"""
    return [make_public_url(p, folder_id) for p in local_paths]


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
