#!/usr/bin/env python3
"""
본진 원격 명령 실행기 — 전략기획및개인업무 방 소유

배경 (2026-08-17):
  코워크 클라우드 세션은 맥의 '폴더'는 읽고 쓰지만 macOS '프로세스'는 못 만진다.
  그래서 데몬이 죽을 때마다 "형이 맥에서 재시작해주세요" 가 나왔다.
  (08-16 cowork_multi_watch 미기동 · 08-17 디스패처 구코드 상주)
  이 실행기가 그 구멍을 메운다. 폴더에 파일을 쓰면 맥에서 실행된다.

보안 — 아무 셸 문자열이나 실행하지 않는다:
  · ACTIONS 에 등록된 동작만 실행. 미등록이면 즉시 거부
  · shell=True 안 쓴다 (셸 주입 차단)
  · 경로 인자는 파이프라인 루트 안으로 강제
  · rm / sudo / git reset --hard / git checkout . / 삭제성 스크립트 = 미등록
  · 모든 요청·결과를 logs/remote_cmd.log 에 남긴다

주문 형식:  _terminal_inbox/CMD_<이름>.json
  {"cmd": "restart_dispatcher", "args": [], "requested_by": "전략실"}

결과:  _out/cmd_results/<파일명>  +  _terminal_inbox/_cmd_done|_cmd_failed/
  ※ 실패를 done 으로 찍지 않는다 (공유규약 §10-6 · 08-17 가짜done 사고 교훈)

실행:  python3 scripts/remote_cmd_watch.py --daemon
       python3 scripts/remote_cmd_watch.py --once
       python3 scripts/remote_cmd_watch.py --list      (허용 명령 목록)
       python3 scripts/remote_cmd_watch.py --selftest  (실행 없이 자가검증)
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "_terminal_inbox"
CMD_DONE = INBOX / "_cmd_done"
CMD_FAILED = INBOX / "_cmd_failed"
RESULTS = ROOT / "_out" / "cmd_results"
LOGS = ROOT / "logs"
SCRIPTS = ROOT / "scripts"

for d in (INBOX, CMD_DONE, CMD_FAILED, RESULTS, LOGS):
    d.mkdir(parents=True, exist_ok=True)

# ── 금지 목록 ────────────────────────────────────────────────
DENIED_SCRIPTS = {
    "cleanup_old_files.py",   # 파일 삭제
    "terminal_watcher.py",    # 폐기(코덱스 전환으로 대체)
}
DENIED_ARGS = {
    "--dispatch",   # 공유규약: 수동 디스패치 금지 (watcher 가 유일한 디스패처)
    "--publish", "--upload", "--delete", "--purge", "--hard", "--force-delete",
}
DAEMONS = {
    "dispatcher": ("codex_dispatch.py", "scripts/codex_dispatch.py"),
    "multiwatch": ("cowork_multi_watch.py", "scripts/cowork_multi_watch.py"),
    "blogwatch":  ("blog_watcher.py", "scripts/blog_watcher.py"),
}


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        with open(LOGS / "remote_cmd.log", "a") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line, flush=True)


def run(argv, timeout=120):
    """shell=True 없이 실행. (rc, out) 반환."""
    try:
        r = subprocess.run(argv, capture_output=True, text=True,
                           timeout=timeout, cwd=str(ROOT))
        out = (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.stderr else "")
        return r.returncode, out.strip()
    except subprocess.TimeoutExpired:
        return 124, f"오류: {timeout}초 타임아웃"
    except FileNotFoundError as e:
        return 127, f"오류: 실행파일 없음 ({e})"
    except Exception as e:
        return 1, f"오류: {e}"


def safe_path(p, must_exist=True):
    """파이프라인 루트 밖 경로 차단."""
    q = (ROOT / str(p)).resolve() if not str(p).startswith("/") else Path(p).resolve()
    if ROOT not in q.parents and q != ROOT:
        raise ValueError(f"루트 밖 경로 거부: {p}")
    if must_exist and not q.exists():
        raise ValueError(f"경로 없음: {p}")
    return q


def spawn_daemon(script_rel, logname):
    """데몬을 분리 실행(부모가 죽어도 살아있게)."""
    out = open(LOGS / f"{logname}.out", "a")
    subprocess.Popen(
        ["/bin/zsh", "-lc", f"cd {ROOT} && exec python3 {script_rel} --daemon"],
        stdout=out, stderr=subprocess.STDOUT,
        start_new_session=True, cwd=str(ROOT),
    )


# ── 허용 동작 ────────────────────────────────────────────────
def act_status(args):
    _, ps = run(["pgrep", "-lf", "codex_dispatch|cowork_multi|blog_watcher|remote_cmd"])
    _, gs = run(["git", "status", "--short"])
    _, gl = run(["git", "log", "--oneline", "-3"])
    inbox = sorted(p.name for p in INBOX.glob("TASK_*.json"))
    failed = sorted(p.name for p in (INBOX / "_failed").glob("*.json")) if (INBOX / "_failed").exists() else []
    return 0, json.dumps({
        "데몬": ps.splitlines() or ["(없음)"],
        "미커밋": len(gs.splitlines()),
        "최근커밋": gl.splitlines(),
        "대기주문서": inbox or ["(없음)"],
        "실패주문서": failed or ["(없음)"],
    }, ensure_ascii=False, indent=2)


def act_restart(args):
    """args: ["dispatcher"] / ["multiwatch"] / ["all"]"""
    targets = args or ["all"]
    if "all" in targets:
        targets = ["dispatcher", "multiwatch"]
    report = []
    for t in targets:
        if t not in DAEMONS:
            raise ValueError(f"모르는 데몬: {t} (가능: {', '.join(DAEMONS)})")
        pat, rel = DAEMONS[t]
        if not (ROOT / rel).exists():
            report.append(f"{t}: ⛔ 스크립트 없음 ({rel})")
            continue
        run(["pkill", "-f", pat], timeout=20)
        time.sleep(1)
        spawn_daemon(rel, t)
        report.append(f"{t}: 재시작 요청")
    time.sleep(3)
    _, ps = run(["pgrep", "-lf", "codex_dispatch|cowork_multi"])
    return 0, "\n".join(report) + "\n--- pgrep ---\n" + (ps or "(잡히는 프로세스 없음 ⛔)")


def act_pgrep(args):
    pat = args[0] if args else "codex_dispatch|cowork_multi|remote_cmd"
    return run(["pgrep", "-lf", pat], timeout=20)


def act_tail(args):
    if not args:
        raise ValueError("tail_log 에는 파일 경로가 필요하다")
    p = safe_path(args[0])
    n = str(int(args[1])) if len(args) > 1 else "40"
    return run(["tail", "-n", n, str(p)], timeout=30)


def act_ls(args):
    p = safe_path(args[0]) if args else ROOT
    return run(["ls", "-lt", str(p)], timeout=30)


def act_python(args):
    if not args:
        raise ValueError("python_script 에는 스크립트명이 필요하다")
    name = Path(args[0]).name
    if not name.endswith(".py"):
        raise ValueError("py 스크립트만 허용")
    if name in DENIED_SCRIPTS:
        raise ValueError(f"금지 스크립트: {name}")
    target = (SCRIPTS / name)
    if not target.exists():
        raise ValueError(f"scripts/ 안에 없음: {name}")
    rest = [str(a) for a in args[1:]]
    bad = [a for a in rest if a in DENIED_ARGS]
    if bad:
        raise ValueError(f"금지 인자: {', '.join(bad)}")
    if "--daemon" in rest:
        raise ValueError("데몬 기동은 restart 동작으로만")
    return run(["python3", str(target)] + rest, timeout=600)


def act_git_commit(args):
    msg = args[0] if args else f"자동저장 {datetime.now():%Y-%m-%d %H:%M} (원격 명령)"
    lock = ROOT / ".git" / "index.lock"
    if lock.exists() and (time.time() - lock.stat().st_mtime) > 600:
        # 10분 넘게 방치된 락 = 죽은 락. 지우지 않고 치워둔다.
        stash = ROOT / "_to_delete" / "gitlock"
        stash.mkdir(parents=True, exist_ok=True)
        lock.rename(stash / f"index.lock.{int(time.time())}")
    rc, o1 = run(["git", "add", "-A"], timeout=180)
    if rc != 0:
        return rc, o1
    rc, o2 = run(["git", "commit", "-m", msg], timeout=180)
    _, o3 = run(["git", "log", "--oneline", "-1"])
    return (0 if rc in (0, 1) else rc), f"{o2}\n--- HEAD ---\n{o3}"


def act_git_push(args):
    return run(["git", "push", "origin", "HEAD"], timeout=300)


def act_move_order(args):
    """보류해 둔 주문서를 _terminal_inbox 로 투입."""
    if not args:
        raise ValueError("옮길 파일 경로가 필요하다")
    src = safe_path(args[0])
    if src.suffix != ".json" or not src.name.startswith("TASK_"):
        raise ValueError("TASK_*.json 만 투입 가능")
    dst = INBOX / src.name
    src.rename(dst)
    return 0, f"투입 완료: {dst.relative_to(ROOT)}"


ACTIONS = {
    "status":             (act_status,     "데몬·미커밋·주문서 현황 한 번에"),
    "restart":            (act_restart,    "데몬 재시작 (dispatcher|multiwatch|all)"),
    "restart_dispatcher": (lambda a: act_restart(["dispatcher"]),  "디스패처만 재시작"),
    "restart_multiwatch": (lambda a: act_restart(["multiwatch"]),  "멀티워치만 재시작"),
    "pgrep":              (act_pgrep,      "프로세스 조회"),
    "tail_log":           (act_tail,       "로그 꼬리 (경로, 줄수)"),
    "ls":                 (act_ls,         "폴더 목록 (루트 안쪽만)"),
    "python_script":      (act_python,     "scripts/ 안 파이썬 실행 (금지목록 제외)"),
    "git_commit":         (act_git_commit, "add -A + commit (죽은 락 자동 정리)"),
    "git_push":           (act_git_push,   "origin push"),
    "move_order":         (act_move_order, "보류 주문서를 _terminal_inbox 로 투입"),
}


def process(path):
    try:
        req = json.loads(path.read_text())
    except Exception as e:
        req = {"_parse_error": str(e)}

    name = req.get("cmd")
    args = req.get("args") or []
    if not isinstance(args, list):
        args = [args]

    log(f"수신: {path.name} · cmd={name} · args={args} · by={req.get('requested_by','?')}")

    if name not in ACTIONS:
        rc, out = 2, f"오류: 허용되지 않은 명령 '{name}'. 가능: {', '.join(sorted(ACTIONS))}"
    else:
        try:
            rc, out = ACTIONS[name][0](args)
        except Exception as e:
            rc, out = 2, f"오류: {e}"

    ok = (rc == 0)
    req.update({
        "status": "done" if ok else "failed",   # 실패를 done 으로 찍지 않는다
        "returncode": rc,
        "result": out[:8000],
        "completed_at": datetime.now().isoformat(),
    })
    blob = json.dumps(req, ensure_ascii=False, indent=2)
    (RESULTS / path.name).write_text(blob)
    # unlink 대신 rename — 삭제 권한이 없는 마운트에서도 동작하고, 원자적이다
    path.write_text(blob)
    path.rename((CMD_DONE if ok else CMD_FAILED) / path.name)
    log(("완료: " if ok else "⛔실패: ") + f"{path.name} (rc={rc})")
    return ok


def sweep():
    n = 0
    for p in sorted(INBOX.glob("CMD_*.json")):
        process(p)
        n += 1
    return n


def watch():
    log(f"🚀 원격 명령 실행기 시작 · 감시={INBOX} · 허용 {len(ACTIONS)}개")
    while True:
        try:
            sweep()
        except Exception as e:
            log(f"루프 오류(계속 진행): {e}")
        time.sleep(5)


def selftest():
    print("허용 명령:", ", ".join(sorted(ACTIONS)))
    print("금지 스크립트:", ", ".join(sorted(DENIED_SCRIPTS)))
    print("금지 인자:", ", ".join(sorted(DENIED_ARGS)))
    checks = []
    try:
        safe_path("/etc/passwd")
        checks.append("❌ 루트 밖 경로가 통과됨")
    except ValueError:
        checks.append("✅ 루트 밖 경로 차단")
    try:
        act_python(["cleanup_old_files.py"])
        checks.append("❌ 금지 스크립트가 통과됨")
    except ValueError:
        checks.append("✅ 금지 스크립트 차단")
    try:
        act_python(["render_trigger.py", "--dispatch"])
        checks.append("❌ 금지 인자가 통과됨")
    except ValueError:
        checks.append("✅ 금지 인자(--dispatch) 차단")
    try:
        act_restart(["존재하지않는데몬"])
        checks.append("❌ 미등록 데몬이 통과됨")
    except ValueError:
        checks.append("✅ 미등록 데몬 차단")
    print("\n".join(checks))
    return all(c.startswith("✅") for c in checks)


if __name__ == "__main__":
    if "--list" in sys.argv:
        for k in sorted(ACTIONS):
            print(f"{k:20s} {ACTIONS[k][1]}")
    elif "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    elif "--once" in sys.argv:
        print(f"처리 {sweep()}건")
    else:
        watch()
