"""스레드(Threads) API 발행 — 표준 라이브러리만 사용.

secrets/threads.json 형식 (gitignore — 절대 커밋 금지):
    {
      "access_token": "...",          # Threads API 장기 토큰 (본진작업지시 7번)
      "user_id": "..."                # 생략 가능 — 없으면 /me로 조회해 자동 저장
    }

사용:
    python3 -m shorts.threads check                       # 토큰·계정 확인
    python3 -m shorts.threads publish content/threads/파일.md   # 게시문 발행 (--- 아래 본문)
    python3 -m shorts.threads publish --text "한 줄 글"
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://graph.threads.net/v1.0"
DEFAULT_SECRETS = "secrets/threads.json"


def load_secrets(path: str | Path = DEFAULT_SECRETS) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"스레드 자격증명 없음: {p} — 본진작업지시 7번(threads 토큰) 필요")
    creds = json.loads(p.read_text(encoding="utf-8"))
    if "access_token" not in creds:
        raise ValueError(f"{p}에 access_token 없음")
    return creds


def _get(url: str, timeout: int = 30) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read())


def _post(url: str, data: dict, timeout: int = 60) -> dict:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def resolve_user_id(creds: dict, secrets_path: str | Path = DEFAULT_SECRETS) -> str:
    """user_id가 없으면 /me로 조회해서 secrets에 저장한다."""
    if creds.get("user_id"):
        return creds["user_id"]
    me = _get(f"{API}/me?fields=id,username&access_token={urllib.parse.quote(creds['access_token'])}")
    creds["user_id"] = me["id"]
    Path(secrets_path).write_text(json.dumps(creds, ensure_ascii=False, indent=2), encoding="utf-8")
    return me["id"]


def extract_body(md_text: str) -> str:
    """게시문 md 파일에서 본문만 뽑는다 — `---` 구분선 아래가 본문."""
    if "\n---\n" in md_text:
        return md_text.split("\n---\n", 1)[1].strip()
    return md_text.strip()


def publish_text(text: str, creds: dict, secrets_path: str | Path = DEFAULT_SECRETS) -> str:
    """텍스트 스레드를 발행하고 게시물 ID를 돌려준다 (컨테이너 생성 → 발행 2단계)."""
    uid = resolve_user_id(creds, secrets_path)
    token = creds["access_token"]
    container = _post(f"{API}/{uid}/threads", {
        "media_type": "TEXT", "text": text, "access_token": token,
    })
    time.sleep(2)  # 컨테이너 처리 대기 (공식 권장)
    result = _post(f"{API}/{uid}/threads_publish", {
        "creation_id": container["id"], "access_token": token,
    })
    return result["id"]


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="스레드 발행")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_c = sub.add_parser("check")
    p_c.add_argument("--secrets", default=DEFAULT_SECRETS)
    p_p = sub.add_parser("publish")
    p_p.add_argument("file", nargs="?", default=None, help="게시문 md 파일 (--- 아래가 본문)")
    p_p.add_argument("--text", default=None)
    p_p.add_argument("--secrets", default=DEFAULT_SECRETS)
    args = ap.parse_args(argv)

    creds = load_secrets(args.secrets)
    if args.cmd == "check":
        uid = resolve_user_id(creds, args.secrets)
        me = _get(f"{API}/{uid}?fields=id,username&access_token={urllib.parse.quote(creds['access_token'])}")
        print(f"✅ 스레드 연결 OK — @{me.get('username')} (id {me.get('id')})")
        return 0

    text = args.text or extract_body(Path(args.file).read_text(encoding="utf-8"))
    if not text:
        print("❌ 발행할 본문이 없습니다", file=sys.stderr)
        return 1
    post_id = publish_text(text, creds, args.secrets)
    print(f"✅ 스레드 발행 완료 — 게시물 ID {post_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
