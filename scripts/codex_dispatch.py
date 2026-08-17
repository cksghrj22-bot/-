#!/usr/bin/env python3
"""
Codex 본진 디스패처 — inbox TASK를 Codex에 전달

Claude 토큰 고갈 시 또는 Codex 본진 전환 시 사용
terminal_watcher.py 대신 이것을 LaunchAgent로 등록
"""
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
INBOX = ROOT / "_terminal_inbox"
DONE = INBOX / "_done"
FAILED = INBOX / "_failed"
LOGS = ROOT / "logs"

DONE.mkdir(exist_ok=True)
FAILED.mkdir(exist_ok=True)
LOGS.mkdir(exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOGS / "codex_dispatch.log", "a") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

def get_pending_tasks():
    tasks = []
    for f in INBOX.glob("TASK_*.json"):
        try:
            task = json.loads(f.read_text())
            if task.get("status", "pending") == "pending":
                tasks.append((f, task))
        except:
            pass
    return sorted(tasks, key=lambda x: x[1].get("created_at", ""))

def dispatch_to_codex(task):
    """Codex CLI로 작업 전달 (비대화형 exec)"""
    room = task.get("room", "알수없음")
    title = task.get("title") or task.get("task") or "제목없음"
    # CLAUDE.md 규격은 {"room","task","timeout"} — request/instructions 도 함께 받는다
    request = task.get("request") or task.get("task") or task.get("instructions") or ""
    if not isinstance(request, str):
        request = json.dumps(request, ensure_ascii=False, indent=2)

    prompt = f"""방: {room}
제목: {title}

요청:
{request}

작업 완료 후 결과만 간단히 보고.
"""

    try:
        timeout = int(task.get("timeout") or 300)
    except (TypeError, ValueError):
        timeout = 300
    timeout = max(30, min(timeout, 1800))

    # ⚠️ 2026-08-17 실사고: `codex -p <프롬프트>` 로 보내고 있었다.
    #    codex 의 -p 는 --profile(프로파일 이름)이라 주문서 전량이
    #    "invalid --profile value" 로 실패했다. 비대화형 실행은 `codex exec <프롬프트>` 다.
    # ⚠️ 2026-08-17 실사고 #2 — 샌드박스가 네트워크를 끊고 있었다.
    #    실측: CODEX_SANDBOX=seatbelt · CODEX_SANDBOX_NETWORK_DISABLED=1
    #          → `curl: (6) Could not resolve host` · `scutil --dns: No DNS configuration available`
    #    증상: 드라이브 다운로드·pip 설치 등 셸에서 나가는 작업이 전부 죽었다.
    #          MCP 커넥터는 코덱스 자체 통로라 살아있지만 34MB 넘는 파일을 못 받는다.
    #    조치: 차노 2026-08-17 지시("무조건 드라이브에서 받아라") → 샌드박스 네트워크를 연다.
    NET = ["--sandbox", "danger-full-access"]
    attempts = [
        ["codex", "exec"] + NET + [prompt],   # 네트워크 허용 (기본)
        ["codex", "exec", prompt],            # 플래그 미지원 CLI 폴백
        ["codex", prompt],                    # 구버전 폴백(위치인자)
    ]
    last_err = ""
    for cmd in attempts:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(ROOT),
            )
        except subprocess.TimeoutExpired:
            return f"오류: {timeout}초 타임아웃"
        except FileNotFoundError:
            return "오류: codex CLI 없음 (PATH 확인)"
        except Exception as e:
            return f"오류: {e}"

        if result.returncode == 0:
            return result.stdout

        last_err = (result.stderr or result.stdout or "").strip()
        # 인자 형식 문제일 때만 다음 후보로 넘어간다
        if not any(k in last_err for k in ("unexpected argument", "unrecognized subcommand", "invalid value")):
            break

    return f"오류: {last_err}"

def process_task(filepath, task):
    name = task.get("title") or task.get("task") or "?"
    log(f"처리 시작: {name}")

    task["status"] = "processing"
    filepath.write_text(json.dumps(task, ensure_ascii=False, indent=2))

    result = dispatch_to_codex(task)

    # 공유규약 §10-6 「발주 ≠ 완료」 — 실패를 done 으로 찍지 않는다.
    # 예전 코드는 무조건 done + _done 이동이라 실패 주문서가 조용히 사라졌다(2026-08-17 실사고).
    ok = not result.lstrip().startswith("오류:")

    task["status"] = "done" if ok else "failed"
    task["completed_at"] = datetime.now().isoformat()
    task["codex_result"] = result[:2000]

    dest = (DONE if ok else FAILED) / filepath.name
    dest.write_text(json.dumps(task, ensure_ascii=False, indent=2))
    filepath.unlink()

    log(("완료: " if ok else "⛔실패(→_failed): ") + name)
    return result

def watch():
    log("🚀 Codex 디스패처 시작 (5초 간격)")
    while True:
        tasks = get_pending_tasks()
        for filepath, task in tasks:
            process_task(filepath, task)
        time.sleep(5)

if __name__ == "__main__":
    import sys
    if "--daemon" in sys.argv:
        watch()
    elif "--once" in sys.argv:
        tasks = get_pending_tasks()
        for filepath, task in tasks:
            process_task(filepath, task)
    else:
        watch()
