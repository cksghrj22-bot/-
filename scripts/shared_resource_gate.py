#!/usr/bin/env python3
"""공유 자원 게이트 — 전략실만 수정 가능, 업무실은 읽기만

이 스크립트를 git pre-commit hook으로 등록하면
secrets/, scripts/, CLAUDE.md, knowledge/ 수정 시 방 체크.

사용법:
    python3 scripts/shared_resource_gate.py [--check-only]

pre-commit hook 등록:
    echo 'python3 scripts/shared_resource_gate.py' >> .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

# 공유 자원 경로
SHARED_PATHS = [
    "secrets/",
    "scripts/",
    "CLAUDE.md",
    "knowledge/",
]

# 전략실만 수정 가능
ALLOWED_ROOMS = ["전략실", "전략기획방", "본진터미널", "전략기획및개인업무"]

# 각 방별 자기 줄기 코드 예외 (이 파일들은 해당 방이 직접 커밋 가능)
ROOM_OWN_CODE = {
    "낙타자막인스타스레드방": [
        "scripts/cards/amton_",
        "scripts/cards/nakta_",
        "scripts/film_grade.py",
        "scripts/cards/fonts/",
        "scripts/cards/glyphlib/",
    ],
    "유튜브쇼츠방": [
        "scripts/shorts/",
        "scripts/build_short",
    ],
    "만화연재방": [
        "scripts/cards/comic_",
        "scripts/manga_",
    ],
    "블로그자동화방": [
        "scripts/naver_",
        "scripts/blog_",
    ],
    "교육디렉터방": [
        "scripts/edu_",
    ],
}


def get_staged_files() -> list[str]:
    """staged된 파일 목록"""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True
    )
    return result.stdout.strip().split("\n") if result.stdout.strip() else []


def is_shared_resource(path: str, room: str = None) -> bool:
    """공유 자원인지 확인 — 각 방 자기 코드는 예외"""
    # 먼저 공유 자원인지 체크
    is_shared = False
    for shared in SHARED_PATHS:
        if path.startswith(shared) or path == shared.rstrip("/"):
            is_shared = True
            break

    if not is_shared:
        return False

    # 자기 방 코드면 예외
    if room and room in ROOM_OWN_CODE:
        for own_prefix in ROOM_OWN_CODE[room]:
            if path.startswith(own_prefix):
                return False  # 자기 코드는 공유자원 아님

    return True


def get_current_room() -> str | None:
    """현재 방 이름 확인 (코워크 방이면 방 이름, 본진이면 본진터미널)"""
    # 코워크 방 확인
    cowork_claude = Path("_cowork_sync/CLAUDE.md")
    if cowork_claude.exists():
        content = cowork_claude.read_text()
        for line in content.split("\n"):
            if line.startswith("# 이 방은"):
                # "# 이 방은 「유튜브쇼츠방」이다" 형태
                start = line.find("「")
                end = line.find("」")
                if start > 0 and end > start:
                    return line[start+1:end]

    # 본진 확인
    import socket
    hostname = socket.gethostname()
    if "Mac-Studio" in hostname:
        return "본진터미널"

    return None


def main():
    check_only = "--check-only" in sys.argv

    room = get_current_room()
    staged = get_staged_files()
    shared_modified = [f for f in staged if is_shared_resource(f, room)]

    if not shared_modified:
        print("✅ 공유 자원 수정 없음")
        return 0
    print(f"현재 방: {room or '알 수 없음'}")
    print(f"수정된 공유 자원: {shared_modified}")

    if room in ALLOWED_ROOMS:
        print(f"✅ {room}은(는) 공유 자원 수정 가능")
        return 0

    print(f"❌ {room}은(는) 공유 자원 수정 불가")
    print(f"   전략실에 요청하세요: _cowork_sync/요청큐.md")

    if check_only:
        return 1

    # pre-commit hook으로 실행 시 커밋 차단
    return 1


if __name__ == "__main__":
    sys.exit(main())
