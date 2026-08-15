#!/bin/bash
# 대기 중인 블로그 원고를 순차로 임시저장한다. 발행·삭제 없음.
cd "$(dirname "$0")/.."
OUT=_cowork_sync/briefings/블로그_일괄_결과.txt
: > "$OUT"
for J in 20260815_두상_세련미 20260815_소년등과와_색 20260815_예쁨1편_예쁘다는건뭘까; do
  [ -f "_publish_jobs/blog_parsed/$J/blocks.json" ] || continue
  T=$(cat "_publish_jobs/blog_parsed/$J/title.txt" 2>/dev/null)
  echo "▶ $T" | tee -a "$OUT"
  PID=$(cat _naver_profile/.run.lock 2>/dev/null); [ -n "$PID" ] && kill "$PID" 2>/dev/null
  rm -f _naver_profile/.run.lock; sleep 2
  JOB="$J" LOGIN_WAIT=600 node scripts/naver_blog_save.mjs >> /tmp/blog_save_$J.log 2>&1
  cat _cowork_sync/briefings/블로그_임시저장_결과.txt >> "$OUT" 2>/dev/null
  echo "────────────" >> "$OUT"
  sleep 3
done
echo "완료" >> "$OUT"
cat "$OUT"
