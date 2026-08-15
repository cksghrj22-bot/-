#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""낙타 자막바 카드 — 게이트 (규격 검사 + 자동 로그).

쓰는 법:
    python3 scripts/cards/nakta_gate.py <폴더>
    → 통과 exit 0 / 탈락 exit 1

TODO: 규격이 정해지면 검사 추가
"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime


def log_to_rooms(msg: str):
    """_ROOMS_LOG.md에 자동 기록."""
    log_path = Path(__file__).parent.parent.parent / "_ROOMS_LOG.md"
    ts = datetime.now().strftime("%m-%d %H:%M")
    line = f"- `{ts}` **낙타자막인스타** — {msg}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)
    print(f"[로그 자동기록] {line.strip()}")


def main() -> int:
    if len(sys.argv) < 2:
        print("사용법: nakta_gate.py <폴더>")
        return 2

    tgt = Path(sys.argv[1])
    if not tgt.is_dir():
        print(f"[탈락] {tgt} 폴더 아님")
        log_to_rooms(f"게이트 탈락. {tgt}. 폴더 아님.")
        return 1

    images = list(tgt.glob("*.png")) + list(tgt.glob("*.jpg"))
    if not images:
        print(f"[탈락] {tgt} 에 이미지 없음")
        log_to_rooms(f"게이트 탈락. {tgt}. 이미지 없음.")
        return 1

    print(f"== 낙타 게이트: {tgt.name} ==")
    print(f"  이미지 {len(images)}장")

    # TODO: 규격 검사 추가 (해상도, 자막 위치 등)
    # 지금은 이미지 존재만 확인

    fails = []
    # 규격 검사 코드 여기에 추가

    if fails:
        print("\n[게이트 탈락]")
        for f in fails:
            print(f"   {f}")
        log_to_rooms(f"게이트 탈락. {tgt.name}. {len(images)}장. 사유: {fails[0][:50]}...")
        return 1

    print("[통과] 이미지 존재 확인")
    log_to_rooms(f"게이트 통과. {tgt.name}. {len(images)}장. **형 확인 후 발행 대기.**")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
