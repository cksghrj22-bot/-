# 코드방(B방 Claude) → 디스코드 발송 = 내가 상위에서 Creator OS(본진)를 부르는 채널.
# (2026-07-24 이찬호 "너가 상위단계니까 니가 디스코드를 불러야지 / 무조건 연동해")
# secrets/discord_webhook.txt 에 디스코드 채널 웹훅 URL 한 줄만 넣으면 즉시 가동.
import sys, json, urllib.request
from pathlib import Path

WEBHOOK_PATH = "/home/user/-/secrets/discord_webhook.txt"

def send(text: str, webhook_path: str = WEBHOOK_PATH) -> int:
    p = Path(webhook_path)
    if not p.exists():
        raise FileNotFoundError(f"웹훅 URL 없음: {webhook_path} — 디스코드 채널 웹훅 URL 한 줄 저장 필요")
    url = p.read_text(encoding="utf-8").strip()
    if not url.startswith("https://"):
        raise ValueError(f"웹훅 URL 형식 이상: {url[:40]!r}")
    body = json.dumps({"content": text[:2000], "username": "코드방(B방)"}).encode("utf-8")
    req = urllib.request.Request(url, data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status  # 204 = 성공

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "코드방→디스코드 연동 테스트 (B방 Claude). 이 메시지 보이면 상위 오케스트레이터 연동 성공."
    try:
        print("보냄 status =", send(msg), "(204=성공)")
    except Exception as e:
        print("실패:", e)
        sys.exit(1)
