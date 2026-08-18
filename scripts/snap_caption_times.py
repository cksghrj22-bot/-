#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""자막 시각을 **실제 발음이 시작되는 지점**에 스냅한다.

ElevenLabs 글자 타임스탬프는 대체로 정확하지만, 쉼 뒤 첫 글자에서 최대 0.7초까지 앞서 찍힌다
(2026-08-18 실측: 「아니라, 방향을 다시 잡는 겁니다」 +0.675초).
무음 경계로 잰 실제 발화 시작이 진짜다 → 그쪽으로 당긴다.
"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIN  = 1.10   # 이 범위 안에서만 스냅한다 (2026-08-18: 0.85 로는 한 줄이 0.371초 남았다)

def onsets(p):
    r = subprocess.run(["ffmpeg","-hide_banner","-i",str(p),"-af",
                        "silencedetect=noise=-38dB:d=0.07","-f","null","-"],
                       capture_output=True, text=True)
    out = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", r.stderr)]
    if not re.search(r"silence_start: 0(\.0+)?\b", r.stderr): out = [0.0] + out
    return out

def main():
    man = Path(sys.argv[1])
    d = json.loads(man.read_text()); cuts = d["cuts"]
    voice = ROOT / (cuts[0].get("voice_track") or "_out/shorts/senior_voice_ts_pad.mp3")
    eo = onsets(voice)
    spoken = [c for c in cuts if not c.get("outro")]
    moved = 0
    # ⚠️ 2026-08-18 (차노 "ep04 약간 싱크 밀린다") —
    #    전엔 줄마다 「가장 가까운 무음경계」를 독립적으로 골랐다.
    #    쉼표가 많은 편(ep04: 발화점 44개/자막 8줄)에서는 **한 줄 안의 쉼표 끊김**에 붙어버렸다.
    #    → 순서를 지키고(앞 줄이 쓴 지점은 다시 못 씀), **앞 줄 발화가 끝난 뒤**만 후보로 본다.
    used = 0.0
    for k, c in enumerate(spoken):
        a = c["speak_at"]
        floor = used + 0.05
        if k: floor = max(floor, spoken[k-1].get("speak_end", 0) - 0.15)
        near = [x for x in eo if x >= floor and abs(x - a) <= WIN]
        if not near:
            near = [x for x in eo if abs(x - a) <= WIN]     # 없으면 제약 풀고 최근접
        if not near:
            used = max(used, a); continue
        b = min(near, key=lambda x: abs(x - a))
        if abs(b - a) > 0.05:
            c["speak_at"] = round(b, 3); moved += 1
        used = max(used, c["speak_at"])
    # 컷 경계 재계산 — 이전 줄 끝과 다음 줄 시작의 중간
    for i, c in enumerate(spoken):
        c["start"] = 0.0 if i == 0 else round((spoken[i-1]["speak_end"] + c["speak_at"]) / 2, 3)
    for i, c in enumerate(spoken):
        c["end"] = spoken[i+1]["start"] if i + 1 < len(spoken) else c["end"]
    for c in cuts:
        if c.get("outro"):
            olen = max(2.6, 27.4 - spoken[-1]["end"])   # 게이트 하한 26초 + 크로스페이드 0.7 + 여유
            c["start"] = spoken[-1]["end"]; c["end"] = round(c["start"] + olen, 3)
            c.pop("xf_applied", None)
    man.write_text(json.dumps({"cuts": cuts}, ensure_ascii=False, indent=1))
    print("스냅 %d줄 · 총 %.2f초" % (moved, cuts[-1]["end"]))
    return 0

sys.exit(main())
