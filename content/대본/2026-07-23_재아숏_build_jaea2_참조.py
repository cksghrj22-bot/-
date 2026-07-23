#!/usr/bin/env python3
"""재아 러닝메이트 숏 v2 — 새 나레이션(40.4s)·중앙 레이아웃·재아 최다.
둘째 줄기: 컬러·NanumSquareRound 윤곽선 자막·목소리 끝=영상 끝. TTS 줄 타이밍에 컷·자막 싱크."""
import json, subprocess
from pathlib import Path

W, H, VH = 1080, 1920, 1200
TOP_BAND = (H - VH) // 2               # 중앙(이찬호 "중앙으로 다시") = 360
SUB_MV = 430                            # 자막: 중앙 영상의 하단부(윤곽선), 밴드 아님
BASE = Path("/tmp/claude-0/-home-user--/4c303924-cd2a-54ae-bace-87654ed6e323/scratchpad")
HY = BASE / "hyrox"
WORK = BASE / "jaea" / "work2"; WORK.mkdir(parents=True, exist_ok=True)
NAR = BASE / "jaea" / "narration_clean.m4a"   # 무음 트림본(실측 STT 타이밍과 일치)
BGM = "/home/user/-/shorts/assets/bgm_piano_long.mp3"
OUT = BASE / "재아_러닝메이트_숏.mp4"
GRADE = "eq=saturation=1.08:contrast=1.03"

D = json.loads((BASE / "jaea" / "spans_stt.json").read_text())   # STT 실측 스팬(추측 아님)
LINES, SPANS = D["lines"], D["spans"]
# NAR_DUR = 실제 나레이션 오디오 길이(끝 안 잘림·뒤 무음 없음)
NAR_DUR = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", str(NAR)], capture_output=True, text=True).stdout.strip())

# 줄 index → (clip, clip_in, 자막표시(2줄 \N))  ·재아 위주·차노=운동/클로징
ASSIGN = [
    ("IMG_2017", 3.0,  "오늘은, 지각한 직원이랑\\N같이 하이록스를 했어요."),
    ("IMG_2020", 2.0,  "혼내는 대신,\\N운동 데이트를 한 거죠."),
    ("IMG_2016", 3.0,  "예전 같으면 이랬을 거예요."),
    ("IMG_2014", 2.0,  "\"세 번째야.\\N그러니까 청소해.\""),
    ("IMG_2008", 1.0,  "근데 그건 벌이지,"),
    ("IMG_2017", 9.0,  "이 친구가 성장하는 길은\\N아니더라고요."),
    ("IMG_2002", 2.0,  "그래서 같이 땀 흘리고,\\N밥도 먹으면서 얘기를 나눴죠."),
    ("IMG_2012", 1.0,  "지각 자체가 잘못이 아니라,"),
    ("IMG_2006", 2.0,  "그 빈자리를 동료들이\\N대신 메웠다는 거."),
    ("IMG_2017", 15.0, "거기에 미안하고,"),
    ("IMG_2020", 8.0,  "채워준 사람들한테\\N고마워할 줄 아는 마음."),
    ("IMG_2016", 8.0,  "저는 그걸 아는 게\\N진짜라고 생각해요."),
    ("IMG_2014", 6.0,  "\"왜 안 했어?\" 다그치는 말은,"),
    ("IMG_2012", 4.0,  "아무것도 바꾸지 못해요."),
    ("IMG_2002", 10.0, "근데 \"어떻게 하면 좋았을까\"\\N묻는 순간,"),
    ("IMG_2017", 25.0, "사람은 조금씩\\N발전하더라고요."),
    ("IMG_2006", 10.0, "그래서 앞으로도,\\N감정으로 혼내기보다"),
    ("IMG_1999", 1.0,  "같이 성장할 길을 찾는\\N원장이 되려고요."),
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
Style: sub,NanumSquareRound,58,&H00FFFFFF,&H00000000,&H00000000,-1,1,6,2,2,90,90,{SUB_MV},1
Style: outro,NanumSquareRound,42,&H70FFFFFF,&H00000000,&H00000000,0,1,2,0,2,60,60,70,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    body = ""
    for i, (s, e) in enumerate(SPANS):
        body += f"Dialogue: 0,{ts(s)},{ts(e)},sub,,0,0,0,,{ASSIGN[i][2]}\n"
    # 아웃트로: 마지막 2.6초 하단 얇게(박스 없음) — 저장 CTA 아님(마스터 규격)
    body += f"Dialogue: 1,{ts(max(0,NAR_DUR-2.6))},{ts(NAR_DUR)},outro,,0,0,0,,SNS에 일기를 쓰고 있어요\n"
    path.write_text(head + body, encoding="utf-8")


def make_seg(i):
    clip, cin, _ = ASSIGN[i]
    # 구간을 '다음 줄 시작'까지(마지막은 나레이션 끝까지) 이어붙여 영상 길이=나레이션 길이 → 끝 음성 안 잘림
    seg_end = SPANS[i + 1][0] if i + 1 < len(SPANS) else NAR_DUR
    dur = seg_end - SPANS[i][0]
    out = WORK / f"js{i:02d}.mp4"
    vf = (f"scale={W}:{VH}:force_original_aspect_ratio=increase,crop={W}:{VH},"
          f"{GRADE},fps=30,setsar=1,pad={W}:{H}:0:{TOP_BAND}:black")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{cin:.2f}", "-t", f"{dur:.2f}",
                    "-i", str(HY / f"{clip}.mov"), "-an", "-vf", vf,
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(out)], check=True)
    return out


def main():
    parts = []
    for i in range(len(ASSIGN)):
        print(f"[{i+1}/{len(ASSIGN)}] {ASSIGN[i][0]} {SPANS[i][1]-SPANS[i][0]:.2f}s", flush=True)
        parts.append(make_seg(i))
    lst = WORK / "list.txt"; lst.write_text("".join(f"file '{p}'\n" for p in parts))
    silent = WORK / "vsilent.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c", "copy", str(silent)], check=True)
    ass = WORK / "sub.ass"; build_ass(ass)
    subbed = WORK / "vsub.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent),
                    "-vf", f"subtitles='{ass}'", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                    "-pix_fmt", "yuv420p", str(subbed)], check=True)
    print("mux 나레이션+BGM...", flush=True)
    # dynaudnorm=길이 안 변함(loudnorm의 3초 잘림 회피). 나레이션 우선·BGM 언더.
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(subbed), "-i", str(NAR),
                    "-stream_loop", "-1", "-i", BGM,
                    "-filter_complex",
                    "[1:a]dynaudnorm=f=250:g=15[nar];[2:a]volume=0.06[bg];"
                    "[nar][bg]amix=inputs=2:duration=first:dropout_transition=0[a]",
                    "-map", "0:v", "-map", "[a]", "-t", f"{NAR_DUR:.3f}",
                    "-c:v", "copy", "-c:a", "aac", "-ar", "44100", str(OUT)], check=True)
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "csv=p=0", str(OUT)], capture_output=True, text=True).stdout.strip() or 0)
    print(f"DONE {OUT} {d:.1f}s", flush=True)


if __name__ == "__main__":
    main()
