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

⛔ **claim 락(진행중 commit+push) 폐지 — 2026-08-04 이찬호 지시.** 렌더러가 코덱스 하나뿐이라
레이스가 없다. 코덱스는 **파일 렌더만** 하고 git 은 아예 안 만진다(샌드박스가 `.git` 을 막으면
거기서 우회하지 말 것). 커밋·push 는 렌더가 끝난 뒤 **샌드박스 밖에서 클로드가 마지막에 한 번**.
(실증: 8/4 밤 claim 우회 시도로 코덱스 세션 하나를 태우고 렌더는 0편.)

사용:
    python3 scripts/render_trigger.py            # 대기건 목록만 (아무것도 실행 안 함)
    python3 scripts/render_trigger.py --dispatch # `status: 대기` 인 잡을 코덱스에게 인계
    python3 scripts/render_trigger.py --dispatch --only 2026-08-05   # 그 잡을 상태 무관 인계

⚠️ claim 락을 먼저 박는 운영(대기→진행중 후 호출)에서는 **반드시 `--only` 로 지정**해서 부른다.
   상태를 진행중으로 바꿔놓고 인자 없이 부르면 '대기'가 아니라서 자기가 잠근 잡을 못 찾는다.

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
    return f"""너는 앳나운 트렁크의 렌더 담당(코덱스)이다. 아래 렌더잡 하나를 **렌더(파일 생성)만** 해라.

렌더잡: {rel}

⛔ **git 은 아예 건드리지 마라 (2026-08-04 이찬호 지시).**
pull·commit·push·clone·claim 락 전부 금지다. 렌더러가 하나뿐이라 레이스가 없다.
샌드박스가 `.git` 을 막아도 **우회하지 마라** — GitHub 커넥터·API·새 클론 시도 전부 금지.
커밋은 렌더가 끝난 뒤 샌드박스 밖에서 클로드가 한 번에 한다. 너는 파일만 만들면 된다.
(실증: 8/4 밤 이 우회 시도로 세션 하나를 통째로 태우고 렌더는 0편이었다.)

절차:
1. 잡 파일의 대상 대본과 규격/지정(프리셋·B롤 위치·BGM)을 그대로 따른다.
   같은 폴더의 `_RENDER_OPTS.txt` 가 있으면 그것도 읽는다.
   잡의 지정과 리포 문서가 어긋나면 **잡 파일과 `knowledge/결정사항_대장.md` 가 우선**이다.
2. `python3 -m shorts.proof <대본폴더> --out <출력폴더> --only <NN> ...` 로 렌더한다.
   `verify_render` 전 항목 PASS 한 것만 시안으로 인정한다.
3. FAIL 이면 **억지로 통과시키지 마라.** 검사기를 고치거나 규격을 낮추는 건 금지.
   사유를 최종 보고에 적고 그 편은 중단한다.
4. 시안마다 컨택트시트 PNG(대표 프레임 6~9장, 자막 보이게)를 `<출력폴더>/contact/` 에 만든다.
5. PASS 시안은 구글드라이브 `앳나운_영상/_최신_바로보기/` 에 올린다(감독 프리뷰 위치).
   드라이브 인증이 막혀 있으면 **우회하지 말고** 로컬 경로만 보고해라.

절대 금지:
- **발행·예약공개 금지.** 유튜브/인스타/스레드 업로드나 publishAt 예약을 걸지 마라.
  감독 프리뷰 게이트가 유일한 발행 관문이다. 시안까지만 만들고 멈춘다.
- `secrets/` 내용을 출력하지 마라.
- 다른 날짜 폴더의 잡은 건드리지 마라. 이 잡 하나만.

끝나면 한국어로, 편별로 **①mp4 절대경로 ②길이 ③쓴 B롤 ④verify PASS/FAIL(FAIL이면 사유)
⑤컨택트시트 경로 ⑥드라이브 링크(있으면)** 만 적어라. 클로드가 이걸 그대로 잡 파일에 박는다."""


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

    if a.only:
        # 명시 지정은 상태 필터를 건너뛴다.
        # 규약상 착수 전에 status 를 '진행중'(claim 락)으로 바꾸고 부르기 때문에,
        # 여기서 '대기'만 찾으면 자기가 잠근 잡을 못 본다(2026-08-04 실증).
        j = SHORTS / a.only / "_RENDER_JOB.md"
        if not j.is_file():
            print(f"그런 렌더잡 없음: {j}")
            return 1
        body = j.read_text(encoding="utf-8", errors="replace")
        if "status: 완료" in body and PENDING_MARK not in body:
            print(f"⚠️ {a.only} 은 이미 완료 표시됨 — 그래도 지정했으므로 인계한다.")
        jobs = [j]
    else:
        jobs = pending_jobs()

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
