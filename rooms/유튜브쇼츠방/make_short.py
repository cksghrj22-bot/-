#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""쇼츠 한 편 = 명령 하나. (유튜브쇼츠방 정본 파이프라인 · 2026-08-18 차노 승인 v11 방식)

  매니페스트(뼈대) → ①통 TTS+글자타임스탬프 ②발음시작 스냅 ③장면 통컷 렌더
                   → ④아웃트로 크로스페이드 ⑤BGM 믹스 ⑥게이트

⚠️ 샌드박스 밖(remote_cmd_watch)에서 실행할 것 — ①이 네트워크를 쓴다.
   {"cmd":"python_script","args":["../rooms/유튜브쇼츠방/make_short.py", ...]} 는 안 된다.
   scripts/make_short_run.py 가 이 파일을 호출한다.

사용: python3 rooms/유튜브쇼츠방/make_short.py <매니페스트.json> <출력.mp4>
"""
import json, subprocess, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
XF   = 0.7          # 아웃트로 크로스페이드
BGM  = ROOT / "shorts/assets/bgm_piano_long.mp3"

def sh(argv, **kw):
    r = subprocess.run([str(a) for a in argv], capture_output=True, text=True, **kw)
    if r.returncode:
        print("⛔", " ".join(str(a) for a in argv)[:160], "\n", (r.stderr or "")[:400], flush=True)
        raise SystemExit(1)
    return r.stdout

def dur(p):
    return float(sh(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]).strip())

def main():
    man = Path(sys.argv[1]); out = Path(sys.argv[2])
    stem = out.stem
    wk = ROOT / ("_out/shorts/_build_%s" % stem)
    resume = "--resume" in sys.argv
    if resume:
        print("① 통 TTS — 건너뜀(--resume)", flush=True)
    else:
        print("① 통 TTS + 글자 타임스탬프", flush=True)
        sh([sys.executable, ROOT/"scripts/tts_senior_ts.py", man], cwd=ROOT)
    print("② 발음 시작 스냅", flush=True)
    sh([sys.executable, ROOT/"scripts/snap_caption_times.py", man], cwd=ROOT)

    cuts = json.loads(man.read_text())["cuts"]
    voice = ROOT / cuts[0]["voice_track"]
    tot = cuts[-1]["end"]
    pad = voice.with_name(voice.stem + "_pad.mp3")
    sh(["ffmpeg","-v","error","-i",voice,"-af","apad=whole_dur=%.2f"%tot,
        "-ar","48000","-ac","2","-b:a","192k",pad,"-y"])

    print("③ 장면 통컷 렌더", flush=True)
    raw = wk.parent / ("_%s_raw.mp4" % stem)
    sh([sys.executable, ROOT/"rooms/유튜브쇼츠방/build_scene_sian.py", man, raw, wk], cwd=ROOT)

    outro = next((c for c in cuts if c.get("outro")), None)
    vid = wk.parent / ("_%s_video.mp4" % stem)
    if outro:
        print("④ 아웃트로 크로스페이드 %.1f초" % XF, flush=True)
        os_, oe = outro["start"], outro["end"]
        m, o = "/tmp/_ms_main.mp4", "/tmp/_ms_outro.mp4"
        sh(["ffmpeg","-v","error","-i",raw,"-t","%.3f"%os_,"-c:v","libx264","-preset","veryfast",
            "-pix_fmt","yuv420p","-an",m,"-y"])
        sh(["ffmpeg","-v","error","-ss","%.3f"%os_,"-i",raw,"-c:v","libx264","-preset","veryfast",
            "-pix_fmt","yuv420p","-an",o,"-y"])
        sh(["ffmpeg","-v","error","-i",m,"-i",o,"-filter_complex",
            "[0][1]xfade=transition=fade:duration=%.2f:offset=%.3f,fade=t=out:st=%.3f:d=0.7[v]"
            % (XF, os_-XF, oe-XF-0.7), "-map","[v]","-c:v","libx264","-preset","veryfast",
            "-pix_fmt","yuv420p","-r","30",vid,"-y"])
        for c in cuts:
            if c.get("outro"):
                c["start"] = round(c["start"]-XF,3); c["end"] = round(c["end"]-XF,3)
        man.write_text(json.dumps({"cuts": cuts}, ensure_ascii=False, indent=1))
    else:
        sh(["ffmpeg","-v","error","-i",raw,"-c","copy",vid,"-y"])

    V = dur(vid)
    print("⑤ BGM 믹스 (영상 %.2f초)" % V, flush=True)
    mix = wk.parent / ("_%s_mix.mp3" % stem)
    sh(["ffmpeg","-v","error","-stream_loop","-1","-i",BGM,"-i",pad,"-filter_complex",
        "[0]atrim=0:%.2f,afade=t=in:st=0:d=1.4,afade=t=out:st=%.2f:d=2.4,volume=0.22[b];"
        "[1]atrim=0:%.2f,loudnorm=I=-14:TP=-1.5:LRA=11,asplit=2[v1][v2];"
        "[b][v1]sidechaincompress=threshold=0.04:ratio=10:attack=12:release=320[bd];"
        "[bd][v2]amix=inputs=2:normalize=0,alimiter=limit=0.95,afade=t=out:st=%.2f:d=0.7[m]"
        % (V+0.4, max(0,V-2.6), V, max(0,V-0.7)), "-map","[m]","-ar","48000","-ac","2",
        "-b:a","192k",mix,"-y"])
    sh(["ffmpeg","-v","error","-i",vid,"-i",mix,"-map","0:v:0","-map","1:a:0","-c:v","copy",
        "-c:a","aac","-b:a","192k","-ar","48000","-ac","2","-shortest",out,"-y"])
    print("⑥ 게이트", flush=True)
    r = subprocess.run([sys.executable, str(ROOT/"scripts/shorts_gate.py"), str(out),
                        "--manifest", str(man)], capture_output=True, text=True, cwd=ROOT)
    print(r.stdout[-1400:], flush=True)
    print("완성: %s (%.2f초)" % (out.name, dur(out)), flush=True)
    return 0 if "[통과]" in r.stdout else 2

sys.exit(main())
