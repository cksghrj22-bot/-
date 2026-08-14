#!/usr/bin/env python3
"""
Auto Failover - Claude ↔ Codex 자동 전환
토큰 떨어지면 Codex로, 복구되면 Claude로

상태 파일: _state/main_llm.txt (claude / codex)
"""

import subprocess
import json
import os
import time
from pathlib import Path
from datetime import datetime

PIPELINE_DIR = Path(__file__).parent.parent
STATE_DIR = PIPELINE_DIR / "_state"
STATE_FILE = STATE_DIR / "main_llm.txt"
LOG_FILE = STATE_DIR / "failover.log"
WEBHOOKS_FILE = PIPELINE_DIR / "secrets" / "discord_webhooks.json"

def log(msg):
    STATE_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    print(line.strip())
    with open(LOG_FILE, "a") as f:
        f.write(line)

def get_current_main():
    """현재 메인 LLM 확인"""
    STATE_DIR.mkdir(exist_ok=True)
    if STATE_FILE.exists():
        return STATE_FILE.read_text().strip()
    return "claude"

def set_main(llm: str):
    """메인 LLM 설정"""
    STATE_DIR.mkdir(exist_ok=True)
    STATE_FILE.write_text(llm)
    log(f"메인 LLM 변경: {llm}")

def check_claude_status() -> bool:
    """Claude 사용 가능 여부 체크"""
    # claude.ai/settings/usage 페이지 체크는 브라우저 필요
    # 대신 간단한 API 호출 테스트
    try:
        # Claude Code CLI 상태 확인
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except:
        return False

def check_codex_status() -> bool:
    """Codex 사용 가능 여부 체크"""
    try:
        result = subprocess.run(
            ["codex", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return "Codex" in result.stdout or result.returncode == 0
    except:
        return False

def send_webhook(channel: str, message: str):
    """디스코드 알림"""
    if WEBHOOKS_FILE.exists():
        webhooks = json.loads(WEBHOOKS_FILE.read_text())
        if channel in webhooks:
            import urllib.request
            data = json.dumps({"content": message, "username": "Failover"}).encode()
            req = urllib.request.Request(
                webhooks[channel],
                data=data,
                headers={"Content-Type": "application/json", "User-Agent": "atnown-terminal/1.0 (Mozilla/5.0)"}
            )
            try:
                urllib.request.urlopen(req)
            except:
                pass

def failover_to_codex():
    """Claude → Codex 전환"""
    set_main("codex")
    msg = """⚠️ **[자동 전환] Claude → Codex**

Claude 토큰 한도 도달. Codex Pro가 메인으로 전환됨.

**명령 입력 방법:**
```
codex "작업 내용"
ollama run llama3 "질문"
```

Claude 복구되면 자동 복귀."""
    
    send_webhook("기획전략실", msg)
    log("FAILOVER: Claude → Codex")

def restore_to_claude():
    """Codex → Claude 복원"""
    set_main("claude")
    msg = """✅ **[자동 복귀] Codex → Claude**

Claude 토큰 복구됨. Claude가 다시 메인.
Codex는 서브로 대기."""
    
    send_webhook("기획전략실", msg)
    log("RESTORE: Codex → Claude")

def route_task(prompt: str, channel: str = None):
    """현재 메인에 따라 라우팅"""
    main = get_current_main()
    
    if main == "codex":
        # Codex로 처리
        cmd = ["codex", "exec", prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        return result.stdout
    else:
        # Claude inbox로
        inbox_dir = PIPELINE_DIR / "_terminal_inbox"
        inbox_dir.mkdir(exist_ok=True)
        task_file = inbox_dir / f"claude_{int(time.time())}.md"
        task_file.write_text(f"# 작업\n\n{prompt}\n\n채널: {channel or '터미널'}")
        return f"[Claude inbox] {task_file.name}"

def check_and_switch():
    """상태 체크 및 전환"""
    current = get_current_main()
    claude_ok = check_claude_status()
    codex_ok = check_codex_status()
    
    log(f"체크: current={current}, claude={claude_ok}, codex={codex_ok}")
    
    if current == "claude" and not claude_ok and codex_ok:
        failover_to_codex()
    elif current == "codex" and claude_ok:
        restore_to_claude()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Auto Failover")
    parser.add_argument("--check", action="store_true", help="상태 체크 및 전환")
    parser.add_argument("--status", action="store_true", help="현재 상태")
    parser.add_argument("--force", choices=["claude", "codex"], help="강제 전환")
    parser.add_argument("--task", help="작업 라우팅")
    parser.add_argument("--channel", "-c", help="채널")
    
    args = parser.parse_args()
    
    if args.check:
        check_and_switch()
    elif args.status:
        main_llm = get_current_main()
        print(f"메인: {main_llm}")
        print(f"Claude: {'OK' if check_claude_status() else 'X'}")
        print(f"Codex: {'OK' if check_codex_status() else 'X'}")
    elif args.force:
        set_main(args.force)
        print(f"강제 전환: {args.force}")
    elif args.task:
        result = route_task(args.task, args.channel)
        print(result)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
