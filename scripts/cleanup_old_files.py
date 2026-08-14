#!/usr/bin/env python3
"""오래된 파일 자동 정리 — 한 달 이상 안 쓴 임시 파일 삭제

대상 폴더:
- _tmp/
- _out/preview/
- _jobs/_done/ (30일 이상)

제외:
- _out/ 산출물 (발행 전까지 유지)
- _publish_jobs/ (발행 대기)
- secrets/, scripts/, knowledge/ (영구 보존)

사용법:
    python3 scripts/cleanup_old_files.py [--dry-run]

cron 등록 (매주 일요일 새벽 3시):
    0 3 * * 0 cd ~/atnown-content-pipeline && python3 scripts/cleanup_old_files.py >> _logs/cleanup.log 2>&1
"""
from __future__ import annotations
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# 정리 대상 폴더와 보존 기간 (일)
CLEANUP_TARGETS = {
    "_tmp": 7,           # 1주일
    "_out/preview": 14,  # 2주일
    "_jobs/_done": 30,   # 1달
    "_terminal_inbox/_done": 30,  # 1달
}

# 절대 삭제 금지
PROTECTED = [
    "secrets/",
    "scripts/",
    "knowledge/",
    "prompts/",
    "content/",
    "_publish_jobs/",
    ".git/",
]


def is_protected(path: Path) -> bool:
    """보호 대상인지 확인"""
    path_str = str(path)
    return any(path_str.startswith(p) or f"/{p}" in path_str for p in PROTECTED)


def get_age_days(path: Path) -> float:
    """파일의 마지막 수정일로부터 경과 일수"""
    mtime = path.stat().st_mtime
    return (time.time() - mtime) / 86400


def cleanup(dry_run: bool = False) -> dict:
    """오래된 파일 정리"""
    result = {"deleted": [], "skipped": [], "errors": []}

    for folder, max_days in CLEANUP_TARGETS.items():
        folder_path = Path(folder)
        if not folder_path.exists():
            continue

        for item in folder_path.rglob("*"):
            if not item.is_file():
                continue
            if is_protected(item):
                continue

            try:
                age = get_age_days(item)
                if age > max_days:
                    if dry_run:
                        print(f"[DRY-RUN] 삭제 예정: {item} ({age:.1f}일)")
                        result["skipped"].append(str(item))
                    else:
                        item.unlink()
                        print(f"삭제: {item} ({age:.1f}일)")
                        result["deleted"].append(str(item))
            except Exception as e:
                result["errors"].append(f"{item}: {e}")

    return result


def main():
    dry_run = "--dry-run" in sys.argv

    print(f"=== 오래된 파일 정리 시작 ({datetime.now()}) ===")
    if dry_run:
        print("[DRY-RUN 모드 - 실제 삭제 안 함]")

    result = cleanup(dry_run)

    print(f"\n=== 결과 ===")
    print(f"삭제: {len(result['deleted'])}개")
    print(f"스킵: {len(result['skipped'])}개")
    print(f"에러: {len(result['errors'])}개")

    if result["errors"]:
        print("\n에러:")
        for e in result["errors"]:
            print(f"  {e}")


if __name__ == "__main__":
    main()
