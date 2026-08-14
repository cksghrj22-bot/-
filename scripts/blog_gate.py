#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""블로그 원고 — 게이트 (규격 검사 + 자동 로그).

쓰는 법:
    python3 scripts/blog_gate.py <원고.md>
    → 통과 exit 0 / 탈락 exit 1

TODO: 규격이 정해지면 검사 추가 (글자 수, 소제목 수, 서식 등)
"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime


def log_to_rooms(msg: str):
    """_ROOMS_LOG.md에 자동 기록."""
    log_path = Path(__file__).parent.parent / "_ROOMS_LOG.md"
    ts = datetime.now().strftime("%m-%d %H:%M")
    line = f"- `{ts}` **블로그자동화방** — {msg}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)
    print(f"[로그 자동기록] {line.strip()}")


def main() -> int:
    if len(sys.argv) < 2:
        print("사용법: blog_gate.py <원고.md>")
        return 2

    tgt = Path(sys.argv[1])
    if not tgt.exists():
        print(f"[탈락] {tgt} 파일 없음")
        log_to_rooms(f"게이트 탈락. {tgt}. 파일 없음.")
        return 1

    text = tgt.read_text(encoding="utf-8")
    chars = len(text)

    print(f"== 블로그 게이트: {tgt.name} ==")
    print(f"  글자 수: {chars}")

    # TODO: 규격 검사 추가 (글자 수 범위, 소제목 수, 서식 등)
    # 지금은 파일 존재만 확인

    fails = []
    # 규격 검사 코드 여기에 추가

    if fails:
        print("\n[게이트 탈락]")
        for f in fails:
            print(f"   {f}")
        log_to_rooms(f"게이트 탈락. {tgt.name}. {chars}자. 사유: {fails[0][:50]}...")
        return 1

    print("[통과] 파일 존재 확인")
    log_to_rooms(f"게이트 통과. {tgt.name}. {chars}자. **형 확인 후 발행 대기.**")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
