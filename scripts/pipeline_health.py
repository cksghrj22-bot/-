#!/usr/bin/env python3
"""파이프라인 전체 헬스 체크 — 한 번에 모든 문제 확인

본진터미널 시작할 때 이것만 돌리면 전체 상태 파악.

사용법:
    python3 scripts/pipeline_health.py
"""
from __future__ import annotations
import json
import os
import socket
import subprocess
from datetime import datetime
from pathlib import Path


def check_identity() -> tuple[str, bool]:
    """본진 확인"""
    hostname = socket.gethostname()
    is_bonjin = "Mac-Studio" in hostname
    return hostname, is_bonjin


def check_daemons() -> dict[str, dict]:
    """launchd 데몬 상태"""
    result = subprocess.run(
        ["launchctl", "list"],
        capture_output=True, text=True
    )
    daemons = {}
    for line in result.stdout.split("\n"):
        if "atnown" not in line:
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            pid = parts[0]
            exit_code = parts[1]
            label = parts[2]
            daemons[label] = {
                "pid": pid if pid != "-" else None,
                "exit_code": int(exit_code) if exit_code != "-" else None,
                "running": pid != "-" and int(pid) > 0
            }
    return daemons


def check_connections() -> dict[str, bool]:
    """연결 상태"""
    secrets = Path("secrets")
    return {
        "instagram": (secrets / "instagram.json").exists(),
        "youtube": (secrets / "youtube.json").exists(),
        "gdrive": (secrets / "gdrive.json").exists(),
        "elevenlabs": (secrets / "elevenlabs.json").exists(),
    }


def check_uncommitted() -> list[str]:
    """커밋 안 된 중요 파일"""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True
    )
    important = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        filepath = line[3:].strip().strip('"')
        if any(filepath.startswith(p) for p in ["knowledge/", "scripts/", "content/", "_ROOMS"]):
            important.append(filepath)
    return important


def check_logs() -> dict[str, str]:
    """최근 로그"""
    logs = {}
    for log_file in Path("_logs").glob("*.log"):
        try:
            content = log_file.read_text()
            lines = content.strip().split("\n")
            logs[log_file.name] = lines[-1][:80] if lines else "(빈 파일)"
        except:
            logs[log_file.name] = "(읽기 실패)"
    return logs


def check_inbox() -> dict[str, int]:
    """inbox 상태"""
    return {
        "_terminal_inbox": len(list(Path("_terminal_inbox").glob("*.json"))),
        "_terminal_inbox/_done": len(list(Path("_terminal_inbox/_done").glob("*.json"))) if Path("_terminal_inbox/_done").exists() else 0,
        "_publish_jobs": len(list(Path("_publish_jobs").glob("*.json"))) if Path("_publish_jobs").exists() else 0,
    }


def main():
    print("=" * 60)
    print("🏥 파이프라인 헬스 체크")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 정체성
    hostname, is_bonjin = check_identity()
    icon = "✅" if is_bonjin else "⚠️"
    print(f"\n{icon} 정체: {hostname}")
    if is_bonjin:
        print("   → 본진터미널")
    else:
        print("   → 코워크 (공유자원 수정 금지)")

    # 2. 데몬
    print("\n📡 데몬 상태:")
    daemons = check_daemons()
    running = 0
    for label, status in sorted(daemons.items()):
        if status["running"]:
            running += 1
            print(f"   ✅ {label.replace('com.atnown.', '')} (PID {status['pid']})")
        elif status["exit_code"] and status["exit_code"] > 0:
            print(f"   ❌ {label.replace('com.atnown.', '')} (exit {status['exit_code']})")
        else:
            print(f"   ⏸️  {label.replace('com.atnown.', '')} (대기)")
    print(f"   → {running}/{len(daemons)} 실행 중")

    # 3. 연결
    print("\n🔌 API 연결:")
    conns = check_connections()
    for key, ok in conns.items():
        icon = "✅" if ok else "❌"
        print(f"   {icon} {key}")

    # 4. 커밋 안 된 파일
    uncommitted = check_uncommitted()
    if uncommitted:
        print(f"\n⚠️ 커밋 안 된 중요 파일 ({len(uncommitted)}개):")
        for f in uncommitted[:5]:
            print(f"   - {f}")
        if len(uncommitted) > 5:
            print(f"   ... 외 {len(uncommitted) - 5}개")
    else:
        print("\n✅ 중요 파일 모두 커밋됨")

    # 5. inbox
    inbox = check_inbox()
    print("\n📥 inbox:")
    for name, count in inbox.items():
        print(f"   {name}: {count}개")

    # 6. 최근 로그
    print("\n📝 최근 로그:")
    logs = check_logs()
    for name, last_line in list(logs.items())[:3]:
        print(f"   {name}: {last_line[:50]}...")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
