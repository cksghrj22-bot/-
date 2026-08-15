#!/usr/bin/env python3
"""방 간섭 차단 게이트 — 각 방은 자기 영역만, 다른 방 간섭 금지

각 방은 자기 영역에서 자유롭게 작업.
다른 방 영역 건드리면 차단.
전략기획실만 전체 접근.

pre-commit hook으로 등록:
    echo 'python3 scripts/room_gate.py' >> .git/hooks/pre-commit
"""
from __future__ import annotations
import subprocess
import socket
import sys
from pathlib import Path

# 방별 영역 — 자기 영역만 수정 가능
ROOM_TERRITORY = {
    "낙타자막인스타스레드방": [
        "_out/낙타/",
        "_out/cards/",
        "_out/amton/",
        "content/cards/",
        "scripts/cards/amton_",
        "scripts/cards/nakta_",
        "scripts/film_grade.py",
        "scripts/cards/fonts/",
        "scripts/cards/glyphlib/",
    ],
    "유튜브쇼츠방": [
        "_out/shorts/",
        "content/shorts/",
        "scripts/shorts/",
        "scripts/build_short",
    ],
    "만화연재방": [
        "_out/만화/",
        "_out/연재/",
        "_out/결이/",
        "content/만화/",
        "scripts/cards/comic_",
        "scripts/manga_",
    ],
    "블로그자동화방": [
        "_out/blog/",
        "content/blog/",
        "_publish_jobs/blog_parsed/",
        "scripts/naver_",
        "scripts/blog_",
    ],
    "교육디렉터방": [
        "_out/교육/",
        "content/교육/",
        "scripts/edu_",
    ],
}

# 전략실 = 전체 접근
STRATEGY_ROOMS = ["전략기획및개인업무", "전략기획실", "본진터미널"]

# 공유 영역 (누구나 읽기, 전략실만 수정)
SHARED_ONLY = ["secrets/", "CLAUDE.md", "knowledge/", "_strategy/"]


def is_bonjin() -> bool:
    return "Mac-Studio" in socket.gethostname()


def get_current_room() -> str | None:
    cowork_claude = Path("_cowork_sync/CLAUDE.md")
    if cowork_claude.exists():
        content = cowork_claude.read_text()
        for line in content.split("\n"):
            if "이 방은" in line and "」" in line:
                start = line.find("「")
                end = line.find("」")
                if start > 0 and end > start:
                    return line[start+1:end]
    if is_bonjin():
        return "본진터미널"
    return None


def get_staged_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True
    )
    return result.stdout.strip().split("\n") if result.stdout.strip() else []


def is_in_territory(filepath: str, room: str) -> bool:
    """파일이 해당 방 영역인지"""
    if room in STRATEGY_ROOMS or is_bonjin():
        return True  # 전략실은 전체

    territories = ROOM_TERRITORY.get(room, [])
    for t in territories:
        if filepath.startswith(t):
            return True
    return False


def is_other_room_territory(filepath: str, room: str) -> bool:
    """파일이 다른 방 영역인지"""
    for other_room, territories in ROOM_TERRITORY.items():
        if other_room == room:
            continue
        for t in territories:
            if filepath.startswith(t):
                return True
    return False


def is_shared_only(filepath: str) -> bool:
    """공유 전용 영역인지"""
    for s in SHARED_ONLY:
        if filepath.startswith(s):
            return True
    return False


def main():
    room = get_current_room()
    staged = get_staged_files()

    if not staged or staged == [""]:
        return 0

    # 전략실은 통과
    if room in STRATEGY_ROOMS or is_bonjin():
        print(f"✅ {room} — 전체 접근")
        return 0

    blocked = []
    for f in staged:
        # 공유 전용 영역
        if is_shared_only(f):
            blocked.append(f"공유자원: {f}")
            continue

        # 다른 방 영역
        if is_other_room_territory(f, room):
            blocked.append(f"다른방영역: {f}")
            continue

    if blocked:
        print(f"❌ {room} — 다른 방 간섭 차단")
        for b in blocked[:5]:
            print(f"   {b}")
        if len(blocked) > 5:
            print(f"   ... 외 {len(blocked)-5}개")
        return 1

    print(f"✅ {room} — 자기 영역 OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
