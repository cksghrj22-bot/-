#!/bin/bash
cd "$(dirname "$0")"
echo "════════════════════════════════════════"
echo " 앳나운 블로그 — 네이버 임시저장"
echo "════════════════════════════════════════"
echo "· 글: 한남동미용실 커트 | 두상이 작아야 세련돼 보입니다"
echo "· 임시저장까지만 합니다. 발행 버튼 안 누릅니다."
echo "· 삭제도 안 합니다."
echo ""
if [ ! -d node_modules/playwright ]; then
  echo "· 최초 1회 설치 중(플레이라이트)… 잠깐 걸려요"
  npm i playwright >/tmp/naver_npm.log 2>&1
  npx playwright install chromium >>/tmp/naver_npm.log 2>&1
fi
# 이전 실행이 남아 있으면 정리
PID=$(cat _naver_profile/.run.lock 2>/dev/null)
[ -n "$PID" ] && kill "$PID" 2>/dev/null
rm -f _naver_profile/.run.lock
sleep 1

JOB=20260815_두상_세련미 node scripts/naver_blog_save.mjs

echo ""
echo "──────────── 결과 ────────────"
cat _cowork_sync/briefings/블로그_임시저장_결과.txt 2>/dev/null || echo "(결과 파일 없음 = 실행 실패)"
echo ""
read -p "엔터 누르면 이 창 닫힘 " _
