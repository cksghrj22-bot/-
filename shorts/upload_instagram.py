"""인스타그램 릴스 업로드 (Instagram Graph API, 비즈니스/크리에이터 계정 필요).

secrets/instagram.json 형식:
    {
      "access_token": "장기 액세스 토큰",
      "ig_user_id": "인스타그램 비즈니스 계정 ID"
    }

절차: 미디어 컨테이너 생성 → rupload로 영상 전송 → 처리 대기 → 게시.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

GRAPH = "https://graph.facebook.com/v19.0"
RUPLOAD = "https://rupload.facebook.com/ig-api-upload/v19.0"


def load_credentials(path: str | Path) -> dict:
    creds = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = {"access_token", "ig_user_id"} - creds.keys()
    if missing:
        raise ValueError(f"instagram 자격증명에 누락된 키: {sorted(missing)}")
    return creds


def _post(url: str, params: dict) -> dict:
    data = urllib.parse.urlencode(params).encode()
    with urllib.request.urlopen(urllib.request.Request(url, data=data, method="POST"), timeout=60) as r:
        return json.loads(r.read())


def _get(url: str, params: dict) -> dict:
    with urllib.request.urlopen(f"{url}?{urllib.parse.urlencode(params)}", timeout=60) as r:
        return json.loads(r.read())


def upload_reel(video_path: str | Path, caption: str, creds: dict, timeout_sec: int = 600) -> str:
    """릴스를 업로드·게시하고 미디어 ID를 반환한다."""
    video_path = Path(video_path)
    token = creds["access_token"]
    user = creds["ig_user_id"]

    # 1) 컨테이너 생성 (로컬 업로드 모드)
    container = _post(
        f"{GRAPH}/{user}/media",
        {"media_type": "REELS", "upload_type": "resumable", "caption": caption, "access_token": token},
    )
    container_id = container["id"]

    # 2) 영상 바이너리 전송
    data = video_path.read_bytes()
    request = urllib.request.Request(
        f"{RUPLOAD}/{container_id}",
        data=data,
        method="POST",
        headers={
            "Authorization": f"OAuth {token}",
            "offset": "0",
            "file_size": str(len(data)),
        },
    )
    with urllib.request.urlopen(request, timeout=600) as r:
        result = json.loads(r.read())
    if not result.get("success", True):
        raise RuntimeError(f"영상 전송 실패: {result}")

    # 3) 처리 완료 대기
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        status = _get(f"{GRAPH}/{container_id}", {"fields": "status_code", "access_token": token})
        code = status.get("status_code")
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise RuntimeError(f"인스타그램 처리 실패: {status}")
        time.sleep(10)
    else:
        raise TimeoutError("인스타그램 영상 처리 대기 시간 초과")

    # 4) 게시
    published = _post(
        f"{GRAPH}/{user}/media_publish",
        {"creation_id": container_id, "access_token": token},
    )
    return published["id"]
