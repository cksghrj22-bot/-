#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""매니페스트의 말 22줄을 줄별로 TTS 합성 → 실측 길이로 매니페스트 타이밍 재계산.

⚠️ 샌드박스 밖(remote_cmd_watch)에서 돌려야 한다. codex_dispatch 로 돌리면 DNS 가 죽는다.
실행: {"cmd":"python_script","args":["tts_senior.py","<매니페스트.json>"]}

줄별로 따로 뽑고 **컷 길이를 실제 음성 길이에 맞춘다** → 자막·화면·목소리가 구조적으로 못 어긋난다.
"""
import json, os, sys, subprocess, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG  = json.loads((ROOT / "secrets/elevenlabs.json").read_text())
OUT  = ROOT / "_out/shorts/_voice"
PAD_HEAD, PAD_TAIL = 0.12, 0.34      # 말 앞뒤 여백 — 컷이 말에 딱 붙어 숨 막히지 않게
# 2026-08-10 실사고: speed 1.12 로 합성해 리듬이 깨졌다 → 정본 1.05
VS = {"stability": 0.42, "similarity_boost": 0.85, "style": 0.15,
      "use_speaker_boost": True, "speed": 1.05}

def dur(p):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(p)],
                       capture_output=True, text=True)
    try: return float(r.stdout)
    except: return 0.0

def tts(text, dest, prev="", nxt=""):
    if dest.exists() and dest.stat().st_size > 1000:
        return dur(dest)
    url = "https://api.elevenlabs.io/v1/text-to-speech/%s?output_format=mp3_44100_128" % CFG["voice_id"]
    body = json.dumps({"text": text, "model_id": CFG.get("model_id", "eleven_multilingual_v2"),
                       "voice_settings": VS, "previous_text": prev, "next_text": nxt}).encode()
    req = urllib.request.Request(url, data=body, headers={
        "xi-api-key": CFG["api_key"], "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        dest.write_bytes(r.read())
    d = dur(dest)
    print("  ✅ %-30s %.2f초  %d bytes" % (dest.name, d, dest.stat().st_size), flush=True)
    return d

def main():
    man = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "content/manifests/쇼츠_시니어_통합편_v5_20260817.json"
    OUT.mkdir(parents=True, exist_ok=True)
    cuts = json.loads(man.read_text())["cuts"]
    says = [c["말"] for c in cuts]
    print("TTS %d줄 · voice=%s · speed=%s" % (len(says), CFG["voice_id"], VS["speed"]), flush=True)
    t = 0.0; parts = []
    for i, c in enumerate(cuts):
        mp3 = OUT / ("l%02d.mp3" % i)
        d = tts(c["말"], mp3, says[i-1] if i else "", says[i+1] if i+1 < len(says) else "")
        if d <= 0:
            print("⛔ %d 합성 실패" % i); return 1
        seg = round(PAD_HEAD + d + PAD_TAIL, 2)
        c["start"], c["end"] = round(t, 2), round(t + seg, 2)
        c["voice"] = mp3.name; c["voice_sec"] = round(d, 2); c["speak_at"] = round(t + PAD_HEAD, 2)
        t = round(t + seg, 2); parts.append((mp3, seg))
    # 줄별 mp3 를 무음 패딩과 함께 이어붙인다 — 컷 경계와 말 시작점이 정확히 일치한다
    lst = OUT / "concat.txt"
    with open(lst, "w") as f:
        for mp3, seg in parts:
            f.write("file '%s'\n" % os.path.abspath(mp3))
    raw = OUT / "_raw.mp3"
    subprocess.run(["ffmpeg","-v","error","-f","concat","-safe","0","-i",str(lst),
                    "-c","copy",str(raw),"-y"], check=True)
    # 패딩을 반영해 정확히 다시 조립
    inputs, filt = [], []
    for i, (mp3, seg) in enumerate(parts):
        inputs += ["-i", str(mp3)]
        filt.append("[%d]adelay=%d|%d,apad=whole_dur=%.3f[a%d]" % (i, int(PAD_HEAD*1000), int(PAD_HEAD*1000), seg, i))
    fc = ";".join(filt) + ";" + "".join("[a%d]" % i for i in range(len(parts))) + "concat=n=%d:v=0:a=1[out]" % len(parts)
    final = ROOT / "_out/shorts/senior_voice_20260817.mp3"
    subprocess.run(["ffmpeg","-v","error"] + inputs + ["-filter_complex", fc, "-map","[out]",
                    "-ar","48000","-ac","2","-b:a","192k",str(final),"-y"], check=True)
    man.write_text(json.dumps({"cuts": cuts}, ensure_ascii=False, indent=1))
    print("\n총 길이 %.2f초 · 보이스 %s (%.2f초)" % (t, final.name, dur(final)), flush=True)
    print("매니페스트 타이밍 갱신 완료: %s" % man.name, flush=True)
    return 0

sys.exit(main())
