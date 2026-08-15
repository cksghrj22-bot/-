#!/usr/bin/env python3
"""
TASK 실행 데몬 — _terminal_inbox의 TASK 파일 처리
코워크 → 드라이브 → cowork_multi_watch → TASK → [이 스크립트] → 실행

2026-08-14 생성
"""
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
INBOX = ROOT / "_terminal_inbox"
DONE = INBOX / "_done"
LOG = ROOT / "data/task_executor.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def execute_task(task_file: Path):
    """TASK 파일 읽고 실행"""
    try:
        task = json.loads(task_file.read_text())
        room = task.get("room", "unknown")
        title = task.get("title", "")
        request = task.get("request", "")

        log(f"📥 [{room}] {title}")

        # request에서 명령어 추출 (```bash ... ``` 블록 또는 전체)
        cmd = extract_command(request)

        if cmd:
            log(f"🔧 실행: {cmd[:100]}...")
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=300
            )

            output = result.stdout + result.stderr
            status = "success" if result.returncode == 0 else "failed"

            # 결과 기록
            task["executed_at"] = datetime.now().isoformat()
            task["status"] = status
            task["output"] = output[:5000]
            task["return_code"] = result.returncode

            log(f"{'✅' if status == 'success' else '❌'} [{room}] rc={result.returncode}")

            # _done으로 이동 (명령어 있을 때만)
            DONE.mkdir(exist_ok=True)
            done_file = DONE / task_file.name
            done_file.write_text(json.dumps(task, ensure_ascii=False, indent=2))
            task_file.unlink()
        else:
            # 명령어 없으면 스킵 — terminal_watcher.py가 처리하도록 남겨둠
            log(f"⏭️ [{room}] bash 명령 없음, 스킵 (Codex용)")

    except subprocess.TimeoutExpired:
        log(f"⏰ [{room}] 타임아웃 (5분)")
        move_to_done(task_file, "timeout")
    except Exception as e:
        log(f"❌ 처리 실패: {e}")
        move_to_done(task_file, f"error: {e}")

def extract_command(text: str) -> str:
    """텍스트에서 bash 명령어 추출"""
    import re

    # ```bash ... ``` 블록 찾기
    match = re.search(r'```(?:bash|sh)?\n(.+?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # python3 또는 bash로 시작하는 줄 찾기
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith(('python3 ', 'bash ', 'sh ', './')):
            return line

    return ""

def move_to_done(task_file: Path, status: str):
    """에러난 파일도 _done으로 이동"""
    try:
        DONE.mkdir(exist_ok=True)
        task = json.loads(task_file.read_text())
        task["status"] = status
        task["executed_at"] = datetime.now().isoformat()
        (DONE / task_file.name).write_text(json.dumps(task, ensure_ascii=False, indent=2))
        task_file.unlink()
    except:
        pass

def watch():
    """INBOX 감시 루프"""
    log("🚀 TASK 실행 데몬 시작")

    while True:
        try:
            # TASK_*.json 파일 찾기
            tasks = sorted(INBOX.glob("TASK_*.json"))

            for task_file in tasks:
                execute_task(task_file)

        except Exception as e:
            log(f"❌ 감시 에러: {e}")

        time.sleep(2)

def once():
    """한 번만 실행"""
    tasks = sorted(INBOX.glob("TASK_*.json"))
    log(f"📋 {len(tasks)}개 TASK 발견")
    for task_file in tasks:
        execute_task(task_file)

if __name__ == "__main__":
    import sys
    if "--daemon" in sys.argv:
        watch()
    elif "--once" in sys.argv:
        once()
    else:
        print("사용법: python3 task_executor.py [--daemon|--once]")
        print("  --daemon: 계속 감시")
        print("  --once: 한 번만 실행")
