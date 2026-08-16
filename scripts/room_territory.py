#!/usr/bin/env python3
"""방별 영역 관리 — 충돌 방지 + 전체 참조

각 방은 자기 영역만 쓰기, 전체는 _out/_index.json에서 참조.

영역:
    유튜브쇼츠방: _out/shorts/, content/shorts/
    낙타방: _out/낙타/, _out/cards/, content/cards/
    전략기획실: 전체 (제한 없음)

사용법:
    # 영역 확인
    python3 scripts/room_territory.py check "유튜브쇼츠방" "_out/shorts/test.mp4"

    # 전체 인덱스 갱신
    python3 scripts/room_territory.py index

    # 전체 산출물 보기
    python3 scripts/room_territory.py list
"""
from __future__ import annotations
import json
import os
import socket
import sys
from datetime import datetime
from pathlib import Path

# 방별 영역 정의 — _ROOMS.md 7방 명부가 정본 (2026-08-16 동기화)
TERRITORIES = {
    # 전략 (전체 접근)
    "전략기획및개인업무": None,
    "전략기획실": None,  # 별칭
    "본진터미널": None,

    # 낙타자막인스타스레드방 (코드 N)
    "낙타자막인스타스레드방": [
        "_out/낙타/",
        "_out/cards/",
        "_out/amton/",
        "_out/스레드/",
        "content/cards/",
        "content/amton/",
        "content/threads/",
    ],

    # 유튜브쇼츠방 (코드 A)
    "유튜브쇼츠방": [
        "_out/shorts/",
        "content/shorts/",
        "content/대본/",
        "_jobs/_done/",
    ],

    # 블로그자동화방
    "블로그자동화방": [
        "_out/blog/",
        "content/blog/",
        "_publish_jobs/blog_parsed/",
    ],

    # 만화연재방 (코드 M)
    "만화연재방": [
        "_out/만화/",
        "_out/연재/",
        "_out/결이/",
        "content/만화/",
    ],

    # 교육디렉터방
    "교육디렉터방": [
        "_out/교육/",
        "content/교육/",
    ],

    # 차노책출판
    "차노책출판": [
        "_out/책/",
        "content/책/",
    ],
}

# 별칭 → 정본 이름 (드라이브 인박스·구 방코드가 다른 이름을 쓴다)
ALIASES = {
    "낙타자막인스타": "낙타자막인스타스레드방",
    "낙타방": "낙타자막인스타스레드방",
    "N": "낙타자막인스타스레드방",
    "인스타방": "낙타자막인스타스레드방",
    "영상방": "유튜브쇼츠방",
    "쇼츠영상방": "유튜브쇼츠방",
    "A": "유튜브쇼츠방",
    "블로그방": "블로그자동화방",
    "D": "블로그자동화방",
    "만화카드방": "만화연재방",
    "M": "만화연재방",
    "교육디렉터실": "교육디렉터방",
    "E": "교육디렉터방",
    "차노책출판방": "차노책출판",
    "P": "차노책출판",
    "전략실": "전략기획및개인업무",
    "기획실": "전략기획및개인업무",
    "전략방": "전략기획및개인업무",
    "S": "전략기획및개인업무",
}


def canon(room: str) -> str:
    """별칭을 정본 방 이름으로."""
    return ALIASES.get(room, room)


# 공유 영역 (잠금 필수)
SHARED_ZONES = [
    "_publish_jobs/",
    "_ROOMS_LOG.md",
    "_ROOMS.md",
]

# 전략기획실이 관리하는 전체 인덱스 (다른 방은 여기서 참조)
INDEX_FILE = Path("_strategy/전체_산출물_인덱스.json")


def is_bonjin() -> bool:
    return "Mac-Studio" in socket.gethostname()


def lookup_in_index(filepath: str) -> str | None:
    """전략실 인덱스에서 파일 정보 조회"""
    if not INDEX_FILE.exists():
        return None

    try:
        index = json.loads(INDEX_FILE.read_text())
        for f in index.get("all_files", []):
            if filepath in f["path"] or f["path"].endswith(filepath):
                room = f.get("room", "미분류")
                size_kb = f["size"] // 1024
                return f"{f['path']} ({size_kb}KB, {f['modified']}, {room})"
    except:
        pass
    return None


def get_territory(room: str) -> list[str] | None:
    """방의 영역 반환. None이면 전체 접근."""
    room = canon(room)
    if is_bonjin() or room in ["전략기획실", "본진터미널", "전략실", "전략기획및개인업무"]:
        return None
    return TERRITORIES.get(room, [])


def check_access(room: str, filepath: str) -> tuple[bool, str]:
    """방이 파일에 접근 가능한지 확인"""
    territory = get_territory(room)

    # 전략실은 전체 접근
    if territory is None:
        return True, "✅ 전략실 — 전체 접근 가능"

    # 공유 영역은 잠금 필요 경고
    for zone in SHARED_ZONES:
        if filepath.startswith(zone) or filepath == zone.rstrip("/"):
            return True, f"⚠️ 공유 영역 — 잠금 권장: {zone}"

    # 자기 영역 체크
    for allowed in territory:
        if filepath.startswith(allowed):
            return True, f"✅ {room} 영역"

    # 영역 밖 → 전략실 인덱스 참조 안내
    index_info = lookup_in_index(filepath)
    if index_info:
        return False, f"❌ {room} 영역 밖 → 전략실 참조:\n   📍 {index_info}"
    return False, f"❌ {room} 영역 밖. 전략실 인덱스 확인: _strategy/전체_산출물_인덱스.json"


def build_index() -> dict:
    """전체 산출물 인덱스 생성"""
    index = {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "rooms": {},
        "all_files": []
    }

    out_dir = Path("_out")
    if not out_dir.exists():
        return index

    for room, territories in TERRITORIES.items():
        if territories is None:
            continue
        room_files = []
        for territory in territories:
            if territory.startswith("_out/"):
                folder = Path(territory)
                if folder.exists():
                    for f in folder.rglob("*"):
                        if f.is_file() and not f.name.startswith("."):
                            room_files.append({
                                "path": str(f),
                                "size": f.stat().st_size,
                                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                            })
        if room_files:
            index["rooms"][room] = room_files
            index["all_files"].extend(room_files)

    # 미분류 파일
    classified = set(f["path"] for f in index["all_files"])
    for f in out_dir.rglob("*"):
        if f.is_file() and not f.name.startswith(".") and str(f) not in classified:
            index["all_files"].append({
                "path": str(f),
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                "room": "미분류"
            })

    # 저장
    INDEX_FILE.parent.mkdir(exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=2))

    return index


def show_list():
    """전체 산출물 목록"""
    if not INDEX_FILE.exists():
        print("인덱스 없음. 먼저 실행: room_territory.py index")
        return

    index = json.loads(INDEX_FILE.read_text())

    print(f"📦 전체 산출물 ({index['updated']} 기준)")
    print("=" * 50)

    for room, files in index.get("rooms", {}).items():
        print(f"\n🏠 {room} ({len(files)}개)")
        for f in files[:5]:
            size_kb = f["size"] // 1024
            print(f"   {f['path']} ({size_kb}KB)")
        if len(files) > 5:
            print(f"   ... 외 {len(files) - 5}개")

    # 미분류
    unclassified = [f for f in index.get("all_files", []) if f.get("room") == "미분류"]
    if unclassified:
        print(f"\n❓ 미분류 ({len(unclassified)}개)")
        for f in unclassified[:5]:
            print(f"   {f['path']}")


def main():
    if len(sys.argv) < 2:
        print("사용법: room_territory.py <check|index|list> [방] [파일]")
        return 1

    cmd = sys.argv[1]

    if cmd == "check":
        if len(sys.argv) < 4:
            print("사용법: room_territory.py check <방> <파일>")
            return 1
        ok, msg = check_access(sys.argv[2], sys.argv[3])
        print(msg)
        return 0 if ok else 1

    if cmd == "index":
        index = build_index()
        print(f"✅ 인덱스 갱신: {len(index['all_files'])}개 파일")
        print(f"   저장: {INDEX_FILE}")
        return 0

    if cmd == "list":
        show_list()
        return 0

    if cmd == "territories":
        print("📋 방별 영역:")
        for room, t in TERRITORIES.items():
            if t is None:
                print(f"  {room}: 전체")
            else:
                print(f"  {room}: {t}")
        return 0

    print(f"알 수 없는 명령: {cmd}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
