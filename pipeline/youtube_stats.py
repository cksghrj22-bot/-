"""유튜브 조회수 수집기 — 조합 엔진의 반응 데이터 입력.

secrets/youtube_api_key.txt (API 키), secrets/youtube_channel_id.txt (채널 ID) 필요.
API 키는 공개 데이터 조회 전용 — 업로드는 upload_youtube.py(OAuth)가 담당.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://www.googleapis.com/youtube/v3"


def _get(endpoint: str, params: dict) -> dict:
    url = f"{API}/{endpoint}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def load_secrets(secrets_dir: str | Path = "secrets") -> tuple[str, str]:
    """secrets/ 파일 우선, 없으면 환경 변수(YOUTUBE_API_KEY, YOUTUBE_CHANNEL_ID).

    환경 변수는 클라우드 환경 설정에 등록해두면 모든 새 세션에 자동 주입된다.
    """
    d = Path(secrets_dir)
    key_file = d / "youtube_api_key.txt"
    ch_file = d / "youtube_channel_id.txt"
    key = key_file.read_text(encoding="utf-8").strip() if key_file.exists() else os.environ.get("YOUTUBE_API_KEY", "")
    channel = ch_file.read_text(encoding="utf-8").strip() if ch_file.exists() else os.environ.get("YOUTUBE_CHANNEL_ID", "")
    if not key or not channel:
        raise FileNotFoundError(
            "유튜브 자격증명 없음 — secrets/ 파일 또는 환경 변수(YOUTUBE_API_KEY, YOUTUBE_CHANNEL_ID) 필요"
        )
    return key, channel


def fetch_recent_videos(key: str, channel_id: str, limit: int = 50) -> list[dict]:
    """채널 업로드 재생목록에서 최근 영상 + 조회수/좋아요/댓글을 가져온다."""
    uploads = "UU" + channel_id[2:]  # UC → UU: 업로드 전체 재생목록
    items = _get(
        "playlistItems",
        {"part": "contentDetails", "playlistId": uploads, "maxResults": min(limit, 50), "key": key},
    ).get("items", [])
    ids = [i["contentDetails"]["videoId"] for i in items]
    if not ids:
        return []
    videos = _get(
        "videos",
        {"part": "snippet,statistics", "id": ",".join(ids), "key": key},
    ).get("items", [])
    result = []
    for v in videos:
        stats = v.get("statistics", {})
        result.append(
            {
                "videoId": v["id"],
                "title": v["snippet"]["title"],
                "publishedAt": v["snippet"]["publishedAt"][:10],
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
            }
        )
    return result


def render_report(videos: list[dict], top: int = 15) -> str:
    """조회수 순 마크다운 리포트 — 조합 엔진(prompts/01)의 입력으로 쓴다."""
    ranked = sorted(videos, key=lambda v: -v["views"])[:top]
    lines = ["# 유튜브 반응 리포트 (조회수 순)", ""]
    lines.append("| 순위 | 제목 | 조회수 | 좋아요 | 댓글 | 게시일 |")
    lines.append("|---|---|---|---|---|---|")
    for rank, v in enumerate(ranked, start=1):
        lines.append(
            f"| {rank} | [{v['title']}](https://youtube.com/watch?v={v['videoId']}) "
            f"| {v['views']:,} | {v['likes']:,} | {v['comments']:,} | {v['publishedAt']} |"
        )
    lines.append("")
    lines.append("> 상위 제목들의 공통 키워드·프레임을 조합 엔진(prompts/01) 입력의 '반응 검증 축'으로 사용할 것.")
    return "\n".join(lines)
