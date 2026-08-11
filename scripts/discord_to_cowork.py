#!/usr/bin/env python3
# 디스코드 #assistant 대화 → atnown-trunk/_cowork_sync/discord_assistant_live.md → GitHub push.
# 목적: 클라우드 코워크 방이 git pull 로 이 대화를 읽게 한다 (SSOT = GitHub origin).
#
# 읽기 소스에 대한 사실(2026-08-11 조사):
#   discord_listen.py 는 봇 토큰(secrets/discord_bot_token.txt)으로 Discord REST 를 폴링한다.
#   그러나 그 봇 토큰은 클라우드 방(/home/user/-/secrets/)에만 있고 이 맥에는 없다.
#   이 맥의 로컬 SSOT 는 Creator OS(본진)가 이미 이 채널의 모든 메시지를 실시간 적재해 둔
#   Postgres 테이블 creator_os_capture_events 다 (phone_to_obsidian.py 와 동일한 로컬 DB 패턴).
#   → 봇 토큰 없이도 차노쌤(사람)+Assistant(봇/webhook) 양쪽을 다 뽑을 수 있다. 필터링 안 함.
import json, os, subprocess, sys
from datetime import datetime, timezone, timedelta

CHANNEL_ID = "1518460128968572958"           # #assistant
TRUNK      = os.path.expanduser("~/atnown-trunk")
OUT        = os.path.join(TRUNK, "_cowork_sync", "discord_assistant_live.md")
PSQL       = "/Applications/Creator OS.app/Contents/Resources/vendor/postgres/bin/psql"
LIMIT      = 100
KST        = timezone(timedelta(hours=9))

# Creator-OS 봇이 뿌리는 순간적 진행 표시(대화 맥락 아님) — 노이즈 제거
NOISE = ("⏳", "🕐", "🔧 도구 사용", "처리 중", "이어서 이 메시지도 답변")


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def fetch_messages():
    """capture_events 에서 채널 최근 LIMIT개를 오래된→최신 순으로 반환."""
    if not os.path.exists(PSQL):
        log(f"[ERR] Creator OS psql 없음: {PSQL} — Creator OS 미설치/미기동")
        sys.exit(1)
    # 최신 LIMIT개를 뽑아 파이썬에서 오래된순으로 뒤집는다.
    q = (
        "SELECT row_to_json(t) FROM ("
        "SELECT discord_message_id AS id, "
        "to_char(created_at,'YYYY-MM-DD\"T\"HH24:MI:SSOF') AS ts, "
        "coalesce(payload->'discord'->>'author_display_name', "
        "         payload->'discord'->>'author_username','?') AS author, "
        "coalesce(payload->'discord'->>'is_bot','false') AS is_bot, "
        "coalesce(payload->'discord'->>'content','') AS content "
        f"FROM creator_os_capture_events WHERE channel_id={CHANNEL_ID} "
        f"ORDER BY created_at DESC LIMIT {LIMIT}) t"
    )
    try:
        r = subprocess.run(
            [PSQL, "-h", "127.0.0.1", "-p", "5434", "-U", "creator_os",
             "-d", "creator_os", "-t", "-A", "-c", q],
            capture_output=True, text=True, timeout=30)
    except Exception as e:
        log(f"[ERR] psql 실행 실패: {e}")
        sys.exit(1)
    if r.returncode != 0:
        log(f"[ERR] psql 오류(rc={r.returncode}): {r.stderr.strip()[:300]}")
        sys.exit(1)
    rows = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    rows.reverse()  # 오래된 → 최신
    return rows


def to_kst(ts):
    """ISO ts → 'YYYY-MM-DD HH:MM' (KST)."""
    try:
        dt = datetime.fromisoformat(ts)
        return dt.astimezone(KST).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return (ts or "")[:16].replace("T", " ")


def render(rows):
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")
    out = [
        "# 디스코드 #assistant 대화 (자동 동기화)",
        "",
        f"_마지막 갱신: {now} · 최근 {LIMIT}개 · 소스: Creator OS capture_events (SSOT)_",
        "",
        "---",
        "",
    ]
    kept = 0
    for m in rows:
        content = (m.get("content") or "").strip()
        if not content:
            continue
        if any(n in content for n in NOISE) and len(content) < 120:
            continue  # 짧은 순간표시만 스킵 (실제 발화 안에 이모지 들어간 건 유지)
        author = m.get("author") or "?"
        when = to_kst(m.get("ts", ""))
        out.append(f"**[{author}] ({when})**")
        out.append(content)
        out.append("")
        kept += 1
    if kept == 0:
        out.append("_(표시할 메시지 없음)_")
    return "\n".join(out) + "\n"


def git(*args, check=True):
    r = subprocess.run(["git", "-C", TRUNK, *args],
                       capture_output=True, text=True,
                       env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    if check and r.returncode != 0:
        log(f"[ERR] git {' '.join(args)} 실패(rc={r.returncode}): {r.stderr.strip()[:300]}")
        sys.exit(1)
    return r


def main():
    rows = fetch_messages()
    md = render(rows)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    prev = ""
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            prev = f.read()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(md)
    log(f"[OK] {OUT} 작성 ({len(rows)}행 처리)")

    # 헤더의 '마지막 갱신' 시각은 매번 바뀌므로, 본문(대화)이 실제로 바뀐 경우에만 커밋.
    def body(s):
        return "\n".join(l for l in s.splitlines() if not l.startswith("_마지막 갱신"))
    if body(prev) == body(md):
        log("[SKIP] 대화 내용 변화 없음 — commit/push 생략")
        return

    branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip() or "main"
    git("add", "_cowork_sync/discord_assistant_live.md")
    st = git("status", "--porcelain", "_cowork_sync/discord_assistant_live.md").stdout.strip()
    if not st:
        log("[SKIP] git diff 없음 — commit/push 생략")
        return
    git("commit", "-m", "sync: discord #assistant 대화 자동 갱신")
    # 다른 방과 충돌 방지: pull --rebase 후 push (CLAUDE.md 방 자동동기화 규약)
    git("pull", "--rebase", "origin", branch, check=False)
    push = git("push", "origin", f"HEAD:{branch}", check=False)
    if push.returncode != 0:
        log(f"[ERR] git push 실패(rc={push.returncode}): {push.stderr.strip()[:400]}")
        sys.exit(1)
    log(f"[OK] push 성공 → origin/{branch}")


if __name__ == "__main__":
    main()
