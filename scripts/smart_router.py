#!/usr/bin/env python3
"""
스마트 라우터 — Ollama 우선, Claude 마지막
토큰 절약용. 2026-08-16

사용법:
    python3 scripts/smart_router.py "요약해줘: 긴 텍스트..."
    python3 scripts/smart_router.py --claude "차노 목소리로 대본 써줘"
    python3 scripts/smart_router.py --status
"""

import subprocess
import sys
import re
import json
from pathlib import Path

# Ollama로 보낼 키워드 (단순 작업)
OLLAMA_KEYWORDS = [
    "요약", "정리", "번역", "translate", "분류", "나열", "리스트",
    "몇 개", "몇개", "찾아", "검색", "비교", "차이", "설명해",
    "뭐야", "뭔지", "알려줘", "what is", "explain", "summarize",
    "count", "list", "compare", "포맷", "변환", "convert"
]

# Claude 필수 키워드 (창작/판단)
CLAUDE_KEYWORDS = [
    "차노", "대본", "글써", "작성", "기획", "전략", "판단",
    "코드", "스크립트", "버그", "수정", "디버그", "리뷰",
    "보이스", "톤", "서사", "스토리", "창작", "아이디어"
]

def should_use_claude(prompt: str) -> bool:
    prompt_lower = prompt.lower()
    for kw in CLAUDE_KEYWORDS:
        if kw in prompt_lower:
            return True
    return False

def should_use_ollama(prompt: str) -> bool:
    prompt_lower = prompt.lower()
    for kw in OLLAMA_KEYWORDS:
        if kw in prompt_lower:
            return True
    return False

def run_ollama(prompt: str) -> str:
    """Ollama llama3 실행 (무료, 로컬)"""
    try:
        result = subprocess.run(
            ["ollama", "run", "llama3", prompt],
            capture_output=True, text=True, timeout=120
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "[Ollama 타임아웃 - Claude로 전환 필요]"
    except Exception as e:
        return f"[Ollama 오류: {e}]"

def log_usage(model: str, prompt_preview: str):
    """사용 로그 기록"""
    log_path = Path(__file__).parent.parent / "_state" / "router_log.jsonl"
    log_path.parent.mkdir(exist_ok=True)

    from datetime import datetime
    entry = {
        "ts": datetime.now().isoformat(),
        "model": model,
        "prompt": prompt_preview[:50]
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def get_stats():
    """라우팅 통계"""
    log_path = Path(__file__).parent.parent / "_state" / "router_log.jsonl"
    if not log_path.exists():
        return {"ollama": 0, "claude": 0, "절약률": "0%"}

    ollama_count = 0
    claude_count = 0
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            entry = json.loads(line)
            if entry.get("model") == "ollama":
                ollama_count += 1
            else:
                claude_count += 1

    total = ollama_count + claude_count
    if total == 0:
        return {"ollama": 0, "claude": 0, "절약률": "0%"}

    savings = round(ollama_count / total * 100)
    return {
        "ollama": ollama_count,
        "claude": claude_count,
        "절약률": f"{savings}%"
    }

def main():
    if len(sys.argv) < 2:
        print("사용법: python3 scripts/smart_router.py \"질문\"")
        print("       python3 scripts/smart_router.py --claude \"Claude 필수 작업\"")
        print("       python3 scripts/smart_router.py --status")
        sys.exit(1)

    if sys.argv[1] == "--status":
        stats = get_stats()
        print(f"📊 라우터 통계")
        print(f"   Ollama: {stats['ollama']}회 (무료)")
        print(f"   Claude: {stats['claude']}회 (유료)")
        print(f"   절약률: {stats['절약률']}")
        sys.exit(0)

    force_claude = sys.argv[1] == "--claude"
    if force_claude:
        prompt = " ".join(sys.argv[2:])
    else:
        prompt = " ".join(sys.argv[1:])

    if not prompt.strip():
        print("질문을 입력하세요")
        sys.exit(1)

    # 라우팅 결정
    if force_claude or should_use_claude(prompt):
        print("[→ Claude 필요 - 여기서 직접 작업하세요]")
        print(f"질문: {prompt[:100]}...")
        log_usage("claude", prompt)
    elif should_use_ollama(prompt):
        print("[→ Ollama (무료)]")
        print("-" * 40)
        response = run_ollama(prompt)
        print(response)
        log_usage("ollama", prompt)
    else:
        # 기본: Ollama 먼저 시도
        print("[→ Ollama 시도 (기본)]")
        print("-" * 40)
        response = run_ollama(prompt)
        print(response)
        log_usage("ollama", prompt)

if __name__ == "__main__":
    main()
