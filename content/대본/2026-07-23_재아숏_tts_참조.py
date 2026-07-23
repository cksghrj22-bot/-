#!/usr/bin/env python3
"""재아 나레이션 TTS — 차노 클론·A_차분(둘째 줄기). 라임 부호 반영 + 줄별 타이밍 저장."""
import json, sys
from pathlib import Path
sys.path.insert(0, "/home/user/-")
from shorts import tts
from collections import namedtuple

BASE = Path("/tmp/claude-0/-home-user--/4c303924-cd2a-54ae-bace-87654ed6e323/scratchpad/jaea")
WORK = BASE / "tts_work"; WORK.mkdir(parents=True, exist_ok=True)
OUT = BASE / "narration_v2.m4a"
Line = namedtuple("Line", ["text"])

# 다듬음 확정본 (형 수정 반영: 성장하는 길·발전·성장할 길). 각 줄=자막 한 단위·발화 한 호흡.
LINES = [
    "오늘은, 지각한 직원이랑 같이 하이록스를 했어요.",
    "혼내는 대신, 운동 데이트를 한 거죠.",
    "예전 같으면 이랬을 거예요.",
    "세 번째야. 그러니까 청소해.",
    "근데 그건 벌이지,",
    "이 친구가 성장하는 길은 아니더라고요.",
    "그래서 같이 땀 흘리고, 밥도 먹으면서 얘기를 나눴죠.",
    "지각 자체가 잘못이 아니라,",
    "그 빈자리를 동료들이 대신 메웠다는 거.",
    "거기에 미안하고,",
    "채워준 사람들한테 고마워할 줄 아는 마음.",
    "저는 그걸 아는 게 진짜라고 생각해요.",
    "왜 안 했어? 다그치는 말은,",
    "아무것도 바꾸지 못해요.",
    "근데 어떻게 하면 좋았을까, 묻는 순간",
    "사람은 조금씩 발전하더라고요.",
    "그래서 앞으로도, 감정으로 혼내기보다",
    "같이 성장할 길을 찾는 원장이 되려고요.",
]

creds = json.loads(Path("/home/user/-/secrets/elevenlabs.json").read_text())
creds["model_id"] = creds.get("model_id") or "eleven_multilingual_v2"
creds["voice_settings"] = {"stability": 0.38, "similarity_boost": 0.82, "style": 0.28, "use_speaker_boost": True}
creds["speed"] = 1.0
creds["punct_targets"] = {".": 0.18, "?": 0.20, "!": 0.20, "…": 0.16, ",": 0.08}

lines = [Line(t) for t in LINES]
out, spans = tts.build_narration_single(lines, creds, WORK, OUT)
data = {"out": str(out), "lines": LINES, "spans": spans}
(BASE / "narration_v2_spans.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
print("나레이션:", out)
print(f"줄 {len(spans)}개 · 총길이 {spans[-1][1]:.2f}s")
for i, (l, (s, e)) in enumerate(zip(LINES, spans)):
    print(f"  {s:5.2f}-{e:5.2f}  {l[:30]}")
