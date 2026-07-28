#!/usr/bin/env bash
# 세션 시작 환경 부트스트랩 — 방·세션 간 재현성 보장(2026-07-28 형 지적: 환경 불일치 사고).
# 규칙이 문서가 아니라 '실행'되게: 폰트·의존성을 코드로 설치한다.
set -e
REPO="/home/user/-"
mkdir -p /root/.fonts
for f in "$REPO"/assets/fonts/*.ttf; do [ -f "$f" ] && cp -n "$f" /root/.fonts/ || true; done
if ! fc-match "NanumSquareRound ExtraBold" | grep -q NanumSquareRound; then
  apt-get install -y fonts-nanum-extra >/dev/null 2>&1 || true
fi
fc-cache -f >/dev/null 2>&1
echo "[setup_env] fonts ready: $(fc-match 'NanumSquareRound ExtraBold')"
