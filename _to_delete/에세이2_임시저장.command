#!/bin/bash
cd "$(dirname "$0")"
echo "════════════════════════════════════════"
echo " 차노 에세이 2 | 색은 잃어야 생깁니다"
echo "════════════════════════════════════════"
echo "· 글부터 저장하고 서식을 얹습니다 (3번 저장)"
echo "· 서식은 최대 3분. 넘으면 저장하고 끝냅니다"
echo "· 발행·삭제 안 합니다"
echo ""
PID=$(cat _naver_profile/.run.lock 2>/dev/null)
[ -n "$PID" ] && kill "$PID" 2>/dev/null
pkill -f naver_blog_save 2>/dev/null
rm -f _naver_profile/.run.lock; sleep 2
if [ ! -d node_modules/playwright ]; then
  echo "· 최초 1회 설치 중…"
  npm i playwright >/tmp/naver_npm.log 2>&1
  npx playwright install chromium >>/tmp/naver_npm.log 2>&1
fi
JOB=20260815_소년등과와_색 LOGIN_WAIT=600 FORMAT_BUDGET=180 node scripts/naver_blog_save.mjs
echo ""
echo "──────────── 결과 ────────────"
cat _cowork_sync/briefings/블로그_임시저장_결과.txt 2>/dev/null || echo "(결과 없음 = 실패)"
echo ""
read -p "엔터 누르면 닫힘 " _
