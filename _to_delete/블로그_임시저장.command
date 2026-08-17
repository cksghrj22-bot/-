#!/bin/bash
cd "$(dirname "$0")"
echo "════════════════════════════════════════"
echo " 앳나운 블로그 — 네이버 임시저장"
echo "════════════════════════════════════════"
echo "· 크롬이 뜹니다. 로그인 화면이 나오면 로그인만 해주세요."
echo "  (로그인되면 나머지는 자동으로 진행됩니다)"
echo "· 임시저장까지만 합니다. 발행 버튼 안 누릅니다. 삭제도 안 합니다."
echo ""

JOBS=(); i=1
for d in _publish_jobs/blog_parsed/*/; do
  n=$(basename "$d"); [ "${n:0:1}" = "_" ] && continue
  [ -f "$d/blocks.json" ] || continue
  echo "  $i) $(cat "$d/title.txt" 2>/dev/null)"
  JOBS+=("$n"); i=$((i+1))
done
[ ${#JOBS[@]} -eq 0 ] && { echo "올릴 글이 없습니다."; read -p "엔터 " _; exit 1; }

echo ""
read -p "번호 선택 (엔터=1번): " SEL
[ -z "$SEL" ] && SEL=1
JOBNAME="${JOBS[$((SEL-1))]}"
[ -z "$JOBNAME" ] && { echo "잘못된 번호"; read -p "엔터 " _; exit 1; }
echo ""
echo "▶ $(cat "_publish_jobs/blog_parsed/$JOBNAME/title.txt")"
echo ""

if [ ! -d node_modules/playwright ]; then
  echo "· 최초 1회 설치 중(플레이라이트)… 1~2분 걸려요"
  npm i playwright >/tmp/naver_npm.log 2>&1
  npx playwright install chromium >>/tmp/naver_npm.log 2>&1
fi
PID=$(cat _naver_profile/.run.lock 2>/dev/null); [ -n "$PID" ] && kill "$PID" 2>/dev/null
rm -f _naver_profile/.run.lock; sleep 1

JOB="$JOBNAME" LOGIN_WAIT=600 node scripts/naver_blog_save.mjs

echo ""
echo "──────────── 결과 ────────────"
cat _cowork_sync/briefings/블로그_임시저장_결과.txt 2>/dev/null || echo "(결과 파일 없음 = 실행 실패)"
echo ""
read -p "엔터 누르면 이 창 닫힘 " _
