#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""대본을 **한 번에 통으로** 합성하고 글자 타임스탬프로 자막 시각을 뽑는다.

⚠️ 왜 바꿨나 (차노 2026-08-18 "컷과 컷 사이 발음이 뭉개지거나 뚝뚝 끊긴다")
   전 방식은 22줄을 **따로 합성해 이어붙였다.** 그래서
     · 줄마다 목소리가 새로 시작해 이음매가 들린다
     · 앞뒤 무음을 자르면서 ㅅ·ㅎ·ㅍ 같은 여린 자음의 머리·꼬리가 깎였다 → 발음이 뭉갠다
   → **한 번의 요청으로 전체를 읽게 하고**, 응답의 글자별 타임스탬프로 줄 시작 시각을 계산한다.
     이음매가 아예 없고, 자막은 실제 발음 시각에 붙는다.

샌드박스 밖(remote_cmd_watch)에서 실행할 것.
"""
import base64, json, os, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG  = json.loads((ROOT / "secrets/elevenlabs.json").read_text())
VS   = {"stability": 0.42, "similarity_boost": 0.85, "style": 0.15,
        "use_speaker_boost": True, "speed": 1.08}
TAIL = 0.45          # 마지막 말 뒤 여운

def main():
    man = Path(sys.argv[1])
    d = json.loads(man.read_text()); cuts = d["cuts"]
    spoken = [c for c in cuts if not c.get("outro")]      # 아웃트로는 읽지 않는다
    lines = [c["말"] for c in spoken]
    # 개행으로 이으면 모델이 문단 쉼(최대 3.4초)을 넣는다 → 한 칸 띄어쓰기로 잇는다.
    # 문장 끝 마침표가 자연스러운 쉼을 이미 준다.
    text = " ".join(lines)

    url = ("https://api.elevenlabs.io/v1/text-to-speech/%s/with-timestamps"
           "?output_format=mp3_44100_128" % CFG["voice_id"])
    body = json.dumps({"text": text, "model_id": CFG.get("model_id", "eleven_multilingual_v2"),
                       "voice_settings": VS}).encode()
    req = urllib.request.Request(url, data=body, headers={
        "xi-api-key": CFG["api_key"], "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        res = json.loads(r.read())

    out = ROOT / "_out/shorts/senior_voice_ts.mp3"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(res["audio_base64"]))
    al = res.get("alignment") or res.get("normalized_alignment") or {}
    chars = al.get("characters", [])
    starts = al.get("character_start_times_seconds", [])
    ends = al.get("character_end_times_seconds", []) or starts
    if not chars:
        print("⛔ 타임스탬프 없음"); return 1
    print("오디오 %d bytes · 글자 %d개" % (out.stat().st_size, len(chars)), flush=True)

    # 글자 인덱스 → 각 줄의 첫 글자/마지막 글자 위치
    pos, line_span = 0, []
    for i, ln in enumerate(lines):
        s0 = pos; s1 = pos + len(ln) - 1
        line_span.append((s0, s1)); pos = s1 + 2      # +1 글자, +1 구분자(공백)
    def t_of(idx, arr, default):
        return float(arr[idx]) if 0 <= idx < len(arr) else default

    total_audio = float(ends[-1]) if ends else 0.0
    for i, c in enumerate(spoken):
        s0, s1 = line_span[i]
        c["speak_at"] = round(t_of(s0, starts, 0.0), 3)
        c["speak_end"] = round(t_of(s1, ends, total_audio), 3)
    # 컷 경계 = 이전 줄 끝과 다음 줄 시작의 중간 (말 위에서 자막이 바뀌지 않게)
    for i, c in enumerate(spoken):
        c["start"] = 0.0 if i == 0 else round((spoken[i-1]["speak_end"] + c["speak_at"]) / 2, 3)
    for i, c in enumerate(spoken):
        c["end"] = spoken[i+1]["start"] if i + 1 < len(spoken) else round(c["speak_end"] + TAIL, 3)
    # 아웃트로
    for c in cuts:
        if c.get("outro"):
            # 아웃트로 최소 2.6초. 단, 게이트가 26초 미만을 막으므로(짧은 편) 모자라면 늘린다.
            olen = max(2.6, 27.0 - spoken[-1]["end"])
            c["start"] = spoken[-1]["end"]; c["end"] = round(c["start"] + olen, 3)
            c.pop("speak_at", None); c.pop("speak_end", None)
    for c in cuts: c["voice_track"] = "_out/shorts/senior_voice_ts.mp3"
    man.write_text(json.dumps({"cuts": cuts}, ensure_ascii=False, indent=1))

    tot = cuts[-1]["end"]
    padded = ROOT / "_out/shorts/senior_voice_ts_pad.mp3"
    subprocess.run(["ffmpeg","-v","error","-i",str(out),"-af","apad=whole_dur=%.2f" % tot,
                    "-ar","48000","-ac","2","-b:a","192k",str(padded),"-y"], check=True)
    r = subprocess.run(["ffmpeg","-hide_banner","-i",str(padded),"-af",
                        "silencedetect=noise=-38dB:d=0.12","-f","null","-"],
                       capture_output=True, text=True)
    import re
    sil = [float(x) for x in re.findall(r"silence_duration: ([0-9.]+)", r.stderr)]
    print("총 %.2f초 · 말 %.2f초 · 무음 %d구간 합계 %.2f초 (최장 %.2f초)"
          % (tot, total_audio, len(sil), sum(sil), max(sil) if sil else 0), flush=True)
    print("매니페스트 갱신: %s" % man.name, flush=True)
    return 0

sys.exit(main())
