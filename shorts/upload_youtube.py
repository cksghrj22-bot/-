"""유튜브 업로드: OAuth 리프레시 토큰 + 재개형(resumable) 업로드. 표준 라이브러리만 사용.

secrets/youtube.json 형식:
    {
      "client_id": "....apps.googleusercontent.com",
      "client_secret": "...",
      "refresh_token": "..."
    }

refresh_token 발급은 docs/youtube-shorts-pipeline.md 참고.
업로드 1건당 API 할당량 1,600 유닛 (기본 일일 10,000 → 하루 약 6건).
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = (
    "https://www.googleapis.com/upload/youtube/v3/videos"
    "?uploadType=resumable&part=snippet,status"
)


def load_credentials(path: str | Path) -> dict:
    creds = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = {"client_id", "client_secret", "refresh_token"} - creds.keys()
    if missing:
        raise ValueError(f"youtube 자격증명에 누락된 키: {sorted(missing)}")
    return creds


def get_access_token(creds: dict) -> str:
    data = urllib.parse.urlencode(
        {
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": creds["refresh_token"],
            "grant_type": "refresh_token",
        }
    ).encode()
    request = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())["access_token"]


def build_metadata(
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    privacy: str = "private",
    publish_at: str | None = None,
) -> dict:
    """업로드 메타데이터를 만든다. publish_at(RFC3339)을 주면 예약 공개.

    ⛔ 안전장치(2026-07-19 이찬호 지시 "다시 실수 안하게"): publish_at이 과거면 예외.
    과거 시각을 주면 유튜브가 예약이 아니라 **즉시 공개**해버린다(실제 사고: 오늘을 7/18로
    착각해 7/19로 걸었다가 이미 지나 바로 공개됨). 미래인지 코드가 강제 확인한다.
    """
    from datetime import datetime, timezone
    status: dict = {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}
    if publish_at:
        try:
            t = datetime.fromisoformat(publish_at.replace("Z", "+00:00"))
        except ValueError as e:
            raise ValueError(f"publishAt RFC3339 형식 오류: {publish_at!r}") from e
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if t <= now:
            raise ValueError(
                f"publishAt이 과거입니다: {publish_at} (지금 UTC={now.isoformat(timespec='seconds')}). "
                f"과거로 예약하면 유튜브가 즉시 공개해버림 — 미래 시각(UTC)으로 다시 주세요."
            )
        status["privacyStatus"] = "private"  # 예약 공개는 private + publishAt 조합
        status["publishAt"] = publish_at
    return {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": (tags or [])[:30],
            "categoryId": "22",
        },
        "status": status,
    }


def upload(video_path: str | Path, metadata: dict, creds: dict, chunk_size: int = 8 * 1024 * 1024) -> str:
    """영상을 업로드하고 videoId를 반환한다."""
    video_path = Path(video_path)
    token = get_access_token(creds)
    size = video_path.stat().st_size

    # 1) 업로드 세션 시작 → Location 헤더로 업로드 URL 수령
    body = json.dumps(metadata).encode("utf-8")
    request = urllib.request.Request(
        UPLOAD_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Length": str(size),
            "X-Upload-Content-Type": "video/*",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        session_url = response.headers["Location"]

    # 2) 조각 업로드
    with video_path.open("rb") as f:
        offset = 0
        while offset < size:
            chunk = f.read(chunk_size)
            end = offset + len(chunk) - 1
            put = urllib.request.Request(
                session_url,
                data=chunk,
                method="PUT",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Length": str(len(chunk)),
                    "Content-Range": f"bytes {offset}-{end}/{size}",
                },
            )
            try:
                with urllib.request.urlopen(put, timeout=300) as response:
                    return json.loads(response.read())["id"]  # 마지막 조각: 완료 응답
            except urllib.error.HTTPError as exc:
                if exc.code != 308:  # 308 = 조각 수신됨, 계속
                    raise
            offset = end + 1

    raise RuntimeError("업로드가 완료 응답 없이 끝났습니다")
