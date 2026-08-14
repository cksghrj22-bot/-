#!/usr/bin/env python3
"""세션 시작 자동 체크 — 방 정체성, 최근 발행, 연결 상태 확인

새 세션 시작할 때 이 스크립트 실행하면:
1. 방 정체성 확인 (본진/코워크)
2. 최근 발행 내역과 로그 대조
3. 연결 상태 확인 (인스타, 유튜브, 드라이브)
4. 누락된 로그 있으면 경고

사용법:
    python3 scripts/session_init.py
"""
from __future__ import annotations
import json
import socket
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def check_identity() -> str:
    """본진/코워크 확인"""
    hostname = socket.gethostname()
    if "Mac-Studio" in hostname:
        return "본진터미널 (Mac Studio)"

    cowork = Path("_cowork_sync/CLAUDE.md")
    if cowork.exists():
        content = cowork.read_text()
        for line in content.split("\n"):
            if "이 방은" in line and "」" in line:
                start = line.find("「")
                end = line.find("」")
                if start > 0 and end > start:
                    return f"코워크: {line[start+1:end]}"
    return "알 수 없음"


def check_recent_posts() -> list[dict]:
    """인스타 최근 게시물 확인"""
    try:
        creds = json.loads(Path("secrets/instagram.json").read_text())
        token = creds["access_token"]
        user = creds["ig_user_id"]
        url = f"https://graph.facebook.com/v19.0/{user}/media?fields=id,caption,timestamp&limit=5&access_token={token}"
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.loads(r.read()).get("data", [])
    except Exception as e:
        return []


def check_logs() -> list[str]:
    """_ROOMS_LOG.md에서 최근 발행 기록"""
    log_file = Path("_ROOMS_LOG.md")
    if not log_file.exists():
        return []
    content = log_file.read_text()
    lines = []
    for line in content.split("\n"):
        if "발행" in line and line.startswith("- `"):
            lines.append(line)
        if len(lines) >= 5:
            break
    return lines


def check_connections() -> dict:
    """연결 상태 확인"""
    status = {}
    secrets = Path("secrets")

    status["instagram"] = (secrets / "instagram.json").exists()
    status["youtube"] = (secrets / "youtube.json").exists()
    status["gdrive"] = (secrets / "gdrive.json").exists()
    status["elevenlabs"] = (secrets / "elevenlabs.json").exists()

    return status


def main():
    print("=" * 50)
    print("세션 시작 자동 체크")
    print("=" * 50)

    # 1. 방 정체성
    identity = check_identity()
    print(f"\n🏠 정체: {identity}")

    # 2. 연결 상태
    print("\n🔌 연결 상태:")
    conns = check_connections()
    for key, ok in conns.items():
        icon = "✅" if ok else "❌"
        print(f"   {icon} {key}")

    # 3. 최근 인스타 발행
    print("\n📸 최근 인스타 발행:")
    posts = check_recent_posts()
    if posts:
        for p in posts[:3]:
            ts = p.get("timestamp", "")[:10]
            cap = (p.get("caption") or "")[:30].replace("\n", " ")
            print(f"   {ts} | {cap}...")
    else:
        print("   (확인 불가)")

    # 4. 로그 기록
    print("\n📝 최근 로그 (발행):")
    logs = check_logs()
    if logs:
        for log in logs[:3]:
            print(f"   {log[:80]}...")
    else:
        print("   (없음)")

    # 5. 누락 경고
    if posts and logs:
        post_dates = set(p.get("timestamp", "")[:10] for p in posts)
        log_dates = set()
        for log in logs:
            if "`" in log:
                date_part = log.split("`")[1][:5]  # MM-DD
                log_dates.add(f"2026-{date_part}")

        missing = post_dates - log_dates
        if missing:
            print(f"\n⚠️ 로그 누락 의심: {missing}")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
