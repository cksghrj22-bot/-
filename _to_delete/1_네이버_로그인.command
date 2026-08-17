#!/bin/bash
cd "$(dirname "$0")"
echo "════════════════════════════════════════"
echo " 앳나운 — 네이버 로그인 1회"
echo "════════════════════════════════════════"
echo "· 글 안 씁니다. 발행 버튼 없습니다."
echo "· 크롬 뜨면 로그인만 하세요. 되면 알아서 닫힙니다."
echo ""
if [ ! -d node_modules/playwright ]; then
  echo "· 최초 1회 설치 중… 잠깐 걸려요"
  npm i playwright >/tmp/naver_npm.log 2>&1
  npx playwright install chromium >>/tmp/naver_npm.log 2>&1
fi
PID=$(cat _naver_profile/.run.lock 2>/dev/null); [ -n "$PID" ] && kill "$PID" 2>/dev/null
rm -f _naver_profile/.run.lock; sleep 1
node scripts/naver_login.mjs
echo ""
read -p "엔터 누르면 이 창 닫힘 " _
