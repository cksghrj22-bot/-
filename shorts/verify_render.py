"""쇼츠 mind 렌더 전수 검사 — 규격 7항목을 한 번에. 하나라도 어긋나면 FAIL.

- 함수로 쓰기: `from shorts.verify_render import verify; fails = verify(mp4, ass)`
  → fails 는 실패 사유 문자열 리스트(비어 있으면 통과). 렌더 파이프가 import 해서 자동 게이트로 쓴다.
- CLI 로 쓰기: `python3 -m shorts.verify_render <mp4> <ass>` → PASS/FAIL 출력, FAIL 이면 exit 1.

⚠️ 이 검사기는 '규격의 정본'을 그대로 반영해야 한다. 규격이 바뀌면 여기도 같이 바꾼다
   (config·검사기·knowledge/제작규격_정본.md 3곳이 항상 일치). 검사기가 틀린 값을 정답으로
   들고 있으면 'PASS'가 오히려 사고를 은폐한다 — 2026-07-16 나눔/교보 실증."""

from __future__ import annotations

import re
import subprocess
import sys


def _ff(args: list[str]) -> str:
    r = subprocess.run(["ffmpeg", "-hide_banner", *args], capture_output=True, text=True)
    return r.stderr + r.stdout


LEN_MIN, LEN_MAX = 30.0, 46.0  # 길이 규격: 30초 초과 ~ 45초 미만(+톨러런스1s). "일부러 늘리지 마"(이찬호 2026-07-21).


def length_fails(dur: float) -> list[str]:
    """길이 규격(30초 초과~45초 미만) 검사 — ffmpeg 없이 순수 계산이라 단위테스트로 잠근다."""
    if dur < LEN_MIN:
        return [f"길이 {dur:.0f}초 — 30초 밑. 대본 조금 더."]
    if dur > LEN_MAX:
        return [f"길이 {dur:.0f}초 — 45초 초과. 대본 줄일 것"]
    return []


def verify(mp4: str, ass: str, duration: float | None = None) -> list[str]:
    """규격 검사. 실패 사유 리스트를 돌려준다(빈 리스트 = 통과)."""
    fails: list[str] = []
    info = subprocess.run(["ffmpeg", "-hide_banner", "-i", mp4], capture_output=True, text=True).stderr

    # 1) 해상도 1080x1920
    if "1080x1920" not in info:
        m = re.search(r"(\d{3,4}x\d{3,4})", info)
        fails.append(f"해상도 {m.group(1) if m else '?'} (1080x1920 아님)")
    dm = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", info)
    dur = int(dm[1]) * 3600 + int(dm[2]) * 60 + float(dm[3]) if dm else 0
    if duration:  # 렌더가 아는 정확한 길이를 넘겨주면 우선 사용
        dur = duration

    # 1b) 길이 40~50초 (이찬호 2026-07-21): 25초처럼 짧거나 50 넘으면 FAIL.
    fails += length_fails(dur)

    # 2) 흑백: 25% 지점 중앙 500x500 채도(SATAVG) 낮아야. ffmpeg 읽기 플레이크 방어로 빈값이면 1회 재시도.
    t = dur * 0.25
    satv = None
    for _ in range(2):
        sat = _ff(["-ss", f"{t:.1f}", "-i", mp4, "-vframes", "1",
                   "-vf", "crop=500:500:(iw-500)/2:(ih-500)/2,signalstats,"
                          "metadata=print:key=lavfi.signalstats.SATAVG", "-f", "null", "-"])
        sm = re.search(r"SATAVG=([\d.]+)", sat)
        if sm:
            satv = float(sm[1])
            break
    if satv is None:
        satv = 999
    if satv > 18:
        fails.append(f"흑백 아님 (중앙 채도 SATAVG={satv:.1f} > 18)")

    # 3) BGM: 아웃트로(나레이션 뒤 순수 BGM 구간)가 '들리게' 깔려야 한다.
    #    무음(-inf)뿐 아니라 너무 작아도(≈안 들림) FAIL. 정상편 아웃트로 ≈ -34dB, 안 들리던 06 = -52dB.
    #    → 들리는 바 -45dB. 끝 페이드아웃(약1.6s) 때문에 맨 끝은 조용해지므로, 페이드 앞
    #    순수 BGM 창 [dur-3.3, dur-1.8]에서 측정한다. 빈값이면 1회 재시도(플레이크 방어).
    AUDIBLE_DB = -45.0
    rms: list[str] = []
    for _ in range(2):
        tail = _ff(["-ss", f"{max(0, dur - 3.3):.1f}", "-t", "1.5", "-i", mp4,
                    "-af", "astats=metadata=1:reset=0", "-f", "null", "-"])
        rms = [x for x in re.findall(r"RMS level dB:\s*(-?[\d.]+|-inf)", tail) if x != "-inf"]
        if rms:
            break
    if not rms:
        fails.append("BGM 없음 (아웃트로 완전 무음) — BGM 무조건 깔 것")
    else:
        worst = min(float(x) for x in rms)
        if worst < AUDIBLE_DB:
            fails.append(f"BGM 너무 작아 안 들림 (아웃트로 RMS {worst:.0f}dB < 들리는 기준 {AUDIBLE_DB:.0f}dB)")

    # ASS 기반 검사
    a = open(ass, encoding="utf-8").read()
    styles = {ln.split(",")[0].replace("Style: ", ""): ln
              for ln in a.splitlines() if ln.startswith("Style:")}
    dialog = [ln for ln in a.splitlines() if ln.startswith("Dialogue:")]

    # 4a) ASS 폰트명 KyoboHandwriting2019(공백 없음) — 공백판은 libass가 DejaVu로 폴백.
    for nm in ("Default", "Title"):
        if nm in styles and "KyoboHandwriting2019" not in styles[nm].replace(" ", ""):
            f = styles[nm].split(",")[1]
            fails.append(f"{nm} 폰트 {f} (KyoboHandwriting2019 아님)")
    # 4b) 실렌더 폰트 — ass 재렌더해 libass fontselect 로그로 실제 폰트 확인.
    #     ASS 텍스트만 맞아도 픽셀은 폴백폰트일 수 있어 반드시 실렌더로 검증.
    fs = _ff(["-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=1",
              "-vf", f"ass={ass}", "-frames:v", "1", "-f", "null", "-"])
    picked = [p.split("/")[-1] for p in re.findall(r"fontselect:.*?->\s*(\S+)", fs)]
    if picked and not any("Kyobo" in p for p in picked):
        fails.append(f"실렌더 폰트 폴백! libass가 교보를 못 골랐음 → {set(picked)} (ASS 폰트명 공백 확인)")
    cjk = [p for p in picked if any(x in p.lower()
           for x in ("wenquanyi", "wqy", "noto", "droid", "cjk", "song"))]
    if cjk:
        fails.append(f"한글이 CJK 폰트로 폴백! {set(cjk)} (교보 글리프 누락/폰트명 오류)")

    # 5) 자막 블랙박스: Default BorderStyle=4
    if "Default" in styles and styles["Default"].split(",")[7].strip() != "4":
        fails.append("자막 블랙박스 아님 (BorderStyle≠4)")

    # 6) 아웃트로 중앙(alignment 5) + 잘림 없음
    outro = [d for d in dialog if ",Outro," in d]
    if not outro:
        fails.append("아웃트로 없음")
    else:
        al = styles.get("Outro", "").split(",")
        if len(al) >= 11 and al[10].strip() != "5":
            fails.append(f"아웃트로 위치 alignment={al[10].strip()} (중앙5 아님)")
        em = re.search(r",(\d+):(\d+):([\d.]+),Outro", outro[-1])
        oend = int(em[1]) * 3600 + int(em[2]) * 60 + float(em[3]) if em else 999
        if oend > dur + 0.05:
            fails.append(f"아웃트로 잘림 (끝 {oend:.1f}s > 영상 {dur:.1f}s)")

    # 7) 화면 CTA 없음
    for w in ("저장", "좋아요", "구독", "팔로우"):
        if w in a:
            fails.append(f"CTA '{w}' 발견")

    return fails


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) < 2:
        print("사용: python3 -m shorts.verify_render <mp4> <ass>")
        return 2
    mp4, ass = argv[0], argv[1]
    fails = verify(mp4, ass)
    name = mp4.split("/")[-1][:24]
    print(f"{'❌ FAIL' if fails else '✅ PASS'} {name}")
    for f in fails:
        print("   -", f)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
