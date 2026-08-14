#!/usr/bin/env python3
"""자동 커밋 — 커밋 안 된 변경사항 자동 저장

1시간마다 또는 수동 실행 시:
- 변경된 파일 있으면 자동 커밋
- secrets/ 제외 (gitignore)
- 커밋 메시지에 타임스탬프

사용법:
    python3 scripts/auto_commit.py

cron 등록 (매시간):
    0 * * * * cd ~/atnown-content-pipeline && python3 scripts/auto_commit.py >> _logs/auto_commit.log 2>&1

launchd 등록:
    ~/Library/LaunchAgents/com.atnown.autocommit.plist
"""
from __future__ import annotations
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 자동 커밋 대상 경로 (중요 산출물)
AUTO_COMMIT_PATHS = [
    "_ROOMS_LOG.md",
    "_ROOMS.md",
    "knowledge/",
    "content/",
    "_out/",
    "_publish_jobs/",
    "scripts/",
    "prompts/",
]

# 제외
EXCLUDE = [
    "secrets/",
    ".git/",
    "_tmp/",
    "__pycache__/",
]


def get_uncommitted_changes() -> list[str]:
    """커밋 안 된 변경 파일 목록"""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True
    )
    files = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        # " M file.txt" or "?? file.txt" 형태
        status = line[:2]
        filepath = line[3:].strip().strip('"')

        # 제외 대상 체크
        skip = False
        for exc in EXCLUDE:
            if filepath.startswith(exc):
                skip = True
                break
        if skip:
            continue

        # 대상 경로 체크
        for target in AUTO_COMMIT_PATHS:
            if filepath.startswith(target) or filepath == target.rstrip("/"):
                files.append(filepath)
                break

    return files


def auto_commit() -> bool:
    """자동 커밋 실행"""
    files = get_uncommitted_changes()

    if not files:
        print("커밋할 변경사항 없음")
        return False

    print(f"자동 커밋 대상: {len(files)}개")
    for f in files[:10]:
        print(f"  - {f}")
    if len(files) > 10:
        print(f"  ... 외 {len(files) - 10}개")

    # git add
    for f in files:
        subprocess.run(["git", "add", f], capture_output=True)

    # commit
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = f"자동저장 {now} ({len(files)}개 파일)"

    result = subprocess.run(
        ["git", "commit", "-m", msg],
        capture_output=True, text=True
    )

    if result.returncode == 0:
        print(f"✅ 커밋 완료: {msg}")
        return True
    else:
        print(f"❌ 커밋 실패: {result.stderr}")
        return False


def warn_old_uncommitted(days: int = 1) -> list[str]:
    """오래된 uncommitted 파일 경고"""
    import os
    import time

    threshold = time.time() - (days * 86400)
    old_files = []

    files = get_uncommitted_changes()
    for f in files:
        path = Path(f)
        if path.exists():
            mtime = path.stat().st_mtime
            if mtime < threshold:
                age_hours = int((time.time() - mtime) / 3600)
                old_files.append(f"{f} ({age_hours}시간 전)")

    if old_files:
        print(f"\n⚠️ 커밋 안 된 오래된 파일 {len(old_files)}개:")
        for f in old_files:
            print(f"  - {f}")

    return old_files


def main():
    print(f"=== 자동 커밋 ({datetime.now()}) ===")

    # 오래된 파일 경고
    warn_old_uncommitted(days=1)

    # 자동 커밋
    auto_commit()


if __name__ == "__main__":
    main()
