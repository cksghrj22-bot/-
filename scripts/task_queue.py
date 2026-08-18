#!/usr/bin/env python3
"""작업 큐 — 락 충돌 없이 순차 실행
모든 git/파일 작업이 이 큐를 통해 실행됨
"""
import json
import time
import fcntl
import subprocess
from pathlib import Path
from datetime import datetime
from collections import deque

ROOT = Path(__file__).parent.parent
QUEUE_FILE = ROOT / "data/task_queue.json"
LOCK_FILE = ROOT / "data/task_queue.lock"
LOG_FILE = ROOT / "logs/task_queue.log"

QUEUE_FILE.parent.mkdir(exist_ok=True)
LOG_FILE.parent.mkdir(exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def acquire_lock():
    lock_fd = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_fd
    except BlockingIOError:
        lock_fd.close()
        return None

def release_lock(lock_fd):
    if lock_fd:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()

def load_queue():
    if QUEUE_FILE.exists():
        return json.loads(QUEUE_FILE.read_text())
    return []

def save_queue(queue):
    QUEUE_FILE.write_text(json.dumps(queue, ensure_ascii=False, indent=2))

def enqueue(task):
    """작업 추가"""
    lock = acquire_lock()
    if not lock:
        log("⚠️ 큐 락 획득 실패 — 재시도")
        time.sleep(1)
        lock = acquire_lock()
    
    try:
        queue = load_queue()
        task["id"] = f"T{int(time.time()*1000)}"
        task["status"] = "pending"
        task["created"] = datetime.now().isoformat()
        queue.append(task)
        save_queue(queue)
        log(f"📥 작업 추가: {task['id']} - {task.get('name', '?')}")
        return task["id"]
    finally:
        release_lock(lock)

def process_next():
    """다음 작업 처리"""
    lock = acquire_lock()
    if not lock:
        return None
    
    try:
        queue = load_queue()
        pending = [t for t in queue if t["status"] == "pending"]
        if not pending:
            return None
        
        task = pending[0]
        task["status"] = "running"
        task["started"] = datetime.now().isoformat()
        save_queue(queue)
        
        log(f"▶️ 실행: {task['id']} - {task.get('name', '?')}")
        
        try:
            cmd = task.get("cmd", [])
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=task.get("timeout", 300),
                cwd=str(ROOT)
            )
            task["status"] = "done" if result.returncode == 0 else "failed"
            task["output"] = result.stdout[:1000]
            task["error"] = result.stderr[:500]
        except Exception as e:
            task["status"] = "failed"
            task["error"] = str(e)
        
        task["finished"] = datetime.now().isoformat()
        save_queue(queue)
        log(f"{'✅' if task['status']=='done' else '⛔'} 완료: {task['id']}")
        return task
    finally:
        release_lock(lock)

def daemon():
    """큐 데몬 — 계속 처리"""
    log("🚀 작업 큐 데몬 시작")
    while True:
        try:
            result = process_next()
            if not result:
                time.sleep(2)
        except Exception as e:
            log(f"⛔ 에러: {e}")
            time.sleep(5)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "daemon":
        daemon()
    else:
        print("사용: task_queue.py daemon")
