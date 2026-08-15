#!/usr/bin/env python3
"""파일 잠금 시스템 — 충돌 방지 + 히스토리 보존

전략실이 모든 잠금 현황 관리. 기록은 절대 삭제 안 함 — 복구 가능.

파일:
    _locks/active.json — 현재 활성 잠금
    _locks/history.json — 모든 잠금/해제 기록 (영구 보존)

사용법:
    # 잠금 획득
    python3 scripts/file_lock.py lock content/대본.md "유튜브쇼츠방"

    # 잠금 해제
    python3 scripts/file_lock.py unlock content/대본.md "유튜브쇼츠방"

    # 잠금 확인
    python3 scripts/file_lock.py check content/대본.md

    # 전체 현황 (전략실용)
    python3 scripts/file_lock.py status

    # 히스토리 (전략실용)
    python3 scripts/file_lock.py history [파일]

    # 강제 해제 (전략실만)
    python3 scripts/file_lock.py force-unlock content/대본.md
"""
from __future__ import annotations
import json
import socket
import sys
from datetime import datetime
from pathlib import Path

LOCKS_DIR = Path("_locks")
ACTIVE_FILE = LOCKS_DIR / "active.json"
HISTORY_FILE = LOCKS_DIR / "history.json"


def is_bonjin() -> bool:
    """본진/전략실 확인"""
    return "Mac-Studio" in socket.gethostname()


def load_active() -> dict:
    """활성 잠금 로드"""
    LOCKS_DIR.mkdir(exist_ok=True)
    if ACTIVE_FILE.exists():
        return json.loads(ACTIVE_FILE.read_text())
    return {}


def save_active(locks: dict):
    """활성 잠금 저장"""
    LOCKS_DIR.mkdir(exist_ok=True)
    ACTIVE_FILE.write_text(json.dumps(locks, ensure_ascii=False, indent=2))


def load_history() -> list:
    """히스토리 로드"""
    LOCKS_DIR.mkdir(exist_ok=True)
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return []


def append_history(action: str, filepath: str, room: str, note: str = ""):
    """히스토리에 기록 추가 (절대 삭제 안 함)"""
    history = load_history()
    history.append({
        "action": action,
        "file": filepath,
        "room": room,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hostname": socket.gethostname(),
        "note": note
    })
    LOCKS_DIR.mkdir(exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2))


def is_strategy_room(room: str) -> bool:
    """전략기획실 여부"""
    return room in ["전략기획실", "전략실", "본진터미널", "전략방"] or is_bonjin()


def lock_file(filepath: str, room: str) -> tuple[bool, str]:
    """파일 잠금 획득 — 전략실은 우선순위"""
    locks = load_active()

    if filepath in locks:
        owner = locks[filepath]["room"]
        if owner == room:
            return True, f"이미 {room}이 잠금 중"

        # 전략실은 우선순위 — 기존 잠금 밀어냄
        if is_strategy_room(room):
            append_history("priority_override", filepath, room, f"전략실 우선권으로 {owner} 잠금 해제")
            locks[filepath] = {
                "room": room,
                "since": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "hostname": socket.gethostname(),
                "priority": True
            }
            save_active(locks)
            append_history("lock", filepath, room, "전략실 우선권")
            return True, f"⚡ 전략실 우선권: {owner} 잠금 해제 → {room} 획득"

        append_history("lock_blocked", filepath, room, f"충돌: {owner}이 사용 중")
        return False, f"❌ 충돌: {owner}이 사용 중 ({locks[filepath]['since']})"

    locks[filepath] = {
        "room": room,
        "since": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "hostname": socket.gethostname()
    }
    save_active(locks)
    append_history("lock", filepath, room)
    return True, f"✅ 잠금 획득: {filepath}"


def unlock_file(filepath: str, room: str) -> tuple[bool, str]:
    """파일 잠금 해제 (활성에서만 제거, 히스토리는 보존)"""
    locks = load_active()

    if filepath not in locks:
        return True, "이미 해제됨"

    if locks[filepath]["room"] != room and not is_bonjin():
        append_history("unlock_blocked", filepath, room, f"{locks[filepath]['room']}의 잠금")
        return False, f"❌ {locks[filepath]['room']}의 잠금만 해제 가능"

    owner = locks[filepath]["room"]
    del locks[filepath]
    save_active(locks)
    append_history("unlock", filepath, room, f"원래 잠금자: {owner}")
    return True, f"✅ 잠금 해제: {filepath}"


def force_unlock(filepath: str) -> tuple[bool, str]:
    """강제 해제 (전략실만)"""
    if not is_bonjin():
        return False, "❌ 전략실만 강제 해제 가능"

    locks = load_active()
    if filepath in locks:
        owner = locks[filepath]["room"]
        del locks[filepath]
        save_active(locks)
        append_history("force_unlock", filepath, "전략실", f"강제 해제: {owner}의 잠금")
        return True, f"✅ 강제 해제: {filepath} ({owner} 잠금이었음)"
    return True, "이미 해제됨"


def check_file(filepath: str) -> tuple[bool, str]:
    """파일 잠금 확인"""
    locks = load_active()
    if filepath in locks:
        info = locks[filepath]
        return False, f"🔒 {info['room']}이 사용 중 ({info['since']}부터)"
    return True, "✅ 사용 가능"


def show_status():
    """전체 잠금 현황"""
    locks = load_active()

    if not locks:
        print("📭 활성 잠금 없음")
        return

    print(f"📋 활성 잠금 ({len(locks)}개)")
    print("-" * 50)
    for filepath, info in sorted(locks.items()):
        print(f"  🔒 {filepath}")
        print(f"     └ {info['room']} | {info['since']}")


def show_history(filepath: str = None):
    """히스토리 조회"""
    history = load_history()

    if filepath:
        history = [h for h in history if h["file"] == filepath]

    if not history:
        print("📭 기록 없음")
        return

    print(f"📜 히스토리 ({len(history)}건)")
    print("-" * 60)
    for h in history[-20:]:  # 최근 20건
        icon = {"lock": "🔒", "unlock": "🔓", "force_unlock": "⚡", "lock_blocked": "🚫", "unlock_blocked": "🚫"}.get(h["action"], "?")
        print(f"  {icon} {h['time']} | {h['action']:15} | {h['room']}")
        print(f"     └ {h['file']}")
        if h.get("note"):
            print(f"       ({h['note']})")


def main():
    if len(sys.argv) < 2:
        print("사용법: file_lock.py <lock|unlock|check|status|history|force-unlock> [파일] [방이름]")
        return 1

    cmd = sys.argv[1]

    if cmd == "status":
        show_status()
        return 0

    if cmd == "history":
        filepath = sys.argv[2] if len(sys.argv) > 2 else None
        show_history(filepath)
        return 0

    if cmd == "lock":
        if len(sys.argv) < 4:
            print("사용법: file_lock.py lock <파일> <방이름>")
            return 1
        ok, msg = lock_file(sys.argv[2], sys.argv[3])
        print(msg)
        return 0 if ok else 1

    if cmd == "unlock":
        if len(sys.argv) < 4:
            print("사용법: file_lock.py unlock <파일> <방이름>")
            return 1
        ok, msg = unlock_file(sys.argv[2], sys.argv[3])
        print(msg)
        return 0 if ok else 1

    if cmd == "force-unlock":
        if len(sys.argv) < 3:
            print("사용법: file_lock.py force-unlock <파일>")
            return 1
        ok, msg = force_unlock(sys.argv[2])
        print(msg)
        return 0 if ok else 1

    if cmd == "check":
        if len(sys.argv) < 3:
            print("사용법: file_lock.py check <파일>")
            return 1
        ok, msg = check_file(sys.argv[2])
        print(msg)
        return 0 if ok else 1

    print(f"알 수 없는 명령: {cmd}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
