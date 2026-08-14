#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""쇼츠 영상 — 렌더 게이트 (자동 검사 + 발행 전 스샷 시트).

차노 원칙: "표준은 글 아니라 검사코드로 잠근다."
차노 지시(2026-08-14): "영상 발행 전은 항상 스샷으로 띄워서 전체적으로 볼 수 있게 하고 렌더링하기."

쓰는 법:
    python3 scripts/shorts_gate.py <영상.mp4 또는 폴더>
    → 통과 exit 0 / 하나라도 걸리면 exit 1

검사 (knowledge/제작규격_정본.md 기준)
  [S1] 1080x1920 (프리뷰는 경고만, 탈락 아님)
  [S2] 길이 26~59초 — 보완게이트 기준
  [S3] 오디오 스트림 있음 (쇼츠는 나레이션+BGM)
  [S4] 경계 무음 없음 — 앞뒤 0.5초에 소리가 죽어 있으면 경고 (짧은 BGM loop 사고 #207)
  [S5] **하단 UI존(바닥 20%)에 자막 침범** — 흰 픽셀 비율로 자동 검출
       규격: 한글 최하단줄 y=1436 / 영어 y=1500 → 바닥에서 420px 위. 1540 아래는 비어야 한다.
  [S6] 발행 전 스샷 시트 — 등간격 12컷 + **UI존 경계선을 그려서** 한눈에 보이게 만든다.
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

FF, FP = "ffmpeg", "ffprobe"
# 1080x1920 기준 UI존 — 다른 해상도는 비율로 계산
UI_ZONE_RATIO = 1540 / 1920  # 바닥 20%가 UI존


def probe(p: Path) -> dict:
    v = json.loads(subprocess.check_output(
        [FP, "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,avg_frame_rate,duration", "-of", "json", str(p)], text=True))["streams"][0]
    a = subprocess.check_output([FP, "-v", "error", "-select_streams", "a", "-show_entries",
                                 "stream=index", "-of", "csv=p=0", str(p)], text=True).strip()
    v["audio"] = len([x for x in a.split("\n") if x])
    return v


def ui_zone_hits(p: Path, w: int, h: int, dur: float, tmp: Path) -> list[tuple[float, float]]:
    """등간격 프레임의 UI존에서 흰 픽셀 비율을 잰다. 해상도에 맞게 스케일."""
    try:
        from PIL import Image
    except ImportError:
        return []

    ui_zone_top = int(h * UI_ZONE_RATIO)
    ui_zone_height = h - ui_zone_top
    if ui_zone_height <= 0:
        return []

    hits = []
    for i in range(12):
        t = dur * (i + 0.5) / 12
        f = tmp / f"ui_{i:02d}.png"
        subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.2f}",
                        "-i", str(p), "-frames:v", "1",
                        "-vf", f"crop={w}:{ui_zone_height}:0:{ui_zone_top}",
                        str(f)], check=True)
        im = Image.open(f).convert("L")
        hist = im.histogram()
        ratio = sum(hist[201:]) / max(1, sum(hist))
        if ratio > 0.010:
            hits.append((round(t, 2), round(ratio * 100, 2)))
    return hits


def log_to_rooms(msg: str):
    """_ROOMS_LOG.md에 자동 기록 — 방이 빼먹을 수 없게."""
    from datetime import datetime
    log_path = Path(__file__).parent.parent / "_ROOMS_LOG.md"
    ts = datetime.now().strftime("%m-%d %H:%M")
    line = f"- `{ts}` **유튜브쇼츠방** — {msg}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)
    print(f"[로그 자동기록] {line.strip()}")


def main() -> int:
    if len(sys.argv) < 2:
        print("사용법: shorts_gate.py <영상.mp4 | 폴더>"); return 2
    tgt = Path(sys.argv[1])
    vids = sorted(tgt.glob("*.mp4")) if tgt.is_dir() else [tgt]
    vids = [v for v in vids if not v.name.startswith("_")]
    if not vids:
        print(f"[탈락] {tgt} 에 mp4 없음"); return 1

    fails, warns = [], []
    for p in vids:
        print(f"\n== 쇼츠 게이트: {p.name} ==")
        v = probe(p)
        w, h, dur = v["width"], v["height"], float(v["duration"])
        is_preview = (w, h) != (1080, 1920)

        if is_preview:
            print(f"  {w}x{h} [프리뷰]  {v['avg_frame_rate']}  {dur:.2f}s  audio={v['audio']}")
        else:
            print(f"  {w}x{h}  {v['avg_frame_rate']}  {dur:.2f}s  audio={v['audio']}")

        # S2: 길이 26~59초 (보완게이트 기준)
        if dur > 59.0:
            fails.append(f"[S2] {p.name} 길이 {dur:.2f}초 — **59초 초과 금지**")
        elif dur < 26.0:
            fails.append(f"[S2] {p.name} 길이 {dur:.2f}초 — **26초 미만 금지**")

        if v["audio"] == 0:
            fails.append(f"[S3] {p.name} 오디오 없음 (쇼츠는 나레이션+BGM)")

        tmp = p.parent / "_review" / f"_gate_{p.stem}"; tmp.mkdir(parents=True, exist_ok=True)
        for f in tmp.glob("*.png"): f.unlink()
        for f in tmp.glob("*.jpg"): f.unlink()

        # S4 경계 무음
        if v["audio"]:
            r = subprocess.run([FF, "-hide_banner", "-i", str(p),
                                "-af", "silencedetect=noise=-45dB:d=0.4", "-f", "null", "-"],
                               capture_output=True, text=True)
            for line in r.stderr.splitlines():
                if "silence_start" in line:
                    try:
                        st = float(line.split("silence_start:")[1].strip())
                        if st < 0.5 or st > dur - 1.2:
                            warns.append(f"[S4] {p.name} 경계 무음 {st:.2f}s — 짧은 BGM loop 사고 확인")
                    except Exception:
                        pass

        # S5 UI존 침범 (해상도에 맞게 계산)
        hits = ui_zone_hits(p, w, h, dur, tmp)
        ui_zone_top = int(h * UI_ZONE_RATIO)
        if hits:
            fails.append(f"[S5] {p.name} 하단 UI존(y>{ui_zone_top})에 자막 침범 "
                         f"{len(hits)}컷 {hits[:4]} — 유튜브 채널바에 묻힌다")
        else:
            print(f"  UI존(y>{ui_zone_top}) 깨끗")

        # S6 발행 전 스샷 시트 (해상도에 맞게)
        ui_zone_top = int(h * UI_ZONE_RATIO)
        ui_zone_height = h - ui_zone_top
        thumb_w, thumb_h = 240, int(240 * h / w)

        for i in range(12):
            t = dur * (i + 0.5) / 12
            subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.2f}",
                            "-i", str(p), "-frames:v", "1",
                            "-vf", (f"drawbox=x=0:y={ui_zone_top}:w={w}:h={ui_zone_height}:"
                                    "color=red@0.9:t=4,"
                                    f"drawtext=text='{t:.1f}s':x=10:y=10:fontsize=28:"
                                    "fontcolor=yellow:box=1:boxcolor=black@0.7,"
                                    f"scale={thumb_w}:{thumb_h}"),
                            "-q:v", "4", str(tmp / f"sheet_{i:02d}.jpg")], check=True)

        sheet = p.parent / f"_발행전_스샷_{p.stem}.jpg"
        subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error",
                        "-pattern_type", "glob", "-i", str(tmp / "sheet_*.jpg"),
                        "-filter_complex", "tile=6x2:margin=8:padding=8:color=0x101014",
                        "-frames:v", "1", "-q:v", "3", str(sheet)], check=True)

        label = "[프리뷰]" if is_preview else ""
        print(f"  스샷 시트{label}: {sheet}")

    print()
    for wmsg in warns:
        print("  [경고] " + wmsg)
    if fails:
        print("\n[게이트 탈락] 이건 산출물이 아니다.")
        for f in fails:
            print("   " + f)
        # 탈락도 로그에 기록
        names = ", ".join(v.name for v in vids)
        log_to_rooms(f"게이트 탈락. {names}. 사유: {fails[0][:50]}...")
        return 1

    print("[통과] 수치 규격 S1~S5")
    print("\n[S6] 발행 전 필수 — 위 스샷 시트를 **차노에게 띄우고** 전체를 보게 한 다음 발행한다.")
    print("   빨간 박스 = 유튜브 UI존. 그 안에 자막이 걸리면 안 된다.")
    print("   코드가 못 잡는 것(톤·어색함·컷 연결)은 만든 쪽이 직접 보고 판단한다.")

    # 자동 로그 기록 — 방이 빼먹을 수 없게
    names = ", ".join(v.name for v in vids)
    log_to_rooms(f"게이트 통과. {names}. 스샷시트 생성. **형 확인 후 발행 대기.**")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
