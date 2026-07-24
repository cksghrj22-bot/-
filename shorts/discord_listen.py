# 디스코드 수신(폴링) = 형님 폰 → #assistant 채널 → 코드방 B가 읽음.
# 봇 토큰(읽기)로 REST 폴링. secrets/discord_bot_token.txt + secrets/discord_channel_id.txt.
# (2026-07-24 이찬호 "핸드폰이 리모콘이고 핸드폰으로 너에게 메시지가 가야해")
# ⚠️ 지속 수신은 이 세션이 깨어있을 때만. 상시 수신은 본진(Creator OS 봇) 또는 별도 루틴 결정 필요
#    (CLAUDE.md: 코드방에서 트리거/루틴 생성 금지 — 본진 전담).
import json, sys, time
import urllib.request
from pathlib import Path

API = "https://discord.com/api/v10"
TOK_PATH = "/home/user/-/secrets/discord_bot_token.txt"
CH_PATH = "/home/user/-/secrets/discord_channel_id.txt"
SEEN_PATH = "/home/user/-/secrets/discord_last_seen.txt"  # 마지막 처리 메시지 id (gitignore)


def _headers():
    tok = Path(TOK_PATH).read_text(encoding="utf-8").strip()
    return {"Authorization": f"Bot {tok}", "User-Agent": "CodeRoom-B/1.0 (+atnown)",
            "Content-Type": "application/json"}


def _channel():
    return Path(CH_PATH).read_text(encoding="utf-8").strip()


def fetch(after: str | None = None, limit: int = 20):
    """채널의 새 메시지 목록(오래된→최신). after=이 id 이후만."""
    q = f"?limit={limit}" + (f"&after={after}" if after else "")
    req = urllib.request.Request(f"{API}/channels/{_channel()}/messages{q}",
                                 headers=_headers(), method="GET")
    with urllib.request.urlopen(req, timeout=15) as r:
        msgs = json.loads(r.read().decode())
    return list(reversed(msgs))  # API는 최신순 → 오래된순으로


def new_messages(mark: bool = True):
    """마지막 처리 이후 형님(사람) 메시지만 반환. 봇 자기 메시지는 제외."""
    seen = Path(SEEN_PATH).read_text().strip() if Path(SEEN_PATH).exists() else None
    msgs = fetch(after=seen)
    out = []
    for m in msgs:
        if m.get("author", {}).get("bot"):
            continue  # 봇(코드방·Creator OS) 발신 제외
        out.append({"id": m["id"], "author": m["author"].get("username"),
                    "content": m.get("content", ""), "ts": m.get("timestamp")})
    if mark and msgs:
        Path(SEEN_PATH).write_text(msgs[-1]["id"] + "\n")
    return out


def poll(interval: int = 5, rounds: int = 0):
    """rounds=0이면 무한. 새 메시지를 stdout에 JSON으로 흘림(호출측이 처리)."""
    n = 0
    while rounds == 0 or n < rounds:
        for msg in new_messages():
            print(json.dumps(msg, ensure_ascii=False), flush=True)
        n += 1
        if rounds == 0 or n < rounds:
            time.sleep(interval)


if __name__ == "__main__":
    # python3 -m shorts.discord_listen once   → 새 메시지 한 번만 출력
    # python3 -m shorts.discord_listen poll 5 → 5초 간격 폴링
    mode = sys.argv[1] if len(sys.argv) > 1 else "once"
    if mode == "once":
        got = new_messages()
        print(json.dumps(got, ensure_ascii=False, indent=2) if got else "새 메시지 없음")
    elif mode == "poll":
        iv = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        poll(interval=iv)
