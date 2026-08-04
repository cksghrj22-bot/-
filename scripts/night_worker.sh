#!/usr/bin/env bash
# com.atnown.night — 본진(맥스튜디오) 밤샘 무인 렌더 워커
# 설계 정본: pipeline/밤샘_무인_아키텍처.md
# 규약: 발행·예약은 절대 자동 금지(감독 게이트). 이 워커는 '시안'까지만 만든다.
# 동작: git pull → content/shorts/*/_RENDER_JOB.md 대기건 → shorts.proof 렌더
#        → verify_render PASS 시안만 남김 → 결과 append → git push. FAIL이면 사유 기록·중단(억지 금지).
# ⚠️ macOS 본진에서만 의미 있음(로컬 footage·ffmpeg·git 자격 필요). 클라우드 컨테이너 아님.
set -uo pipefail

REPO_DIR="${ATNOWN_REPO:-$HOME/atnown-repo}"
NIGHT_START="${NIGHT_START:-3}"        # 새벽 3시부터
NIGHT_END="${NIGHT_END:-7}"            # 오전 7시까지만(그 외 시간엔 no-op → 낮 자동렌더 방지)
LOG="${ATNOWN_NIGHT_LOG:-$HOME/Library/Logs/atnown-night.log}"
SMOKE="${SMOKE:-0}"                    # 1이면 실제 렌더 생략(배관/명령만 점검)

mkdir -p "$(dirname "$LOG")" 2>/dev/null || true
log(){ echo "[$(date '+%F %T')] $*" | tee -a "$LOG" >&2; }

cd "$REPO_DIR" 2>/dev/null || { log "FATAL: repo 없음 → $REPO_DIR (ATNOWN_REPO로 지정)"; exit 1; }

# 밤 시간대 게이트 (스모크는 무시)
H=$(date +%H); H=${H#0}; [ -z "$H" ] && H=0
if [ "$SMOKE" != "1" ] && { [ "$H" -lt "$NIGHT_START" ] || [ "$H" -ge "$NIGHT_END" ]; }; then
  log "낮 시간(${H}시) — 밤샘 워커 no-op"; exit 0
fi

log "=== 밤샘 워커 시작 (repo=$REPO_DIR smoke=$SMOKE hour=$H) ==="
git pull --rebase origin main >>"$LOG" 2>&1 || log "WARN: git pull 실패(계속 진행)"

shopt -s nullglob
found=0
for job in content/shorts/*/_RENDER_JOB.md; do
  dir=$(dirname "$job")
  [ -f "$dir/_RENDER_DONE.md" ] && continue      # 이미 완료 → 재렌더 안 함
  [ -f "$dir/_RENDER_FAIL.md" ] && continue      # 실패건 → 재시도 금지(억지 방지, 사람이 마커 지워야 재시도)
  found=1
  out="$dir/_render_out"
  opts=""
  [ -f "$dir/_RENDER_OPTS.txt" ] && opts=$(tr '\n' ' ' < "$dir/_RENDER_OPTS.txt")  # 편별 override(예: --preset style_preset_v9 --grade color)
  log "렌더 착수: $dir  opts=[$opts]"

  if [ "$SMOKE" = "1" ]; then
    log "SMOKE: 실제 렌더 생략 — 형성된 명령 검증 → python3 -m shorts.proof \"$dir\" --out \"$out\" $opts"
    continue
  fi

  if python3 -m shorts.proof "$dir" --out "$out" $opts >>"$LOG" 2>&1; then
    {
      echo; echo "## ✅ 밤샘 렌더 완료 ($(date '+%F %T')) — verify_render PASS 시안"
      echo "- 출력: $out"; ls "$out" 2>/dev/null | sed 's/^/  - /'
    } >> "$job"
    : > "$dir/_RENDER_DONE.md"
    log "PASS: $dir"
  else
    {
      echo; echo "## ❌ 밤샘 렌더 실패 ($(date '+%F %T')) — verify FAIL 또는 오류. 억지 금지·중단."
      echo "- 로그 tail:"; tail -n 15 "$LOG" | sed 's/^/  /'
    } >> "$job"
    echo "실패 — 사유는 _RENDER_JOB.md 참조. 재시도는 사람이 이 파일을 지운 후." > "$dir/_RENDER_FAIL.md"
    log "FAIL: $dir (중단·발행 없음)"
  fi
done

if [ "$found" = "1" ] && [ "$SMOKE" != "1" ]; then
  git add -A >>"$LOG" 2>&1
  if git commit -q -m "밤샘 워커: 시안 렌더 결과 append (자동·발행 없음)" >>"$LOG" 2>&1; then
    git push origin HEAD:main >>"$LOG" 2>&1 && log "push 완료" || log "WARN: push 실패"
  else
    log "커밋할 변경 없음"
  fi
else
  log "대기 렌더잡 없음(또는 스모크) — push 생략"
fi
log "=== 밤샘 워커 종료 ==="
