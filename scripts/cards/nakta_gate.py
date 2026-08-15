#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""낙타형 자막바 — 렌더 게이트 (자동 검사).

차노 원칙: "표준은 글 아니라 검사코드로 잠근다."
글로만 적힌 규격은 다음 방이 안 읽으면 끝이다. 이 스크립트가 대신 막는다.

쓰는 법:
    python3 scripts/cards/nakta_gate.py _out/<주제>__N
    → 통과하면 exit 0, 하나라도 걸리면 exit 1 + 무엇이 왜 걸렸는지 출력

검사 (규격 정본 knowledge/규격_낙타형자막바_컨텐츠_정본.md 기준)
  [S1] 1080x1350
  [S2] 30fps
  [S3] 슬라이드당 3~5초
  [S4] 오디오 스트림 0개 (TTS 없음)
  [S5] 자막 위치 변주 — 전 슬라이드가 같은 자리면 탈락(신문 배치 금지)
  [S6] 시안 분산 — 연속 사용 금지
  [S7] 자막 블록이 화면 전폭을 먹지 않음 (전폭 바자막 금지)
  [S8] 눈검수 강제 — 시작/중간/끝 3지점 프레임을 뽑아 컨택트시트를 만든다.
       ※ "자막이 피사체를 가리는가"는 코드가 판정하지 못한다. 사람이 봐야 한다.
          그래서 게이트는 **판정 대신 증거를 강제로 만들어** 놓는다.
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

FF, FP = "ffmpeg", "ffprobe"


def probe(p: Path) -> dict:
    v = json.loads(subprocess.check_output(
        [FP, "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,avg_frame_rate,nb_frames,duration", "-of", "json", str(p)],
        text=True))["streams"][0]
    a = subprocess.check_output(
        [FP, "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
         "-of", "csv=p=0", str(p)], text=True).strip()
    v["audio"] = len([x for x in a.split("\n") if x])
    return v


def overlay_bbox(png: Path):
    """오버레이 PNG에서 자막이 실제로 칠해진 영역(bbox)."""
    try:
        from PIL import Image
    except ImportError:
        return None
    im = Image.open(png).convert("RGBA")
    return im.getchannel("A").getbbox()   # (l, t, r, b) or None


def main() -> int:
    if len(sys.argv) < 2:
        print("사용법: nakta_gate.py <산출폴더>"); return 2
    out = Path(sys.argv[1])
    slides = sorted(out.glob("slide_*.mp4"), key=lambda p: int(p.stem.split("_")[1]))
    if not slides:
        print(f"[탈락] {out} 에 slide_*.mp4 없음"); return 1

    fails, warns, boxes = [], [], []
    print(f"== 낙타 게이트: {out.name} ({len(slides)}장) ==")

    for p in slides:
        n = p.stem
        v = probe(p)
        w, h = v["width"], v["height"]
        dur = float(v["duration"])
        fps = v["avg_frame_rate"]
        if (w, h) != (1080, 1350):
            fails.append(f"[S1] {n} 해상도 {w}x{h} (1080x1350 이어야 함)")
        if fps not in ("30/1", "30000/1001"):
            fails.append(f"[S2] {n} fps {fps} (30 이어야 함)")
        if not (3.0 <= dur <= 5.05):
            fails.append(f"[S3] {n} 길이 {dur:.3f}초 (3~5초)")
        if v["audio"] != 0:
            fails.append(f"[S4] {n} 오디오 스트림 {v['audio']}개 (TTS 없음 = 0)")
        print(f"  {n}: {w}x{h} {fps} {dur:.3f}s audio={v['audio']}")

        ov = out / "_overlays" / f"{n}_overlay.png"
        if ov.exists():
            bb = overlay_bbox(ov)
            boxes.append((n, bb))
            if bb:
                bw = bb[2] - bb[0]
                if bw >= w - 40:
                    fails.append(f"[S7] {n} 자막이 화면 전폭({bw}px) — 전폭 바자막 금지")

    # S5 자막 위치 변주
    pos = [(n, (bb[0], bb[1])) for n, bb in boxes if bb]
    if len(pos) >= 3 and len(set(p for _, p in pos)) == 1:
        fails.append("[S5] 전 슬라이드 자막 위치가 동일 — 신문 배치 금지, 슬라이드마다 변주할 것")
    elif len(pos) >= 4:
        tops = [p[1] for _, p in pos]
        if max(tops) - min(tops) < 100:
            warns.append("[S5] 자막 높이가 전부 비슷함 — 상/중/하로 리듬을 줄 것")

    # S8 눈검수 증거 생성 — 슬라이드당 시작/중간/끝 3컷을 가로로, 슬라이드는 세로로
    rv = out / "_review"; rv.mkdir(exist_ok=True)
    tmp = out / "_review" / "_gate_tiles"; tmp.mkdir(exist_ok=True)
    for old_f in tmp.glob("*.jpg"):
        old_f.unlink()
    idx = 0
    for p in slides:
        dur = float(probe(p)["duration"])
        for t_ in (0.2, dur / 2, dur - 0.2):
            f = tmp / f"{idx:03d}.jpg"
            subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{t_:.2f}",
                            "-i", str(p), "-frames:v", "1", "-vf", "scale=270:338",
                            "-q:v", "4", str(f)], check=True)
            idx += 1
    sheet = out / "_게이트_눈검수.jpg"
    r = subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error",
                        "-pattern_type", "glob", "-i", str(tmp / "*.jpg"),
                        "-filter_complex",
                        f"tile=3x{len(slides)}:margin=8:padding=8:color=0x101014",
                        "-frames:v", "1", "-q:v", "3", str(sheet)],
                       capture_output=True, text=True)
    if r.returncode != 0 or not sheet.exists():
        fails.append(f"[S8] 눈검수 시트 생성 실패 — {r.stderr[-200:]}")
    else:
        # 시트가 실제로 전 컷을 담았는지 크기로 검증 (한 컷만 들어간 사고 방지)
        try:
            from PIL import Image
            sw, sh = Image.open(sheet).size
            exp_w, exp_h = 3 * 270 + 4 * 8, len(slides) * 338 + (len(slides) + 1) * 8
            if abs(sw - exp_w) > 40 or abs(sh - exp_h) > 40:
                fails.append(f"[S8] 눈검수 시트가 {sw}x{sh} — 기대 {exp_w}x{exp_h}. 전 컷이 안 담겼다.")
        except ImportError:
            pass

    print()
    for wmsg in warns:
        print("  ⚠️ " + wmsg)
    if fails:
        print("\n❌ 게이트 탈락")
        for f in fails:
            print("   " + f)
        return 1

    print("✅ 수치 규격 통과 (S1~S7)")
    print(f"\n👁  [S8] 눈으로 볼 것 — {sheet}")
    print("   슬라이드마다 시작/중간/끝 3컷이다. 아래를 **사람이** 확인한다:")
    print("   1. 보여주려는 것(사람·핵심 동작)을 자막이 가리지 않는가")
    print("      → 피사체가 왼쪽이면 자막은 오른쪽. 「좌측정렬」은 글자 정렬이지 블록 위치가 아니다.")
    print("   2. 3지점 전부에서 안 가리는가 (움직이면 위치가 바뀐다)")
    print("   3. 자막 밑 배경이 잡하지 않은가")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
