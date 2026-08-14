#!/usr/bin/env python3
"""Git 위험 명령 차단 — reset --hard, checkout ., restore . 등 감지 시 차단

git alias로 등록하거나, 쉘 함수로 래핑해서 사용.

사용법:
    python3 scripts/git_safety.py <git 명령어>

예:
    python3 scripts/git_safety.py reset --hard HEAD
    → ❌ 차단됨

설치 (zshrc/bashrc에 추가):
    git() {
        if python3 ~/atnown-content-pipeline/scripts/git_safety.py "$@"; then
            command git "$@"
        fi
    }
"""
from __future__ import annotations
import sys

# 차단 패턴 (정확한 인자 조합)
BLOCKED_PATTERNS = [
    ["reset", "--hard"],
    ["reset", "origin/main"],
    ["reset", "origin/master"],
    ["checkout", "."],
    ["checkout", "--", "."],
    ["restore", "."],
    ["restore", "--staged", "."],
    ["clean", "-f"],
    ["clean", "-fd"],
    ["clean", "-fx"],
]

# 경고 패턴 (확인 후 진행)
WARN_PATTERNS = [
    ["push", "--force"],
    ["push", "-f"],
    ["branch", "-D"],
    ["rebase", "-i"],
]


def check_command(args: list[str]) -> tuple[str, str | None]:
    """
    명령어 검사.
    Returns: ("allow" | "block" | "warn", 이유 또는 None)
    """
    # 차단 패턴 체크
    for pattern in BLOCKED_PATTERNS:
        if all(p in args for p in pattern):
            return "block", f"금지된 명령: {' '.join(pattern)}"

    # 경고 패턴 체크
    for pattern in WARN_PATTERNS:
        if all(p in args for p in pattern):
            return "warn", f"위험한 명령: {' '.join(pattern)}"

    return "allow", None


def main():
    args = sys.argv[1:]

    if not args:
        print("사용법: git_safety.py <git 명령어>")
        return 0

    result, reason = check_command(args)

    if result == "block":
        print(f"❌ 차단: {reason}")
        print("   이 명령은 커밋 안 된 작업을 영구 삭제합니다.")
        print("   CLAUDE.md 금지 규칙 참조.")
        return 1

    if result == "warn":
        print(f"⚠️ 경고: {reason}")
        print("   정말 실행하시겠습니까? (이 스크립트는 경고만 합니다)")
        # 경고만 하고 통과
        return 0

    # 허용
    return 0


if __name__ == "__main__":
    sys.exit(main())
