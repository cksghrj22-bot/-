#!/usr/bin/env bash
# 본진(맥스튜디오)에서 이 리포지토리를 코드방과 "같은 코드"로 돌리는 세팅.
# 파이썬 표준기능만 쓰므로 pip 설치 불필요 — ffmpeg만 있으면 된다.
# 처음이든 매번이든 이거 한 번만 돌리면: 최신 코드 받기 + 도구 확인 + 지식인덱스 + 진단.
set -euo pipefail

REPO_URL="${CHANO_REPO_URL:-https://github.com/cksghrj22-bot/-.git}"
DIR="${CHANO_DIR:-$HOME/chano-code}"
BRANCH="${CHANO_BRANCH:-main}"

echo "🌳 본진 세팅 시작 → $DIR (브랜치 $BRANCH)"

# 1) 코드 받기 (있으면 최신화)
if [ -d "$DIR/.git" ]; then
  echo "· 기존 코드 최신화 (git pull)"
  git -C "$DIR" fetch origin "$BRANCH"
  git -C "$DIR" checkout "$BRANCH" 2>/dev/null || true
  git -C "$DIR" merge --ff-only "origin/$BRANCH" 2>/dev/null || git -C "$DIR" pull origin "$BRANCH"
else
  echo "· 처음 받기 (git clone)"
  git clone --branch "$BRANCH" "$REPO_URL" "$DIR" 2>/dev/null || git clone "$REPO_URL" "$DIR"
fi
cd "$DIR"

# 2) 필수 도구 확인
command -v python3 >/dev/null || { echo "❌ python3 없음 — brew install python 또는 python.org"; exit 1; }
if ! command -v ffmpeg >/dev/null; then
  echo "· ffmpeg 없음 → 설치 시도"
  if command -v brew >/dev/null; then brew install ffmpeg; else echo "⚠️ brew 없음 — ffmpeg 수동 설치 필요 (https://ffmpeg.org)"; fi
fi
echo "· python3: $(python3 --version)"
command -v ffmpeg >/dev/null && echo "· ffmpeg: $(ffmpeg -version 2>/dev/null | head -1)"

# 3) 비밀키 자리 (gitignore라 코드엔 안 옴 — 있으면 그대로 쓰고 없어도 지식인덱스는 돎)
mkdir -p secrets
if [ ! -f secrets/elevenlabs.json ]; then
  echo "  (secrets/ 비어있음 — 지식인덱스·검색은 키 없이 OK. 렌더/업로드까지 하려면"
  echo "   노션 「📱 코드방 상태판」의 키를 secrets/에 복원)"
fi

# 4) 지식 인덱스 구축/갱신 (본진 로컬 data/에 쌓임)
echo "· 지식 인덱스 구축"
for d in knowledge docs content briefings prompts; do
  python3 -m pipeline add "$d" >/dev/null 2>&1 || true
done

# 5) 진단
echo "─────────────────────────────"
python3 -m pipeline check || true
echo "─────────────────────────────"
echo "✅ 본진 세팅 완료 — 코드방과 같은 코드가 여기서 돕니다: $DIR"
echo "   최신화(다음부터): bash 본진/세팅.sh"
echo "   양방향 동기화:   bash 본진/동기화.sh both"
