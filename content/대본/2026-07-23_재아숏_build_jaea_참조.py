#!/usr/bin/env python3
"""재아 러닝메이트 숏 — 둘째 줄기 편집(컬러·자막 윤곽선 하단·목소리 끝=영상 끝).
나레이션(29.7s) + 하이록스 재아 footage EDL. ⭐재아 최다 등장 · 차노=클로징."""
import subprocess
from pathlib import Path

W, H, VH = 1080, 1920, 1350          # 캔버스 1080x1920, 영상 4:5 크롭 영역 1080x1350 + 상하 검정밴드
BASE = Path("/tmp/claude-0/-home-user--/4c303924-cd2a-54ae-bace-87654ed6e323/scratchpad")
HY = BASE / "hyrox"
WORK = BASE / "jaea" / "work"; WORK.mkdir(parents=True, exist_ok=True)
NAR = BASE / "jaea" / "narration.m4a"
BGM = "/home/user/-/shorts/assets/bgm_piano_long.mp3"
OUT = BASE / "재아_러닝메이트_숏.mp4"
GRADE = "eq=saturation=1.08:contrast=1.03"   # 그레이딩 최소·생기만
NAR_DUR = 29.70

# 나레이션 줄 시작초(B방 EDL) → (clip, clip_in, 자막)  ·재아 위주, 차노=클로징
cues = [0.00, 3.16, 4.89, 6.82, 8.69, 10.05, 12.56, 14.76, 17.47, 19.86, 23.69, 26.99, NAR_DUR]
SEGS = [
    ("IMG_2017", 3.0,  "지각한 직원,\\N예전 같으면 혼냈어요."),
    ("IMG_2002", 2.0,  "오늘은 같이 운동을 했어요."),
    ("IMG_2012", 1.0,  "땀 한 번 흘리고 나니까\\N보이더라고요."),
    ("IMG_2017", 9.0,  "이 친구도 일부러\\N그런 게 아니구나."),
    ("IMG_2008", 1.0,  "혼내는 건 쉬워요."),
    ("IMG_2014", 2.0,  "너 세 번째야,\\N그러니까 청소해."),
    ("IMG_2016", 2.0,  "근데 그건 벌이지,\\N성장이 아니잖아요."),
    ("IMG_2002", 9.0,  "카운트를 세되,\\N러닝메이트로 셌어요."),
    ("IMG_2006", 2.0,  "옆에서 같이 뛰면서,\\N계속 보고 있다고."),
    ("IMG_2012", 4.0,  "그 사람이 바라는\\N그 사람이 되게."),
    ("IMG_2020", 2.0,  "벌 주려는 게 아니라,\\N같이 가려는 거니까요."),
    ("IMG_1999", 1.0,  "원장이 먼저 뛰면,\\N직원은 따라 뜁니다."),
]


def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def build_ass(path):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: sub,NanumSquareRound,58,&H00FFFFFF,&H00000000,&H00000000,-1,1,6,2,2,90,90,150,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    body = ""
    for i, (_, _, txt) in enumerate(SEGS):
        body += f"Dialogue: 0,{ts(cues[i])},{ts(cues[i+1])},sub,,0,0,0,,{txt}\n"
    path.write_text(head + body, encoding="utf-8")


def make_seg(i):
    clip, cin, _ = SEGS[i]
    dur = cues[i+1] - cues[i]
    src = HY / f"{clip}.mov"
    out = WORK / f"js{i:02d}.mp4"
    vf = (f"scale={W}:{VH}:force_original_aspect_ratio=increase,crop={W}:{VH},"
          f"{GRADE},fps=30,setsar=1,pad={W}:{H}:0:{(H-VH)//2}:black")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{cin:.2f}", "-t", f"{dur:.2f}",
                    "-i", str(src), "-an", "-vf", vf,
                    "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(out)], check=True)
    return out


def main():
    parts = []
    for i in range(len(SEGS)):
        print(f"[{i+1}/{len(SEGS)}] {SEGS[i][0]} {cues[i+1]-cues[i]:.2f}s", flush=True)
        parts.append(make_seg(i))
    lst = WORK / "list.txt"; lst.write_text("".join(f"file '{p}'\n" for p in parts))
    silent = WORK / "video_silent.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c", "copy", str(silent)], check=True)
    ass = WORK / "sub.ass"; build_ass(ass)
    # 자막 굽기
    subbed = WORK / "video_sub.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent),
                    "-vf", f"subtitles='{ass}'", "-c:v", "libx264", "-preset", "veryfast",
                    "-pix_fmt", "yuv420p", str(subbed)], check=True)
    # 나레이션(목소리 끝=영상 끝) + BGM 언더
    print("mux 나레이션+BGM...", flush=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(subbed), "-i", str(NAR),
                    "-stream_loop", "-1", "-i", BGM,
                    "-filter_complex",
                    "[1:a]loudnorm=I=-16:TP=-1.5[nar];[2:a]volume=0.07[bg];"
                    "[nar][bg]amix=inputs=2:duration=first:dropout_transition=0[a]",
                    "-map", "0:v", "-map", "[a]", "-t", f"{NAR_DUR:.2f}",
                    "-c:v", "copy", "-c:a", "aac", "-ar", "44100", str(OUT)], check=True)
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "csv=p=0", str(OUT)], capture_output=True, text=True).stdout.strip() or 0)
    print(f"DONE {OUT} {d:.1f}s", flush=True)


if __name__ == "__main__":
    main()
