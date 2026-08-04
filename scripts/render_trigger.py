#!/usr/bin/env python3
"""렌더 트리거 — 클로드(밤샘)가 대기건을 찾아 코덱스에게 렌더를 인계한다.

역할분담(knowledge/코덱스_클로드_역할분담.md) 실행체:
  새로 '생각'(기획·대본·판단) = 클로드 / 이미 정해진 '실행'(렌더·TTS·업로드) = 코덱스.
클로드가 직접 ffmpeg를 돌리면 분담 위반이고 방 충돌이 난다(2026-08-04 중복렌더 실증).
→ 클로드는 **트리거만** 당기고, 렌더는 코덱스가 이어받는다.

대기 판정 = `pipeline/렌더_레이스_방지.md` 규약의 상태 표기를 그대로 쓴다.
`_RENDER_JOB.md` 안에 `status: 대기` 가 있으면 대기, `진행중`/`완료`면 skip.
(한 파일에 잡이 여러 번 append 되므로 파일 단위 '완료 마커'는 쓰지 않는다 —
 새 잡이 밑에 붙었는데 위쪽 완료 마커 때문에 건너뛰는 사고가 난다. 2026-08-04 실증.)

점유(claim) 락은 코덱스가 잡는다: 착수 시 status→진행중 commit+push, 완료 시 status→완료.
트리거는 락을 대신 잡지 않는다(잡았다가 렌더가 안 붙으면 영영 진행중으로 남는다).

사용:
    python3 scripts/render_trigger.py            # 대기건 목록만 (아무것도 실행 안 함)
    python3 scripts/render_trigger.py --dispatch # 대기건을 코덱스에게 인계
    python3 scripts/render_trigger.py --dispatch --only 2026-08-05

발행·예약은 어떤 경우에도 자동 금지 — 코덱스에게 주는 프롬프트에도 명시한다(감독 프리뷰 게이트).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SHORTS = REPO / "content" / "shorts"
PENDING_MARK = "status: 대기"  # pipeline/렌더_레이스_방지.md 규약

# 코덱스 CLI는 ChatGPT 앱 번들 안에 있다 (PATH에 없음 — 2026-08-04 확인).
CODEX = os.environ.get(
    "CODEX_BIN", "/Applications/ChatGPT.app/Contents/Resources/codex"
)
# 코덱스 전용 작업 클론 (홈·비동기화. iCloud 폴더면 .git이 placeholder로 방출돼 느려진다)
CODEX_CWD = os.environ.get("CODEX_CWD", str(Path.home() / "atnown-repo"))


def pending_jobs() -> list[Path]:
    """`status: 대기` 가 남아 있는 _RENDER_JOB.md 를 날짜순으로."""
    if not SHORTS.is_dir():
        return []
    jobs = []
    for job in sorted(SHORTS.glob("*/_RENDER_JOB.md")):
        if PENDING_MARK in job.read_text(encoding="utf-8", errors="replace"):
            jobs.append(job)
    return jobs


def build_prompt(job: Path) -> str:
    rel = job.relative_to(REPO)
    return f"""너는 앳나운 트렁크의 렌더 담당(코덱스)이다. 아래 렌더잡 하나를 끝까지 처리해라.

렌더잡: {rel}

규약: `pipeline/렌더_레이스_방지.md` (단일 렌더러 = 너, claim 락 필수). 반드시 먼저 읽어라.

절차:
1. `git pull --rebase origin main` 으로 최신을 먼저 당긴다. 대상 잡의 status 가
   **`진행중`이거나 `완료`면 다른 방이 잡은 것이니 아무것도 하지 말고 종료**한다.
1b. 착수하기로 했으면 **먼저 status 를 `진행중(codex·<UTC시각>)` 으로 바꿔 commit+push** 한다(claim 락).
   이걸 안 하면 다른 에이전트가 같은 잡을 또 렌더한다(2026-08-04 사고).
2. 잡 파일의 대상 대본과 규격/지정(프리셋·B롤 위치·BGM)을 그대로 따른다.
   같은 폴더의 `_RENDER_OPTS.txt` 가 있으면 그것도 읽는다.
   잡의 지정과 리포 문서가 어긋나면 **잡 파일과 `knowledge/결정사항_대장.md` 가 우선**이다.
3. `python3 -m shorts.proof <대본폴더> --out <출력폴더> --only <NN> ...` 로 렌더한다.
   `verify_render` 전 항목 PASS 한 것만 시안으로 인정한다.
4. FAIL 이면 **억지로 통과시키지 마라.** 검사기를 고치거나 규격을 낮추는 건 금지.
   사유를 잡 파일에 기록하고 그 편은 중단한다.
5. PASS 시안은 구글드라이브 `앳나운_영상/_최신_바로보기/` 에 올린다(감독 프리뷰 위치).
6. 결과(파일명·길이·B롤·verify 로그)를 잡 파일 끝에 append 하고,
   **그 잡의 status 를 `완료` 로 바꾼다.** `status: 대기` 문자열이 남아 있으면
   트리거가 계속 대기건으로 보고 또 부른다.
7. `git pull --rebase origin main && git push origin HEAD:main` 으로 올린다.

절대 금지:
- **발행·예약공개 금지.** 유튜브/인스타/스레드 업로드나 publishAt 예약을 걸지 마라.
  감독 프리뷰 게이트가 유일한 발행 관문이다. 시안까지만 만들고 멈춘다.
- `secrets/` 내용을 출력하거나 커밋하지 마라.
- 다른 날짜 폴더의 잡은 건드리지 마라. 이 잡 하나만.

끝나면 한국어로 3줄 이내 요약(편수·PASS/FAIL·드라이브 위치)만 남겨라."""


def dispatch(job: Path, dry: bool = False) -> int:
    prompt = build_prompt(job)
    log_dir = REPO / "_render_trigger_logs"
    log_dir.mkdir(exist_ok=True)
    last_msg = log_dir / f"{job.parent.name}.last.txt"

    cmd = [
        CODEX, "exec",
        "-C", CODEX_CWD,
        "-s", "workspace-write",
        # 렌더는 TTS(일레븐랩스)·드라이브 접근이 필요해서 네트워크를 열어준다.
        "-c", "sandbox_workspace_write.network_access=true",
        "-o", str(last_msg),
        prompt,
    ]
    if dry:
        print("[dry-run] " + " ".join(cmd[:-1]) + " <프롬프트>")
        return 0
    if not Path(CODEX).exists():
        print(f"❌ 코덱스 CLI 없음: {CODEX} (ChatGPT 앱 설치/경로 확인)", file=sys.stderr)
        return 2
    print(f"▶ 코덱스에게 인계: {job.relative_to(REPO)}")
    r = subprocess.run(cmd)
    if last_msg.exists():
        print(f"--- 코덱스 최종 보고 ({last_msg}) ---")
        print(last_msg.read_text(encoding="utf-8", errors="replace").strip())
    return r.returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dispatch", action="store_true", help="대기건을 코덱스에게 인계 (없으면 목록만)")
    ap.add_argument("--only", help="이 폴더명(날짜)만")
    ap.add_argument("--dry-run", action="store_true", help="실행할 명령만 보여준다")
    a = ap.parse_args()

    jobs = pending_jobs()
    if a.only:
        jobs = [j for j in jobs if j.parent.name == a.only]

    if not jobs:
        print("대기 중인 렌더잡 없음.")
        return 0

    print(f"대기 렌더잡 {len(jobs)}건:")
    for j in jobs:
        print(f"  - {j.relative_to(REPO)}")

    if not (a.dispatch or a.dry_run):
        print("\n(인계하려면 --dispatch)")
        return 0

    rc = 0
    for j in jobs:
        rc |= dispatch(j, dry=a.dry_run)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
