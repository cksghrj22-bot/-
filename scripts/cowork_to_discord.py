#!/usr/bin/env python3
# 반대 방향 브리지: 클라우드 코워크 방이 되돌린 답 → 디스코드 #assistant 로 발송(웹훅).
#
# 흐름(요약):
#   클라우드 방이 _cowork_sync/outbox/*.md 에 답을 떨군다(파일 1개 = 메시지 1개) → git push.
#   이 스크립트가 git pull → outbox 의 새 파일을 webhook 으로 #assistant 에 올림 →
#   처리한 파일을 outbox/_sent/ 로 옮기고 commit+push(다시 안 보내도록, 방도 처리됨을 앎).
#
# 웹훅 URL: secrets/discord_webhook.txt (gitignore) 한 줄. 없으면 안전하게 대기(에러 아님).
#   → #assistant 채널 웹훅을 Discord 서버설정 > 연동 > 웹훅에서 만들어 URL 한 줄만 저장하면 즉시 가동.
import json, os, subprocess, sys, time, urllib.request
from datetime import datetime, timezone, timedelta

TRUNK       = os.path.expanduser("~/atnown-trunk")
OUTBOX      = os.path.join(TRUNK, "_cowork_sync", "outbox")
SENT        = os.path.join(OUTBOX, "_sent")
WEBHOOK_TXT = os.path.join(TRUNK, "secrets", "discord_webhook.txt")
USERNAME    = "코워크(클라우드)"          # 디스코드에 표시될 이름
MAXLEN      = 1990                          # 웹훅 content 한도(2000) 안전 여유
KST         = timezone(timedelta(hours=9))


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def git(*args, check=True):
    r = subprocess.run(["git", "-C", TRUNK, *args],
                       capture_output=True, text=True,
                       env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    if check and r.returncode != 0:
        log(f"[ERR] git {' '.join(args)} 실패(rc={r.returncode}): {r.stderr.strip()[:300]}")
        sys.exit(1)
    return r


def read_webhook():
    if not os.path.exists(WEBHOOK_TXT):
        return None
    url = ""
    with open(WEBHOOK_TXT, encoding="utf-8") as f:
        url = f.read().strip()
    if not url.startswith("https://"):
        log(f"[WARN] 웹훅 URL 형식 이상: {url[:40]!r} — 무시")
        return None
    return url


def chunks(text, n=MAXLEN):
    """문단 경계를 존중하며 n자 이하로 쪼갠다."""
    text = text.strip()
    if len(text) <= n:
        return [text] if text else []
    out, buf = [], ""
    for para in text.split("\n"):
        if len(buf) + len(para) + 1 > n:
            if buf:
                out.append(buf)
            # 한 줄이 n을 넘으면 강제 슬라이스
            while len(para) > n:
                out.append(para[:n]); para = para[n:]
            buf = para
        else:
            buf = (buf + "\n" + para) if buf else para
    if buf:
        out.append(buf)
    return out


def post(url, content):
    body = json.dumps({"content": content[:2000], "username": USERNAME}).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json",
                 "User-Agent": "CoworkBridge/1.0 (+atnown)"},  # 디스코드는 UA 없으면 403
        method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status  # 204 = 성공


def new_files():
    if not os.path.isdir(OUTBOX):
        return []
    fs = []
    for name in os.listdir(OUTBOX):
        p = os.path.join(OUTBOX, name)
        if (os.path.isfile(p) and name.endswith(".md")
                and not name.startswith(".") and name != "README.md"):
            fs.append(p)
    fs.sort(key=lambda p: (os.path.getmtime(p), p))  # 오래된 순 발송
    return fs


def main():
    os.makedirs(OUTBOX, exist_ok=True)
    os.makedirs(SENT, exist_ok=True)

    # 방이 올린 새 답을 받기 위해 먼저 최신화(포워드 스크립트와 같은 rebase 규약)
    branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip() or "main"
    git("pull", "--rebase", "origin", branch, check=False)

    files = new_files()
    if not files:
        log("[SKIP] outbox 에 새 답 없음")
        return

    url = read_webhook()
    if not url:
        log(f"[WAIT] 웹훅 URL 미설정({WEBHOOK_TXT}) — 새 답 {len(files)}개 대기 중. "
            "URL 한 줄 저장하면 다음 주기에 자동 발송.")
        return

    sent_any = False
    for p in files:
        name = os.path.basename(p)
        with open(p, encoding="utf-8") as f:
            text = f.read()
        parts = chunks(text)
        if not parts:
            # 빈 파일도 처리 완료 취급(무한 대기 방지)
            os.replace(p, os.path.join(SENT, name)); sent_any = True
            log(f"[SKIP] 빈 파일 {name} → _sent 이동")
            continue
        ok = True
        for i, part in enumerate(parts):
            try:
                st = post(url, part)
                log(f"[OK] {name} [{i+1}/{len(parts)}] status={st}")
            except Exception as e:
                log(f"[ERR] {name} [{i+1}/{len(parts)}] 발송 실패: {e}")
                ok = False
                break
            time.sleep(0.6)  # 레이트리밋 여유
        if ok:
            os.replace(p, os.path.join(SENT, name)); sent_any = True

    if not sent_any:
        log("[WARN] 발송 성공 0 — 다음 주기 재시도")
        return

    # 처리 상태를 방과 공유(중복 발송 방지) — outbox 비움/_sent 채움을 push
    git("add", "-A", "_cowork_sync/outbox")
    st = git("status", "--porcelain", "_cowork_sync/outbox").stdout.strip()
    if not st:
        log("[OK] 발송 완료(로컬 이동만, git 변화 없음)")
        return
    stamp = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    git("commit", "-m", f"bridge: 코워크 답 디스코드 발송 처리 {stamp}")
    git("pull", "--rebase", "origin", branch, check=False)
    push = git("push", "origin", f"HEAD:{branch}", check=False)
    if push.returncode != 0:
        log(f"[ERR] git push 실패(rc={push.returncode}): {push.stderr.strip()[:400]}")
        sys.exit(1)
    log(f"[OK] 발송+처리상태 push 완료 → origin/{branch}")


if __name__ == "__main__":
    main()
