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
LOGS = ROOT / "logs"

DONE.mkdir(exist_ok=True)
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
    """Codex CLI로 작업 전달"""
    room = task.get("room", "알수없음")
    title = task.get("title") or task.get("task") or "제목없음"
    # CLAUDE.md 규격은 {"room","task","timeout"} — request/instructions 도 함께 받는다
    request = task.get("request") or task.get("task") or task.get("instructions") or ""
    if not isinstance(request, str):
        request = json.dumps(request, ensure_ascii=False, indent=2)

    prompt = f"""
방: {room}
제목: {title}

요청:
{request}

작업 완료 후 결과만 간단히 보고.
"""

    try:
        result = subprocess.run(
            ["codex", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(ROOT)
        )
        return result.stdout if result.returncode == 0 else f"오류: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "오류: 5분 타임아웃"
    except Exception as e:
        return f"오류: {e}"

def process_task(filepath, task):
    log(f"처리 시작: {task.get('title', '?')}")

    task["status"] = "processing"
    filepath.write_text(json.dumps(task, ensure_ascii=False, indent=2))

    result = dispatch_to_codex(task)

    task["status"] = "done"
    task["completed_at"] = datetime.now().isoformat()
    task["codex_result"] = result[:2000]

    done_path = DONE / filepath.name
    done_path.write_text(json.dumps(task, ensure_ascii=False, indent=2))
    filepath.unlink()

    log(f"완료: {task.get('title', '?')}")
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
