#!/usr/bin/env bash
# 코드방 ↔ 본진 코드 동기화 (git을 형님이 안 만지게 감싼 것).
# 사용: bash 본진/동기화.sh [pull|push|both]   (기본 pull)
#   pull  = 코드방이 올린 최신 코드를 본진으로 내려받기
#   push  = 본진에서 바뀐 코드를 코드방으로 올리기
#   both  = 내려받고 올리기
set -euo pipefail
DIR="${CHANO_DIR:-$HOME/chano-code}"
BRANCH="${CHANO_BRANCH:-main}"
MODE="${1:-pull}"
cd "$DIR"

git fetch origin "$BRANCH"
if [ "$MODE" = pull ] || [ "$MODE" = both ]; then
  echo "· 내려받기 (pull)"
  git merge --ff-only "origin/$BRANCH" 2>/dev/null || git pull origin "$BRANCH"
fi
if [ "$MODE" = push ] || [ "$MODE" = both ]; then
  echo "· 올리기 (push)"
  git add -A
  if git diff --cached --quiet; then echo "  (바뀐 것 없음)"; else git commit -m "본진 변경 동기화"; fi
  git push origin "$BRANCH"
fi
echo "✅ 동기화 완료 ($MODE)"
