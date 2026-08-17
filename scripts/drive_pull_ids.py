#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""드라이브에서 파일 ID로 다운로드 (재작성 2026-08-14)

원본 소실로 _ROOMS_LOG 기록 기반 복원

드라이브 기본 마운트는 Operation not permitted (TCC)
→ API 경로로 직접 다운로드

사용법:
    python3 scripts/drive_pull_ids.py <file_id> <output_path>
    python3 scripts/drive_pull_ids.py <file_id1,file_id2,...> <output_dir>
"""
from __future__ import annotations
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

def main():
    if len(sys.argv) < 3:
        print("사용법: drive_pull_ids.py <file_id> <output_path>")
        print("        drive_pull_ids.py <file_id1,file_id2,...> <output_dir>")
        return 1

    file_ids = sys.argv[1].split(",")
    output = Path(sys.argv[2])

    from shorts.gdrive import download_file

    if len(file_ids) == 1:
        file_id = file_ids[0]
        print(f"다운로드: {file_id} → {output}")
        download_file(file_id, str(output))
        print(f"✅ 완료: {output}")
    else:
        output.mkdir(parents=True, exist_ok=True)
        for file_id in file_ids:
            out_path = output / f"{file_id}"
            print(f"다운로드: {file_id}")
            download_file(file_id, str(out_path))
        print(f"✅ {len(file_ids)}개 완료")

    return 0

if __name__ == "__main__":
    sys.exit(main())
