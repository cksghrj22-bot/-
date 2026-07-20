"""스레드 예약 발행기 — content/threads/스레드_예약.json을 읽어, 예약시각이 지난 미발행 글을
secrets/threads.json 토큰으로 자동 발행하고 posted 표시. 자가 루프가 매시 호출한다.

토큰(secrets/threads.json)이 없으면 조용히 스킵(발행 안 함) — 토큰 들어오면 그때부터 자동 발행.
과거 예약은 지난 즉시 올라가고, 미래 예약은 시각이 되면 올라간다.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

SCHEDULE = Path("content/threads/스레드_예약.json")
TOKEN = Path("secrets/threads.json")


def run(now: datetime | None = None, schedule_path: Path = SCHEDULE) -> dict:
    now = now or datetime.now(timezone.utc)
    if not schedule_path.exists():
        return {"status": "no_schedule", "posted": [], "pending": [], "skipped_no_token": []}
    data = json.loads(schedule_path.read_text(encoding="utf-8"))
    posted, pending, skipped = [], [], []
    have_token = TOKEN.exists()
    if have_token:
        from . import threads
        creds = threads.load_secrets(TOKEN)
    for item in data:
        if item.get("posted"):
            continue
        due = datetime.fromisoformat(item["publish_at"].replace("Z", "+00:00")) <= now
        if not due:
            pending.append(item["label"]); continue
        if not have_token:
            skipped.append(item["label"]); continue
        try:
            pid = threads.publish_text(item["text"], creds, TOKEN)
            item["posted"] = True; item["thread_id"] = pid
            posted.append((item["label"], pid))
        except Exception as e:  # 한 편 실패해도 나머지 계속
            item["error"] = repr(e)[:200]
    schedule_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "ok", "posted": posted, "pending": pending, "skipped_no_token": skipped,
            "have_token": have_token}


if __name__ == "__main__":
    import sys
    r = run()
    print(json.dumps(r, ensure_ascii=False, indent=2))
    if r.get("skipped_no_token"):
        print(f"\n⏸ 토큰 없어 {len(r['skipped_no_token'])}편 대기 — secrets/threads.json 넣으면 자동 발행", file=sys.stderr)
