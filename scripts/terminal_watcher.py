#!/usr/bin/env python3
"""터미널 자동 처리 — inbox → Codex 호출 (야간 무음)"""
import json, time, os, subprocess
from pathlib import Path
from datetime import datetime

PIPELINE = Path.home() / "atnown-content-pipeline"
INBOX = PIPELINE / "_terminal_inbox"
DONE = INBOX / "_done"
WEBHOOKS_FILE = PIPELINE / "secrets/discord_webhooks.json"

# 야간 무음 시간 (00:00 ~ 08:00)
QUIET_START = 0
QUIET_END = 8

ROOM_MAP = {
    "낙타방": "인스타-낙타방",
    "designer": "designer",
    "writer": "writer",
    "brain": "brain",
    "assistant": "assistant",
    "studio": "studio",
    "developer": "developer",
}

# 방별 인수인계 파일 매핑 (채널 ID → 방 이름 → 인수인계)
TRUNK = PIPELINE  # trunk 합쳐짐

# 채널 ID로 강제 분리 (에이전트 섞임 방지)
CHANNEL_ID_MAP = {
    "1537004782970077214": "영상방",       # 쇼츠 전용
    "1537004853618933820": "인스타-낙타방", # 낙타 캐러셀 전용
    "1537004885315424328": "만화카드방",
    "1537006829220012124": "기획전략실",
    "1537005031356629052": "교육디렉팅방",
    "1537004754087968889": "블로그",
}

HANDOVER_MAP = {
    "영상방": PIPELINE / "knowledge/인수인계_쇼츠영상방_2026-08-12.md",
    "인스타-낙타방": PIPELINE / "knowledge/인수인계_낙타방_2026-08-12.md",
    "낙타방": PIPELINE / "knowledge/인수인계_낙타방_2026-08-12.md",
    "만화카드방": PIPELINE / "knowledge/인수인계_만화카드방_2026-08-12.md",
    "기획전략실": PIPELINE / "knowledge/인수인계_전략방_2026-08-12.md",
    "전략방": PIPELINE / "knowledge/인수인계_전략방_2026-08-12.md",
    "교육디렉팅방": PIPELINE / "knowledge/인수인계_교육디렉터실_2026-08-12.md",
    "블로그": PIPELINE / "knowledge/인수인계_D방_블로그_2026-08-12.md",
}

# 방별 규격 강제 (섞임 방지)
ROOM_RULES = {
    "영상방": "쇼츠 1080x1920, TTS 있음, build_c02.py 사용. 낙타 규격 절대 금지.",
    "인스타-낙타방": "캐러셀 1080x1350, TTS 없음, nakta_post.py 사용. 쇼츠 규격 절대 금지.",
    "낙타방": "캐러셀 1080x1350, TTS 없음, nakta_post.py 사용. 쇼츠 규격 절대 금지.",
    "만화카드방": "만화카드 규격. 이미지 생성은 나노바나나2(Gemini) 사용. 다른 방 규격 절대 금지.",
}

KNOWN_ROOMS = {"영상방", "인스타-낙타방", "만화카드방", "기획전략실", "교육디렉팅방", "블로그"}

def resolve_room(task: dict) -> str:
    """제목/내용 키워드로 방 자동 분류 (형님이 편한 방식)"""
    title = task.get("title", "").lower()
    request = task.get("request", "").lower()
    text = f"{title} {request}"
    
    # 에이전트 이름 → 방 이름 변환
    room_raw = task.get("room", "")
    if room_raw in AGENT_TO_ROOM:
        return AGENT_TO_ROOM[room_raw]

    # ★ 명시적 라우팅 우선 (2026-08-13 오분류 버그 수정)
    # 채널 ID가 명시돼 있으면 키워드보다 먼저 신뢰 — designer 테스트가
    # 텍스트 키워드('카드' 등)에 걸려 만화카드방으로 새는 것 방지
    channel_id = task.get("channel_id", "")
    if channel_id in CHANNEL_ID_MAP:
        return CHANNEL_ID_MAP[channel_id]

    # ★ 명시적 room이 이미 실제 방 이름이면 그대로 확정 (2026-08-13)
    # "구글드라이브"의 '글'이 블로그 키워드에 걸려 만화카드방 태스크가 블로그로 새는 사고 차단
    if room_raw in ROOM_MAP:
        return ROOM_MAP[room_raw]
    if room_raw in KNOWN_ROOMS:
        return room_raw

    # 키워드 기반 분류 (trunk/_ROOMS_5방.md 기준) — 명시적 라우팅 없을 때만
    if any(k in text for k in ["낙타", "캐러셀", "계단박스", "운동", "b롤", "인스타"]):
        return "인스타-낙타방"
    if any(k in text for k in ["쇼츠", "유튜브", "영상", "렌더", "대본", "스크립트"]):
        return "영상방"
    if any(k in text for k in ["만화", "결이", "캐릭터", "나노", "카드"]):
        return "만화카드방"
    if any(k in text for k in ["블로그", "네이버", "포스팅", "글쓰기", "블로그글"]):
        return "블로그"
    if any(k in text for k in ["교육", "시즈", "레벨", "승급", "커리큘럼", "디렉터"]):
        return "교육디렉팅방"
    if any(k in text for k in ["전략", "기획", "방향", "브랜딩"]):
        return "기획전략실"

    return task.get("room", "기획전략실")

def load_handover(room: str) -> str:
    """방별 인수인계 문서 로드"""
    # 직접 매핑
    if room in HANDOVER_MAP and HANDOVER_MAP[room].exists():
        return HANDOVER_MAP[room].read_text()[:8000]  # 8K 제한

    # 웹훅 키로 매핑
    key = get_webhook_key(room)
    if key in HANDOVER_MAP and HANDOVER_MAP[key].exists():
        return HANDOVER_MAP[key].read_text()[:8000]

    # 5방 체계 기본 로드
    rooms_5 = TRUNK / "_ROOMS_5방.md"
    if rooms_5.exists():
        return rooms_5.read_text()[:4000]

    return ""

def is_quiet_time():
    """야간 무음 시간인지 확인"""
    hour = datetime.now().hour
    return QUIET_START <= hour < QUIET_END

def load_webhooks():
    if WEBHOOKS_FILE.exists():
        return json.loads(WEBHOOKS_FILE.read_text())
    return {}

def get_webhook_key(room):
    if room in ROOM_MAP:
        return ROOM_MAP[room]
    webhooks = load_webhooks()
    if room in webhooks:
        return room
    if "channel" in room:
        for agent in ["designer", "writer", "brain", "assistant", "studio", "developer"]:
            if agent in room:
                return agent
    return "기획전략실"

def send_discord(room, msg):
    # 야간엔 웹훅 안 보냄 (작업은 함)
    if is_quiet_time():
        print(f"🌙 야간 무음 ({QUIET_START}시-{QUIET_END}시) - 웹훅 생략")
        return
    
    import urllib.request
    webhooks = load_webhooks()
    key = get_webhook_key(room)
    webhook = webhooks.get(key) or webhooks.get("기획전략실")
    if not webhook: return
    data = json.dumps({"content": msg[:2000], "username": "터미널"}).encode()
    req = urllib.request.Request(webhook, data=data, headers={
        "Content-Type": "application/json",
        "User-Agent": "atnown-terminal/1.0 (Mozilla/5.0)",  # Discord/Cloudflare 403 차단 회피 (필수)
    })
    try:
        urllib.request.urlopen(req, timeout=10)  # timeout 필수 — 없으면 소켓 행 시 단일트렁크 큐 전체 멈춤 (2026-08-13)
        print(f"✅ 웹훅: {key}")
    except Exception as e: 
        print(f"❌ 웹훅 실패: {e}")

CODEX_PATH = "/opt/homebrew/bin/codex"

def resolve_codex() -> str:
    """codex CLI 경로 자가치유 — 루프마다 재탐색 (codex_watch.sh 이식).
    시작 시 1회 캐싱하면 설치 전 기동 시 영구 '미설치'로 굳음 → 매번 재탐색."""
    import shutil
    cand = shutil.which("codex")
    if cand:
        return cand
    for p in (
        "/opt/homebrew/bin/codex",
        "/usr/local/bin/codex",
        str(Path.home() / ".npm-global/bin/codex"),
        str(Path.home() / ".codex/bin/codex"),
        str(Path.home() / ".local/bin/codex"),
    ):
        if Path(p).exists():
            return p
    return CODEX_PATH  # 최후 폴백

# 구글드라이브 저장소 (Creator OS 대신 메인)
DRIVE_FOLDER_ID = "1zcbcM9iTX1LFmZKY5sBwUEAos7e9-nLe"  # 앳나운_영상
DRIVE_LATEST_FOLDER = "_최신_바로보기"

def upload_to_drive(file_path: str) -> str:
    """드라이브에 업로드하고 링크 반환"""
    try:
        from shorts.gdrive import upload_file, access_token, load_secrets, find_in_folder

        secrets = load_secrets()
        token = access_token(secrets)

        # _최신_바로보기 폴더 찾기
        latest_folder = find_in_folder(DRIVE_LATEST_FOLDER, DRIVE_FOLDER_ID, token)
        target_folder = latest_folder or DRIVE_FOLDER_ID

        # 업로드
        result = upload_file(file_path, folder_id=target_folder)
        file_id = result.get("id", "")

        if file_id:
            link = f"https://drive.google.com/file/d/{file_id}/view"
            print(f"📤 드라이브 업로드: {link}")
            return link
        return ""
    except Exception as e:
        print(f"❌ 드라이브 업로드 실패: {e}")
        return ""

def call_codex(prompt: str, cwd: str = None, timeout: int = 900) -> str:
    """Codex CLI 호출 (codex_watch.sh 안정성 이식: 경로 자가치유 + 작업별 타임아웃)"""
    codex = resolve_codex()
    if not Path(codex).exists():
        return "[오류] codex CLI 미설치 — 설치 필요"
    print(f"🤖 Codex 호출({Path(codex).name}, tmo={timeout}s): {prompt[:50]}...")
    try:
        result = subprocess.run(
            [
                codex,
                "exec",
                "--dangerously-bypass-approvals-and-sandbox",
                "--skip-git-repo-check",
                "-C",
                str(Path.home()),
                prompt,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,  # stdin 대기로 멈춤 방지
            cwd=cwd or str(PIPELINE)
        )
        output = result.stdout + result.stderr
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('assistant') or 'completed' in line.lower():
                return '\n'.join(lines[i:]).strip()
        return output.strip() or "[완료]"
    except subprocess.TimeoutExpired:
        return f"[타임아웃 {timeout}초]"
    except Exception as e:
        return f"[오류] {e}"

def process_task(task_file):
    """작업 처리 → 키워드로 방 분류 → 인수인계 로드 → Codex 호출"""
    task = json.loads(task_file.read_text())
    room = resolve_room(task)  # 키워드 기반 자동 분류

    mode = task.get("mode", "")
    title = task.get("title", "")
    request = task.get("request", title)
    clips = task.get("clips", [])

    print(f"🔧 처리: {task_file.name}")
    send_discord(room, f"⏳ 작업 시작: {title or request[:50]}")

    # 🧠 인수인계 + 규격 강제 로드 (본진이 생각하는 부분)
    handover = load_handover(room)
    rule = ROOM_RULES.get(room, "")

    context_header = ""
    if handover or rule:
        context_header = f"""## 🔴 이 방: {room}
{f"**강제 규격:** {rule}" if rule else ""}

## 인수인계 (반드시 따를 것)
{handover[:6000] if handover else "(인수인계 없음)"}

---

## 요청
"""
        print(f"📋 방 분류: {room} / 인수인계: {len(handover) if handover else 0}자")

    if mode == "clip_subtitle_sync" and clips:
        subtitles = [c.get("subtitles", [""])[0] for c in clips]
        prompt = f"""{context_header}낙타식 자막 콘텐츠 렌더:
- 소스: {task.get('broll_source_dir', '운동 폴더')}
- 캔버스: {task.get('canvas', '1080x1350')}
- 클립당: {task.get('clip_seconds', '3-5초')}
- 자막: {subtitles}

인수인계 규격대로 렌더하고 드라이브 _최신_바로보기에 업로드."""
    else:
        prompt = f"{context_header}{request or title}"
    
    result = call_codex(prompt, timeout=int(task.get("timeout", 900)))

    # 🔴 산출물 검증 — 가짜 done 방지 (2026-08-14 버그 수정)
    import re

    # Codex 에러 체크
    is_error = result.startswith("[오류]") or result.startswith("[타임아웃")

    # 결과에서 파일 경로 찾기
    file_patterns = re.findall(r'/Users/chanho/[^\s\]\)]+\.(mp4|png|jpg|jpeg|mov|pdf|json|csv)', result)
    existing_files = [f for f in file_patterns if Path(f).exists()]

    # 📤 결과물 드라이브 업로드 + 링크 추출
    drive_links = []
    for fpath in existing_files[:3]:  # 최대 3개
        link = upload_to_drive(fpath)
        if link:
            drive_links.append(f"📎 {Path(fpath).name}: {link}")

    # 🔴 상태 판정 — 에러거나 산출물 없으면 failed
    if is_error:
        task["status"] = "failed"
        task["failure_reason"] = "codex_error"
    elif not existing_files and "expected_output" in task:
        # 기대 산출물이 명시됐는데 없으면 failed
        task["status"] = "failed"
        task["failure_reason"] = "no_output"
    else:
        task["status"] = "done"

    task["completed_at"] = datetime.now().isoformat()
    task["codex_result"] = result[:2000]  # 500→2000 (블로그방 요청 08-15)
    task["verified_files"] = existing_files[:5]  # 실제 존재 확인된 파일

    task["drive_links"] = drive_links

    DONE.mkdir(exist_ok=True)
    done_file = DONE / task_file.name
    done_file.write_text(json.dumps(task, ensure_ascii=False, indent=2))
    task_file.unlink()

    # 디스코드 알림 (드라이브 링크 포함)
    links_text = "\n".join(drive_links) if drive_links else ""
    msg = f"✅ 완료: {title or request[:50]}\n{links_text}\n```\n{result[:1200]}\n```"
    send_discord(room, msg)
    return result

def check_inbox():
    for f in INBOX.glob("TASK_*.json"):
        try:
            task = json.loads(f.read_text())
            status = task.get("status", "pending")
            if status in ["pending", "processing"]:
                return f
        except:
            continue
    return None

def run_loop():
    print("🚀 터미널 watcher 시작 (야간 00-08시 무음)")
    while True:
        task_file = check_inbox()
        if task_file:
            try:
                process_task(task_file)
            except Exception as e:
                print(f"❌ 처리 실패: {e}")
        time.sleep(2)  # 명령 픽업 1~3초 (2026-08-13 이찬호 지시)

# 에이전트 이름 → 방 이름 매핑
AGENT_TO_ROOM = {
    "designer": "만화카드방",
    "writer": "블로그",
    "brain": "기획전략실",
    "assistant": "교육디렉팅방",
    "studio": "영상방",
    "developer": "영상방",
}

if __name__ == "__main__":
    import sys
    if "--daemon" in sys.argv:
        run_loop()
    elif "--once" in sys.argv:
        task_file = check_inbox()
        if task_file:
            process_task(task_file)
        else:
            print("대기 작업 없음")
    else:
        count = 0
        while True:
            task_file = check_inbox()
            if not task_file:
                break
            process_task(task_file)
            count += 1
        print(f"총 {count}개 처리")
