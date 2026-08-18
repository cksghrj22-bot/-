#!/bin/bash
# 블로그 자동 임시저장 — 대기 중인 잡을 전부 순차 처리한다.
# 정본: _strategy/블로그자동화방_전용규약.md §자동화 흐름
# ⛔ 발행·삭제 없음. 임시저장까지만. (naver_blog_save.mjs 안에서 코드로 꺼져 있음)
cd "$(dirname "$0")/.."
ROOT="$PWD"

PARSED="_publish_jobs/blog_parsed"
DONE="_publish_jobs/blog_done"
STATE="_publish_jobs/blog_state.json"
RESULT="_cowork_sync/briefings/블로그_임시저장_결과.txt"
OUT="_cowork_sync/briefings/블로그_일괄_결과.txt"

mkdir -p "$DONE" "_cowork_sync/briefings" "_naver_profile"
[ -f "$STATE" ] || echo '{}' > "$STATE"
: > "$OUT"

# 최초 1회 설치
if [ ! -d node_modules/playwright ]; then
  echo "· 최초 1회 설치 중…"
  npm i playwright >/tmp/naver_npm.log 2>&1
  npx playwright install chrome >>/tmp/naver_npm.log 2>&1
fi

# 대기 잡 = blocks.json 있고, 상태대장에 '성공'으로 안 박힌 것
PENDING=$(python3 - <<'PY'
import json, os
from pathlib import Path
state = json.loads(Path("_publish_jobs/blog_state.json").read_text(encoding="utf-8") or "{}")
jobs = []
p = Path("_publish_jobs/blog_parsed")
if p.exists():
    for d in sorted(p.iterdir()):
        if d.is_dir() and not d.name.startswith("_") and (d / "blocks.json").exists():
            if state.get(d.name, {}).get("상태") != "성공":
                jobs.append(d.name)
print("\n".join(jobs))
PY
)

if [ -z "$PENDING" ]; then
  echo "대기 중인 원고 없음. 전부 임시저장돼 있습니다." | tee -a "$OUT"
  exit 0
fi

COUNT=$(echo "$PENDING" | wc -l | tr -d ' ')
echo "▶ 대기 $COUNT건 — 순차 임시저장 시작" | tee -a "$OUT"
echo "" >> "$OUT"

for J in $PENDING; do
  T=$(cat "$PARSED/$J/title.txt" 2>/dev/null)
  echo ""
  echo "▶ $T"
  echo "▶ $T" | tee -a "$OUT" >/dev/null

  # 브라우저 중복 실행 방지 — 이전 프로세스/락 정리
  pkill -f naver_blog_save 2>/dev/null
  rm -f _naver_profile/.run.lock
  sleep 2

  JOB="$J" LOGIN_WAIT="${LOGIN_WAIT:-600}" FORMAT_BUDGET="${FORMAT_BUDGET:-180}" \
    node scripts/naver_blog_save.mjs >>"/tmp/blog_save_$J.log" 2>&1

  cat "$RESULT" >> "$OUT" 2>/dev/null
  echo "────────────" >> "$OUT"

  # 상태 대장 기록 (중복 금지 규약 — 성공한 주제는 다시 안 만든다)
  JOB="$J" python3 - <<'PY'
import json, os, re
from pathlib import Path
job = os.environ["JOB"]
sp = Path("_publish_jobs/blog_state.json")
state = json.loads(sp.read_text(encoding="utf-8") or "{}")
txt = Path("_cowork_sync/briefings/블로그_임시저장_결과.txt").read_text(encoding="utf-8") if Path("_cowork_sync/briefings/블로그_임시저장_결과.txt").exists() else ""
def pick(k):
    m = re.search(rf"^{k}:\s*(.*)$", txt, re.M)
    return (m.group(1).strip() if m else "")
state[job] = {"상태": pick("상태"), "임시글URL": pick("임시글URL"),
              "막힌지점": pick("막힌지점"), "시각": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")}
sp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"  상태대장 기록: {job} = {state[job]['상태'] or '미상'}")
PY

  # 성공한 것만 done 으로 옮긴다 (막힌 건 남겨서 다음 실행에 재시도)
  if grep -q "^상태: 성공" "$RESULT" 2>/dev/null; then
    mv "$PARSED/$J" "$DONE/${J}_$(date +%H%M)" 2>/dev/null
  fi
  sleep 3
done

echo ""
echo "──────────── 전체 결과 ────────────"
cat "$OUT"
