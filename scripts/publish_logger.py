#!/usr/bin/env python3
"""발행 로거 — 발행 후 자동으로 _ROOMS_LOG.md에 기록

사용법:
    python3 scripts/publish_logger.py --platform instagram --room 유튜브쇼츠방 --caption "캡션..."

발행 스크립트에서 호출:
    from scripts.publish_logger import log_publish
    log_publish("instagram", "유튜브쇼츠방", "부분펌4", media_id="...")
"""
from __future__ import annotations
import sys
from datetime import datetime
from pathlib import Path


def log_publish(
    platform: str,
    room: str,
    title: str,
    media_id: str | None = None,
    caption: str | None = None,
) -> None:
    """발행 기록을 _ROOMS_LOG.md에 추가"""
    log_file = Path("_ROOMS_LOG.md")
    if not log_file.exists():
        print("❌ _ROOMS_LOG.md 없음")
        return

    now = datetime.now().strftime("%m-%d %H:%M")
    cap_preview = (caption or "")[:30].replace("\n", " ")

    entry = f"- `{now}` **{room}** — {title} {platform} 발행."
    if media_id:
        entry += f" media_id={media_id}."
    if cap_preview:
        entry += f" 캡션 「{cap_preview}...」"
    entry += "\n"

    content = log_file.read_text()

    # 헤더 다음에 삽입
    header_end = content.find("\n\n-")
    if header_end == -1:
        # 첫 기록
        header_end = content.find("\n\n")
        if header_end == -1:
            header_end = len(content)

    # 헤더와 첫 기록 사이에 삽입
    insert_pos = content.find("\n- `")
    if insert_pos == -1:
        # 기록이 없으면 끝에 추가
        new_content = content.rstrip() + "\n\n" + entry
    else:
        new_content = content[:insert_pos] + "\n" + entry + content[insert_pos+1:]

    log_file.write_text(new_content)
    print(f"✅ 발행 기록 추가: {entry.strip()}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", required=True)
    parser.add_argument("--room", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--media-id")
    parser.add_argument("--caption")
    args = parser.parse_args()

    log_publish(args.platform, args.room, args.title, args.media_id, args.caption)


if __name__ == "__main__":
    main()
