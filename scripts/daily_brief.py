#!/usr/bin/env python3
"""매일 브리프 — 형에게 필요한 것만 요약

형이 볼 것: 승인 대기 항목 + 완료된 것
내가 처리한 것: 유지보수 로그 (안 보여도 됨)
"""
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent

def get_pending_approvals():
    """승인 대기 중인 것"""
    items = []
    
    # 콘텐츠 팩토리 큐
    q_file = ROOT / "data/content_queue.json"
    if q_file.exists():
        q = json.loads(q_file.read_text())
        for s in q.get("pending", []):
            if s.get("status") == "awaiting_approval":
                items.append({
                    "type": "콘텐츠",
                    "id": s["id"],
                    "summary": s["seed"][:30],
                    "action": "승인/거절"
                })
    
    # 터미널 인박스
    inbox = ROOT / "_terminal_inbox"
    if inbox.exists():
        for f in inbox.glob("TASK_*.json"):
            try:
                t = json.loads(f.read_text())
                if t.get("status") == "pending":
                    items.append({
                        "type": "작업",
                        "id": f.stem,
                        "summary": t.get("title", "?")[:30],
                        "action": "대기중"
                    })
            except:
                pass
    
    return items

def get_completed_today():
    """오늘 완료된 것"""
    today = datetime.now().strftime("%Y-%m-%d")
    items = []
    
    done = ROOT / "_terminal_inbox/_done"
    if done.exists():
        for f in done.glob("*.json"):
            try:
                if today in f.name:
                    items.append(f.stem[:40])
            except:
                pass
    
    return items[-5:]  # 최근 5개만

def get_system_status():
    """시스템 상태 한 줄"""
    import subprocess
    r = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    running = len([l for l in r.stdout.split("\n") if "atnown" in l and not l.startswith("-")])
    return f"데몬 {running}개 가동"

def brief():
    print("=" * 50)
    print(f"📋 데일리 브리프 — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    
    # 시스템
    print(f"\n🖥️ 시스템: {get_system_status()}")
    
    # 승인 대기
    pending = get_pending_approvals()
    if pending:
        print(f"\n⏳ 승인 대기 ({len(pending)}건):")
        for p in pending[:5]:
            print(f"  • [{p['type']}] {p['summary']}... → {p['action']}")
    else:
        print("\n⏳ 승인 대기: 없음")
    
    # 완료
    done = get_completed_today()
    if done:
        print(f"\n✅ 오늘 완료 ({len(done)}건):")
        for d in done:
            print(f"  • {d}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    brief()
