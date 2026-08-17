#!/bin/bash
cd "$(dirname "$0")"
echo "════════════════════════════════════════"
echo " 차노 에세이 2편 — 순차 임시저장"
echo "════════════════════════════════════════"
echo "  1) 차노 에세이 2 | 색은 잃어야 생깁니다"
echo "  2) 차노 에세이 1 | 예쁘다는 건 뭘까"
echo ""
echo "· 글부터 저장하고 서식을 얹습니다 (편당 3번 저장)"
echo "· 포인트색(핑크)은 진짜 강조 2곳에만 들어갑니다"
echo "· 발행·삭제 안 합니다"
echo ""
# 멈춘 것 정리
pkill -f naver_blog_save 2>/dev/null
pkill -f blog_save_all 2>/dev/null
rm -f _naver_profile/.run.lock
sleep 2

if [ ! -d node_modules/playwright ]; then
  echo "· 최초 1회 설치 중…"
  npm i playwright >/tmp/naver_npm.log 2>&1
  npx playwright install chromium >>/tmp/naver_npm.log 2>&1
fi

OUT=_cowork_sync/briefings/블로그_일괄_결과.txt
: > "$OUT"
for J in 20260815_소년등과와_색 20260815_예쁨1편_예쁘다는건뭘까; do
  T=$(cat "_publish_jobs/blog_parsed/$J/title.txt")
  echo ""
  echo "▶ $T"
  echo "▶ $T" >> "$OUT"
  pkill -f naver_blog_save 2>/dev/null; rm -f _naver_profile/.run.lock; sleep 2
  JOB="$J" LOGIN_WAIT=600 FORMAT_BUDGET=180 node scripts/naver_blog_save.mjs
  cat _cowork_sync/briefings/블로그_임시저장_결과.txt >> "$OUT" 2>/dev/null
  echo "────────────" >> "$OUT"
  sleep 3
done

echo ""
echo "──────────── 전체 결과 ────────────"
cat "$OUT"
echo ""
read -p "엔터 누르면 닫힘 " _
