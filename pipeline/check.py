"""연결 진단 — 연동이 제일 먼저다. 모든 연결의 상태를 한 번에 점검한다.

사용: python3 -m pipeline check
어느 기기에서 실행하느냐에 따라 결과가 다르다 (본진 Mac vs 클라우드 샌드박스).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def _reach(url: str, timeout: int = 6) -> bool:
    try:
        req = urllib.request.Request(url, method="HEAD")
        urllib.request.urlopen(req, timeout=timeout)
        return True
    except urllib.error.HTTPError:
        return True  # 서버가 응답했다면 네트워크는 뚫린 것 (4xx여도 도달)
    except Exception:
        return False


def check_all(secrets_dir: str | Path = "secrets", index_path: str | Path = "data/index.json") -> list[tuple[str, str, str]]:
    """(항목, 상태, 설명) 리스트를 반환한다. 상태: OK / 대기 / 차단 / 없음"""
    s = Path(secrets_dir)
    results: list[tuple[str, str, str]] = []

    # 1) 유튜브 조회 (API 키) — 파일 우선, 없으면 환경 변수
    import os

    key_file = s / "youtube_api_key.txt"
    key = key_file.read_text(encoding="utf-8").strip() if key_file.exists() else os.environ.get("YOUTUBE_API_KEY", "")
    if key:
        try:
            q = urllib.parse.urlencode({"part": "id", "id": "dQw4w9WgXcQ", "key": key})
            urllib.request.urlopen(f"https://www.googleapis.com/youtube/v3/videos?{q}", timeout=8)
            results.append(("유튜브 조회수 API", "OK", "키 유효, 네트워크 도달"))
        except urllib.error.HTTPError as e:
            results.append(("유튜브 조회수 API", "차단", f"키 또는 권한 문제 (HTTP {e.code})"))
        except Exception:
            results.append(("유튜브 조회수 API", "차단", "네트워크 차단 (이 기기에서 googleapis 접근 불가)"))
    else:
        results.append(("유튜브 조회수 API", "없음", "secrets 파일도 YOUTUBE_API_KEY 환경 변수도 없음"))

    # 2) 유튜브 업로드 (OAuth)
    oauth_file = s / "youtube.json"
    if oauth_file.exists():
        try:
            creds = json.loads(oauth_file.read_text(encoding="utf-8"))
            missing = {"client_id", "client_secret", "refresh_token"} - creds.keys()
            if missing:
                results.append(("유튜브 업로드 OAuth", "대기", f"누락 필드: {sorted(missing)}"))
            else:
                results.append(("유튜브 업로드 OAuth", "OK", "자격증명 형식 유효 (실업로드는 shorts run에서)"))
        except json.JSONDecodeError:
            results.append(("유튜브 업로드 OAuth", "대기", "JSON 형식 오류"))
    else:
        results.append(("유튜브 업로드 OAuth", "없음", "secrets/youtube.json 없음 — 본진 키 복사 필요"))

    # 3) 인스타그램
    ig_file = s / "instagram.json"
    if ig_file.exists():
        try:
            creds = json.loads(ig_file.read_text(encoding="utf-8"))
            missing = {"access_token", "ig_user_id"} - creds.keys()
            status = ("대기", f"누락 필드: {sorted(missing)}") if missing else ("OK", "자격증명 형식 유효")
            results.append(("인스타그램 API", *status))
        except json.JSONDecodeError:
            results.append(("인스타그램 API", "대기", "JSON 형식 오류"))
    else:
        results.append(("인스타그램 API", "없음", "secrets/instagram.json 없음 — Meta 앱에서 토큰 발급 필요"))

    # 3.5) 일레븐랩스 보이스클론 TTS (코드방/백업 렌더용 — 정본은 본진 Creator OS)
    el_file = s / "elevenlabs.json"
    if el_file.exists():
        try:
            creds = json.loads(el_file.read_text(encoding="utf-8"))
            missing = {"api_key", "voice_id"} - creds.keys()
            if missing:
                results.append(("일레븐랩스 TTS", "대기", f"누락 필드: {sorted(missing)}"))
            elif _reach("https://api.elevenlabs.io/v1/models"):
                results.append(("일레븐랩스 TTS", "OK", "키 형식 유효, 네트워크 도달"))
            else:
                results.append(("일레븐랩스 TTS", "차단", "키는 있으나 api.elevenlabs.io 차단 — 본진에선 사용 가능"))
        except json.JSONDecodeError:
            results.append(("일레븐랩스 TTS", "대기", "JSON 형식 오류"))
    else:
        results.append(("일레븐랩스 TTS", "없음", "secrets/elevenlabs.json 없음 — API 키+voice_id 발급 필요"))

    # 4) 네트워크 (뉴스·메타·일레븐랩스)
    results.append(("네트워크: 뉴스(RSS)", "OK" if _reach("https://www.yna.co.kr") else "차단", "yna.co.kr"))
    results.append(("네트워크: 메타", "OK" if _reach("https://graph.facebook.com") else "차단", "graph.facebook.com"))
    results.append(("네트워크: 일레븐랩스", "OK" if _reach("https://api.elevenlabs.io/v1/models") else "차단", "api.elevenlabs.io"))

    # 5) 지식 인덱스
    idx = Path(index_path)
    if idx.exists():
        chunks = len(json.loads(idx.read_text(encoding="utf-8")).get("chunks", []))
        obsidian = sum(
            1 for c in json.loads(idx.read_text(encoding="utf-8"))["chunks"] if str(c.get("source", "")).startswith("obsidian:")
        )
        note = f"청크 {chunks}개" + (f", 옵시디언 {obsidian}개 포함" if obsidian else " — 옵시디언 미연동 (add-vault 필요)")
        results.append(("지식 인덱스", "OK" if chunks else "대기", note))
    else:
        results.append(("지식 인덱스", "없음", "data/index.json 없음 — pipeline add 실행 필요"))

    return results


def render(results: list[tuple[str, str, str]]) -> str:
    icon = {"OK": "✅", "대기": "🔶", "차단": "🚫", "없음": "❌"}
    lines = ["🔗 연결 진단 (연동이 제일 먼저다)", ""]
    for name, status, note in results:
        lines.append(f"{icon.get(status, '·')} {name}: {status} — {note}")
    return "\n".join(lines)
