#!/usr/bin/env python3
"""블로그 자동 임시저장 감시 데몬

_publish_jobs/blog_parsed/ 에 잡 폴더가 들어오면 자동으로 naver_blog_save.mjs 실행.

⛔ 2026-08-18 수리 — 「가짜 done」 방지
구버전은 returncode==0 이면 성공으로 보고 blog_done 으로 옮겼다.
그런데 naver_blog_save.mjs 는 「막힘」·「중단」에도 exit 0 으로 끝난다(실측).
→ 저장이 안 됐는데도 done 으로 옮겨졌고, 같은 잡을 35초마다 무한 재시도했다
   (실측: 두상_세련미 09:28~09:33 사이 8회 반복 = 「브라우저 반복 실행 금지」 규약 위반).

수리 3가지:
  ① 성공 판정은 결과파일의 「상태: 성공」 + 임시글URL 존재로만 한다. exit code 를 믿지 않는다.
  ② 실패는 blog_state.json 에 실패횟수로 남기고, MAX_TRY 넘으면 더 안 건드린다(무한루프 차단).
  ③ 잡 간격·라운드 간격을 늘려 브라우저를 연달아 띄우지 않는다.

사용법:
    python3 scripts/blog_watcher.py           # 상주
    python3 scripts/blog_watcher.py --once    # 1회만
"""
import os
import re
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
PARSED = ROOT / "_publish_jobs/blog_parsed"
DONE = ROOT / "_publish_jobs/blog_done"
STATE = ROOT / "_publish_jobs/blog_state.json"
RESULT = ROOT / "_cowork_sync/briefings/블로그_임시저장_결과.txt"
LOG = ROOT / "data/blog_watcher.log"

MAX_TRY = 2          # 같은 잡 재시도 상한 — 넘으면 형이 볼 때까지 멈춘다
JOB_GAP = 20         # 잡 사이 간격(초)
ROUND_GAP = 300      # 라운드 간격(초) — 구버전 30초는 너무 잦았다


DAEMON_LOCK = ROOT / "_locks/blog_watcher.pid"


def acquire_daemon_lock():
    """데몬 2개가 동시에 크롬을 잡으면 'Target page, context or browser has been closed' 가 난다.
    2026-08-18 실측: 구버전·수리본이 겹쳐 돌면서 예쁨1편·단골이 즉시 실패했다. 한 대만 돌게 잠근다."""
    DAEMON_LOCK.parent.mkdir(parents=True, exist_ok=True)
    if DAEMON_LOCK.exists():
        try:
            old = int(DAEMON_LOCK.read_text().strip())
            os.kill(old, 0)          # 살아 있으면 예외 안 남
            log(f"⛔ 이미 데몬이 돌고 있습니다 (pid {old}). 이 프로세스는 종료합니다.")
            return False
        except (ValueError, ProcessLookupError, PermissionError):
            log("· 죽은 잠금 파일 발견 — 이어받습니다")
    DAEMON_LOCK.write_text(str(os.getpid()), encoding="utf-8")
    return True


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def load_state():
    if not STATE.exists():
        return {}
    try:
        return json.loads(STATE.read_text(encoding="utf-8") or "{}")
    except Exception:
        return {}


def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def read_result():
    """naver_blog_save.mjs 가 쓴 결과파일을 판독한다. exit code 는 믿지 않는다."""
    if not RESULT.exists():
        return {"상태": "", "임시글URL": "", "막힌지점": "결과파일 없음"}
    txt = RESULT.read_text(encoding="utf-8")
    def pick(k):
        m = re.search(rf"^{k}:[ \t]*(.*)$", txt, re.M)
        return m.group(1).strip() if m else ""
    return {"상태": pick("상태"), "임시글URL": pick("임시글URL"), "막힌지점": pick("막힌지점")}


def node_bin():
    """디스패처/LaunchAgent 는 PATH 가 빈약해서 bare node 가 안 잡힌다(2026-08-17 실측)."""
    cands = ["/opt/homebrew/bin/node", "/usr/local/bin/node", "/usr/bin/node"]
    for c in cands:
        if os.path.exists(c) and os.access(c, os.X_OK):
            return c
    from shutil import which
    return which("node") or "node"


def get_pending_jobs(state):
    if not PARSED.exists():
        return []
    jobs = []
    for d in sorted(PARSED.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        if not (d / "blocks.json").exists():
            continue
        rec = state.get(d.name, {})
        if rec.get("상태") == "성공":
            continue
        if rec.get("실패횟수", 0) >= MAX_TRY:
            continue  # 무한 재시도 차단 — 형이 보고 풀어줄 때까지 멈춘다
        jobs.append(d.name)
    return jobs


def run_blog_save(job_name):
    log(f"📝 블로그 저장 시작: {job_name}")
    state = load_state()
    rec = state.get(job_name, {})

    env = dict(os.environ)
    env["JOB"] = job_name
    env.setdefault("LOGIN_WAIT", "600")
    env.setdefault("FORMAT_BUDGET", "180")
    env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:" + env.get("PATH", "")

    try:
        subprocess.run(
            [node_bin(), str(ROOT / "scripts/naver_blog_save.mjs")],
            cwd=str(ROOT), capture_output=True, text=True, timeout=900, env=env,
        )
    except subprocess.TimeoutExpired:
        log(f"⏰ 타임아웃: {job_name}")

    # ⛔ 성공 판정은 결과파일로만 한다
    r = read_result()
    ok = (r["상태"] == "성공") and bool(r["임시글URL"])

    rec.update({
        "상태": r["상태"] or "미상",
        "임시글URL": r["임시글URL"],
        "막힌지점": r["막힌지점"],
        "시각": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    if ok:
        rec["실패횟수"] = 0
    else:
        rec["실패횟수"] = rec.get("실패횟수", 0) + 1
    state[job_name] = rec
    save_state(state)

    if ok:
        DONE.mkdir(parents=True, exist_ok=True)
        dst = DONE / f"{job_name}_{datetime.now().strftime('%H%M')}"
        (PARSED / job_name).rename(dst)
        log(f"✅ 성공: {job_name} → {r['임시글URL']}")
        return True

    log(f"❌ 실패({rec['실패횟수']}/{MAX_TRY}): {job_name} — {r['상태'] or '미상'} / {r['막힌지점']}")
    if rec["실패횟수"] >= MAX_TRY:
        log(f"⛔ {job_name} 재시도 중단. 원인 해결 전까지 안 건드립니다. (blog_state.json 확인)")
    return False


def watch():
    if not acquire_daemon_lock():
        return
    log(f"🚀 블로그 감시 데몬 시작 (성공판정=결과파일 / 재시도상한={MAX_TRY} / 라운드={ROUND_GAP}초)")
    while True:
        try:
            jobs = get_pending_jobs(load_state())
            if jobs:
                log(f"📋 대기 {len(jobs)}건: {', '.join(jobs)}")
            for job in jobs:
                try:
                    run_blog_save(job)
                except Exception as e:
                    log(f"❌ 에러: {job} - {e}")
                time.sleep(JOB_GAP)
        except Exception as e:
            log(f"❌ 감시 에러: {e}")
        time.sleep(ROUND_GAP)


if __name__ == "__main__":
    import sys
    if "--once" in sys.argv:
        jobs = get_pending_jobs(load_state())
        log(f"📋 {len(jobs)}개 잡 발견")
        for job in jobs:
            run_blog_save(job)
    else:
        watch()
