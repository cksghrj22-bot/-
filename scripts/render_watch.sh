#!/usr/bin/env bash
# 앳나운 온디맨드 렌더 감시 — 본진(Mac Studio) 상시 가동.
# 트렁크에 `status: 대기` 렌더잡이 뜨면 1분 안에 코덱스로 렌더 → 결과 커밋·push.
# 낮/새벽 구분 없이 24/7. 형이 자거나 손 떼도 렌더가 흐른다.
#
# 설계:
#   - 렌더 = 코덱스(render_trigger.py --dispatch). Claude 토큰 안 씀.
#   - 커밋·push = 이 스크립트(샌드박스 밖). claim 락 없음.
#   - 렌더 끝난 잡은 status: 대기 → 완료-자동렌더 로 바꿔 재렌더 루프 방지.
#   - 재렌더 필요분(verify FAIL 등)은 Cowork가 새 '대기' 잡으로 재큐 → 다음 사이클에 다시 잡힘.
#
# 설치(본진에서 1회): 이 파일 하단 주석 or scripts/com.atnown.renderwatch.plist 참조.
set -uo pipefail

REPO="${CODEX_CWD:-$HOME/atnown-repo}"
BRANCH="${ATNOWN_BRANCH:-main}"
INTERVAL="${ATNOWN_WATCH_INTERVAL:-60}"
LOG="${ATNOWN_WATCH_LOG:-$HOME/Library/Logs/atnown-renderwatch.log}"
mkdir -p "$(dirname "$LOG")" 2>/dev/null || true

log() { echo "$(date -u +%FT%TZ) $*" >>"$LOG"; }

cd "$REPO" 2>/dev/null || { log "REPO 없음: $REPO"; exit 1; }
log "renderwatch 시작 (repo=$REPO branch=$BRANCH interval=${INTERVAL}s)"

while true; do
  # 가드(2026-08-05): 이전 사이클이 남긴 stuck rebase/merge를 무조건 정리 → churn/블로킹 방지.
  git rebase --abort 2>/dev/null && log "이전 stuck rebase 정리함"
  git merge  --abort 2>/dev/null && log "이전 stuck merge 정리함"
  rm -fr .git/rebase-merge .git/rebase-apply 2>/dev/null || true

  # pull 실패(바이너리 충돌 등) 시 반드시 abort → 리포를 stuck 상태로 남기지 않는다.
  git pull --rebase origin "$BRANCH" -q 2>>"$LOG" || { git rebase --abort 2>/dev/null; log "pull 실패→abort(로컬 트렁크로 진행)"; }

  if python3 scripts/render_trigger.py 2>>"$LOG" | grep -q "대기 렌더잡"; then
    log "대기 렌더잡 발견 → 코덱스 dispatch"
    python3 scripts/render_trigger.py --dispatch >>"$LOG" 2>&1

    # 렌더 끝난 잡: status 대기 → 완료 (재렌더 무한루프 방지)
    # (재렌더 필요분은 Cowork가 새 '대기' 잡으로 재큐하므로 여기선 전부 완료 처리)
    for j in content/shorts/*/_RENDER_JOB.md; do
      [ -f "$j" ] && sed -i '' 's/status: 대기/status: 완료-자동렌더/g' "$j" 2>>"$LOG"
    done

    if [ -n "$(git status --porcelain)" ]; then
      git add -A 2>>"$LOG"
      git commit -q -m "자동 렌더(본진 watcher): 대기잡 렌더+상태완료" 2>>"$LOG"
      # ★ 핵심 가드: sync pull이 바이너리(컨택트PNG) 충돌로 멈추면 반드시 abort — stuck rebase를 남기지 않는다.
      #   (충돌 자동해소 전략은 미적용 = Cowork 잡편집 보호. 이 사이클은 push 보류, 다음 사이클 재시도.
      #    컨택트시트는 _render_drop 연결폴더로도 Cowork에 전달되므로 미리보기는 끊기지 않음.)
      if git pull --rebase origin "$BRANCH" -q 2>>"$LOG"; then
        if git push origin "$BRANCH" -q 2>>"$LOG"; then
          log "렌더 결과 push 완료(트렁크 동기화)"
        else
          log "push 거부(non-ff) — 다음 사이클 재시도"
        fi
      else
        git rebase --abort 2>/dev/null
        log "sync 충돌→abort. push 보류(다음 사이클 재시도). 컨택트시트는 연결폴더로 전달됨."
      fi
    else
      log "dispatch 후 변경 없음(렌더 산출 못 찾음?) — 로그 확인"
    fi
  fi

  sleep "$INTERVAL"
done
