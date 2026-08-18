#!/bin/bash
# 통합 실행 레이어 — 모든 스크립트가 이걸 통해 실행
# 환경 표준화: PATH, 의존성, 작업 디렉토리

export PATH="/opt/homebrew/bin:/Users/chanho/.local/bin:/usr/local/bin:/usr/bin:/bin"
export PYTHONPATH="/Users/chanho/atnown-content-pipeline"
export ROOT="/Users/chanho/atnown-content-pipeline"

cd "$ROOT" || exit 1

# 실행
exec "$@"
