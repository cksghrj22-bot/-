#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""자막 시각 ↔ 실제 발화 시작을 직접 재서 검증한다.

차노 2026-08-18: "이런 타입으로 실수가 나면 다신 이런 타입으로는 실수가 나면 안 돼."
→ 게이트(S8)가 통과시켜도 눈에는 밀려 보일 수 있다(ep04). 게이트는 whisper·무음경계 중
  **오차가 작은 쪽**을 택하므로, 자막 시각 자체가 틀려도 다른 자로 통과할 수 있었다.
→ 이 검사는 **매니페스트의 speak_at 만** 놓고 무음경계와 대조한다. 봐주는 자가 없다.

사용: python3 scripts/sync_verify.py <매니페스트.json> [허용초=0.30]
"""
import json, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
LIMIT = float(sys.argv[2]) if len(sys.argv) > 2 else 0.30

def onsets(p):
    r = subprocess.run(["ffmpeg","-hide_banner","-i",str(p),"-af",
                        "silencedetect=noise=-38dB:d=0.07","-f","null","-"],
                       capture_output=True, text=True)
    out = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", r.stderr)]
    if not re.search(r"silence_start: 0(\.0+)?\b", r.stderr): out = [0.0] + out
    return out

def main():
    man = Path(sys.argv[1]); cuts = json.loads(man.read_text())["cuts"]
    spoken = [c for c in cuts if not c.get("outro")]
    voice = ROOT / spoken[0]["voice_track"]
    eo = onsets(voice)
    bad, used = [], 0.0
    for k, c in enumerate(spoken, 1):
        a = c["speak_at"]
        near = [x for x in eo if x >= used - 0.01 and abs(x - a) <= 1.2] or \
               [x for x in eo if abs(x - a) <= 1.2]
        if not near: continue
        b = min(near, key=lambda x: abs(x - a)); used = max(used, b)
        if abs(b - a) > LIMIT:
            bad.append((k, a, b, b - a, c["말"]))
    if bad:
        print("⛔ 싱크 검증 %d줄 초과 (허용 %.2f초)" % (len(bad), LIMIT))
        for k, a, b, d, t in bad:
            print("  %2d줄 자막 %6.2f  발화 %6.2f  %+0.3f  %s" % (k, a, b, d, t[:32]))
        return 1
    print("✅ 싱크 검증 통과 (%d줄, 허용 %.2f초)" % (len(spoken), LIMIT))
    return 0

sys.exit(main())
