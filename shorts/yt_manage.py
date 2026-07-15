"""유튜브 채널 관리 — 재생목록 생성/이름변경/분류 + 채널 소개문 교체.

편집 권한 토큰: secrets/youtube_ssl.json (스코프 https://www.googleapis.com/auth/youtube).
기기 인증으로 발급 — force-ssl은 기기 플로우 불가, `youtube`(계정 관리)가 재생목록·소개문·삭제를 커버.

읽기 전용 점검:
    python3 -m shorts.yt_manage inventory
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

SSL_SECRETS = "secrets/youtube_ssl.json"
API = "https://www.googleapis.com/youtube/v3"


def access_token(path: str = SSL_SECRETS) -> str:
    c = json.loads(Path(path).read_text(encoding="utf-8"))
    body = urllib.parse.urlencode({
        "client_id": c["client_id"], "client_secret": c["client_secret"],
        "refresh_token": c["refresh_token"], "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    return json.load(urllib.request.urlopen(req, timeout=30))["access_token"]


def _get(at: str, path: str, params: dict) -> dict:
    url = f"{API}/{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + at})
    return json.load(urllib.request.urlopen(req, timeout=30))


def _send(at: str, method: str, path: str, params: dict, body: dict) -> dict:
    url = f"{API}/{path}?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Authorization": "Bearer " + at, "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))


def list_playlists(at: str) -> list[dict]:
    out, page = [], None
    while True:
        p = {"part": "snippet,contentDetails", "mine": "true", "maxResults": 50}
        if page:
            p["pageToken"] = page
        r = _get(at, "playlists", p)
        out += r.get("items", [])
        page = r.get("nextPageToken")
        if not page:
            break
    return out


def list_items(at: str, playlist_id: str) -> list[dict]:
    out, page = [], None
    while True:
        p = {"part": "snippet,contentDetails", "playlistId": playlist_id, "maxResults": 50}
        if page:
            p["pageToken"] = page
        r = _get(at, "playlistItems", p)
        out += r.get("items", [])
        page = r.get("nextPageToken")
        if not page:
            break
    return out


def create_playlist(at: str, title: str, desc: str = "", privacy: str = "public") -> dict:
    return _send(at, "POST", "playlists", {"part": "snippet,status"},
                 {"snippet": {"title": title, "description": desc},
                  "status": {"privacyStatus": privacy}})


def rename_playlist(at: str, playlist_id: str, title: str, desc: str | None = None) -> dict:
    snip = {"title": title}
    if desc is not None:
        snip["description"] = desc
    return _send(at, "PUT", "playlists", {"part": "snippet"},
                 {"id": playlist_id, "snippet": snip})


def add_video(at: str, playlist_id: str, video_id: str) -> dict:
    return _send(at, "POST", "playlistItems", {"part": "snippet"},
                 {"snippet": {"playlistId": playlist_id,
                              "resourceId": {"kind": "youtube#video", "videoId": video_id}}})


def update_channel_description(at: str, channel_id: str, description: str) -> dict:
    return _send(at, "PUT", "channels", {"part": "brandingSettings"},
                 {"id": channel_id, "brandingSettings": {"channel": {"description": description}}})


def _inventory(at: str) -> None:
    pls = list_playlists(at)
    for pl in pls:
        cnt = pl["contentDetails"]["itemCount"]
        print(f"[{pl['id']}] {pl['snippet']['title']}  · {cnt}편")


if __name__ == "__main__":
    at = access_token()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "inventory"
    if cmd == "inventory":
        _inventory(at)
    else:
        print("알 수 없는 명령:", cmd)
