#!/usr/bin/env python3
# 웹·디스코드 #assistant 대화 → atnown-trunk/_cowork_sync/discord_assistant_live.md → GitHub push.
# 목적: 클라우드 코워크 방이 git pull 로 이 대화를 읽게 한다 (SSOT = GitHub origin).
#
# 읽기 소스에 대한 사실(2026-08-11 조사):
#   Creator OS(본진)가 이 채널들의 모든 메시지를 실시간 적재해 둔 Postgres 테이블
#   creator_os_capture_events 가 로컬 SSOT 다. 봇 토큰 없이도 뽑을 수 있다.
#   같은 인박스가 두 표면(surface)으로 갈라져 서로 다른 channel_id 로 적재된다:
#     · 디스코드 #assistant  = 1518460128968572958
#     · 웹 스튜디오 채팅      = 1536635887780110509 (session logical_channel_id)
#   웹에서 차노쌤(사람)의 발화는 author="Creator-OS" + 본문 앞 "🌐 " 접두로 저장되므로,
#   여기서 사람 발화로 되살려 라벨링한다. 두 표면을 시간순으로 병합해 한 파일에 쓴다
#   ("한 바탕에서 공유" 원칙).
import json, os, subprocess, sys
from datetime import datetime, timezone, timedelta

# (channel_id, 표면 라벨) — 새 표면이 생기면 여기 한 줄만 추가하면 된다.
SOURCES = [
    ("1518460128968572958", "디코"),   # #assistant 디스코드
    ("1536635887780110509", "웹"),     # 웹 스튜디오 채팅
]
TRUNK   = os.path.expanduser("~/atnown-trunk")
OUT     = os.path.join(TRUNK, "_cowork_sync", "discord_assistant_live.md")
PSQL    = "/Applications/Creator OS.app/Contents/Resources/vendor/postgres/bin/psql"
LIMIT   = 100          # 표면당 최근 개수
KST     = timezone(timedelta(hours=9))

# Creator-OS 봇이 뿌리는 순간적 진행 표시(대화 맥락 아님) — 노이즈 제거
NOISE = ("⏳", "🕐", "🔧 도구 사용", "처리 중", "이어서 이 메시지도 답변")


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def fetch_messages(channel_id):
    """capture_events 에서 한 채널의 최근 LIMIT개를 반환 (정렬키 sort 포함)."""
    q = (
        "SELECT row_to_json(t) FROM ("
        "SELECT discord_message_id AS id, "
        "extract(epoch from created_at) AS sort, "
        "to_char(created_at,'YYYY-MM-DD\"T\"HH24:MI:SSOF') AS ts, "
        "coalesce(payload->'discord'->>'author_display_name', "
        "         payload->'discord'->>'author_username','?') AS author, "
        "coalesce(payload->'discord'->>'is_bot','false') AS is_bot, "
        "coalesce(payload->'discord'->>'content','') AS content "
        f"FROM creator_os_capture_events WHERE channel_id={channel_id} "
        f"ORDER BY created_at DESC LIMIT {LIMIT}) t"
    )
    r = subprocess.run(
        [PSQL, "-h", "127.0.0.1", "-p", "5434", "-U", "creator_os",
         "-d", "creator_os", "-t", "-A", "-c", q],
        capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        log(f"[ERR] psql 오류(rc={r.returncode}, ch={channel_id}): {r.stderr.strip()[:300]}")
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
    return rows


def fetch_all():
    """모든 표면을 뽑아 표면 라벨을 붙이고 시간순(오래된→최신)으로 병합."""
    if not os.path.exists(PSQL):
        log(f"[ERR] Creator OS psql 없음: {PSQL} — Creator OS 미설치/미기동")
        sys.exit(1)
    merged = []
    for ch, surface in SOURCES:
        for m in fetch_messages(ch):
            m["surface"] = surface
            merged.append(m)
    merged.sort(key=lambda m: m.get("sort") or 0.0)
    return merged


def normalize(m):
    """웹 표면의 사람 발화 되살리기. (author, content) 반환. None 이면 스킵."""
    author = m.get("author") or "?"
    content = (m.get("content") or "").strip()
    if not content:
        return None
    # 웹: 사람 발화는 author="Creator-OS" + 본문 앞 "🌐 " 접두로 저장됨
    if m.get("surface") == "웹" and content.startswith("🌐"):
        body = content[1:].lstrip()
        if body.startswith("[사용자 응답]"):
            author = "차노쌤(선택)"            # AskUserQuestion 선택 릴레이
        else:
            author = "차노쌤"                   # 웹 채팅에 직접 입력한 발화
        content = body
    # 노이즈: 짧은 순간표시만 스킵 (실제 발화 안에 이모지 들어간 건 유지)
    if any(n in content for n in NOISE) and len(content) < 120:
        return None
    return author, content


def to_kst(ts):
    try:
        dt = datetime.fromisoformat(ts)
        return dt.astimezone(KST).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return (ts or "")[:16].replace("T", " ")


def render(rows):
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S KST")
    out = [
        "# 웹·디스코드 #assistant 대화 (자동 동기화)",
        "",
        f"_마지막 갱신: {now} · 표면당 최근 {LIMIT}개 · 소스: Creator OS capture_events (SSOT)_",
        f"_표면: 디스코드 #assistant + 웹 스튜디오 채팅 — 시간순 병합, 각 발화 앞 `[디코]`/`[웹]` 표기_",
        "",
        "---",
        "",
    ]
    kept = 0
    for m in rows:
        nz = normalize(m)
        if not nz:
            continue
        author, content = nz
        when = to_kst(m.get("ts", ""))
        out.append(f"**[{m.get('surface','?')}] [{author}] ({when})**")
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
    rows = fetch_all()
    md = render(rows)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    prev = ""
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            prev = f.read()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(md)
    log(f"[OK] {OUT} 작성 ({len(rows)}행 병합)")

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
    git("commit", "-m", "sync: 웹·디스코드 #assistant 대화 자동 갱신")
    # 다른 방과 충돌 방지: pull --rebase 후 push (CLAUDE.md 방 자동동기화 규약)
    git("pull", "--rebase", "origin", branch, check=False)
    push = git("push", "origin", f"HEAD:{branch}", check=False)
    if push.returncode != 0:
        log(f"[ERR] git push 실패(rc={push.returncode}): {push.stderr.strip()[:400]}")
        sys.exit(1)
    log(f"[OK] push 성공 → origin/{branch}")


if __name__ == "__main__":
    main()
