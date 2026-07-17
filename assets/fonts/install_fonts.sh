#!/usr/bin/env bash
# 쇼츠 렌더 폰트 설치 — 새 세션마다 1회. 교보손글씨2019(정본) + 브랜디드 폰트.
set -e
mkdir -p ~/.fonts
DIR="$(cd "$(dirname "$0")" && pwd)"
# 1) 커밋된 교보손글씨 사용, 없으면 noonnu CDN에서 재확보(WOFF→TTF)
if [ -f "$DIR/KyoboHandwriting2019.ttf" ]; then
  cp "$DIR/KyoboHandwriting2019.ttf" ~/.fonts/
else
  curl -sL "https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_20-04@1.0/KyoboHand.woff" -o /tmp/kyobo.woff
  python3 - <<'PY'
from fontTools.ttLib import TTFont
f=TTFont('/tmp/kyobo.woff'); f.flavor=None; f.save('/root/.fonts/KyoboHandwriting2019.ttf')
PY
fi
fc-cache -f >/dev/null 2>&1
fc-match "Kyobo Handwriting 2019" | grep -qi kyobo && echo "✅ 교보손글씨 설치됨" || echo "❌ 교보손글씨 설치 실패"
