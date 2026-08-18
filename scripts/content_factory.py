#!/usr/bin/env python3
"""콘텐츠 팩토리 — 씨앗에서 완성까지 자동화

형: 씨앗 + yes/no
나: 확장 + 레퍼런스 + 제작 + 발행 + 시스템 유지
"""
import json
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
SEEDS = ROOT / "content/seeds"
REFS = ROOT / "content/references"
QUEUE = ROOT / "data/content_queue.json"

SEEDS.mkdir(parents=True, exist_ok=True)
REFS.mkdir(parents=True, exist_ok=True)
QUEUE.parent.mkdir(exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def load_queue():
    if QUEUE.exists():
        return json.loads(QUEUE.read_text())
    return {"pending": [], "approved": [], "done": []}

def save_queue(q):
    QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=2))

def add_seed(seed_text, content_type="shorts"):
    """씨앗 추가 → 확장 제안 생성"""
    q = load_queue()
    seed = {
        "id": f"S{int(datetime.now().timestamp())}",
        "seed": seed_text,
        "type": content_type,
        "created": datetime.now().isoformat(),
        "status": "needs_approval",
        "expanded": None,
        "references": []
    }
    q["pending"].append(seed)
    save_queue(q)
    log(f"📌 씨앗 추가: {seed['id']}")
    return seed

def expand_seed(seed_id):
    """씨앗을 콘텐츠 제안으로 확장"""
    q = load_queue()
    for s in q["pending"]:
        if s["id"] == seed_id:
            # 여기서 실제로는 LLM 호출해서 확장
            s["expanded"] = {
                "title": f"[제안] {s['seed'][:20]}...",
                "outline": "1. 도입\n2. 본문\n3. 마무리",
                "angle": "차노 시점에서",
            }
            s["status"] = "awaiting_approval"
            save_queue(q)
            log(f"📝 확장 완료: {seed_id}")
            return s
    return None

def approve(seed_id):
    """형 승인 → 제작 대기열로"""
    q = load_queue()
    for i, s in enumerate(q["pending"]):
        if s["id"] == seed_id:
            s["status"] = "approved"
            s["approved_at"] = datetime.now().isoformat()
            q["approved"].append(q["pending"].pop(i))
            save_queue(q)
            log(f"✅ 승인됨: {seed_id}")
            return True
    return False

def reject(seed_id, reason=""):
    """거절 → 수정 또는 폐기"""
    q = load_queue()
    for s in q["pending"]:
        if s["id"] == seed_id:
            s["status"] = "rejected"
            s["reject_reason"] = reason
            save_queue(q)
            log(f"❌ 거절됨: {seed_id} - {reason}")
            return True
    return False

def get_status():
    """현재 상태"""
    q = load_queue()
    return {
        "대기중": len(q["pending"]),
        "승인됨": len(q["approved"]),
        "완료": len(q["done"])
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("사용: content_factory.py [add|status|approve|reject] ...")
        print(f"현재: {get_status()}")
    elif sys.argv[1] == "status":
        print(json.dumps(get_status(), ensure_ascii=False))
    elif sys.argv[1] == "add" and len(sys.argv) > 2:
        add_seed(" ".join(sys.argv[2:]))
