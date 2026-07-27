"""창엽 「커트의 정석」 쇼츠 빌더 — 원본 발화(창엽) 구간을 채널 쇼츠 규격으로 컷.

⚠️ 이건 TTS 나레이션 쇼츠(shorts.proof)가 아니라 **원본 발화 그대로 살리는** 교육쇼츠라
proof/render_lib 파이프라인을 못 탄다. 대신 §1 쇼츠 규격(prompts/07·제작규격_정본)을 그대로 강제한다:
- 캔버스 1080×1920, 영상=정사각(1:1) 중앙(형 2026-07-27 "정사각형 비율로")
- 제목 교보손글씨 128 노랑(&H0000D7FF) 상단 검정밴드(형 2026-07-27 "제목 크게"), 흰 보조훅
- 색보정 warm_film + dim 25%(제작규격_정본), BGM piano_long 14%
- 자막 = 창엽 실제 발화(diar speaker_0만), 지어내지 않음. 원본시간 매핑(-ss A 추출과 동기)
- 하단 UI존(바닥 380px) 위로 자막 배치
"""
import json, subprocess
CY = "/tmp/claude-0/-home-user--/4c303924-cd2a-54ae-bace-87654ed6e323/scratchpad/cy2"
KYOBO = "KyoboHandwriting2019"
BGM = "/home/user/-/shorts/assets/bgm_piano_long.mp3"
WARM = ("eq=saturation=0.90:contrast=1.06:brightness=0.02,"
        "colorbalance=rm=0.03:bm=-0.03:rh=0.02:bh=-0.03,"
        "curves=all='0/0.03 0.5/0.5 1/0.98'")
DIM = 0.25
VY = 520   # 정사각 영상 y위치(위=제목밴드 0~520, 영상 520~1600, 아래 UI존 회피)


def ts(x):
    h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def build(clip, A, B, h1, h2, outname):
    w = json.load(open(f"{CY}/diar_{clip}.json"))
    words = [(x['s'] - A, x['t']) for x in w
             if A <= x['s'] <= B and x.get('spk') == 'speaker_0']
    cues = []; cur = []
    for lt, t in words:
        cur.append((lt, t)); j = ' '.join(z[1] for z in cur)
        if len(j) >= 15 or t.strip().endswith(('.', '?', '!', '요', '다', '까', '고', '지', '네', '든', '야')):
            cues.append((cur[0][0], cur[-1][0] + 0.5, ' '.join(z[1] for z in cur).strip())); cur = []
    if cur:
        cues.append((cur[0][0], cur[-1][0] + 0.6, ' '.join(z[1] for z in cur).strip()))
    DUR = B - A
    # 제목 128 노랑(상단밴드 align8) + 흰 보조훅 104 · 자막 90 흰 검정박스 하단(align2, UI존 위)
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: t1,{KYOBO},128,&H0000D7FF,&H00000000,&H00000000,-1,1,4,0,8,40,40,70,1
Style: t2,{KYOBO},104,&H00FFFFFF,&H00000000,&H00000000,-1,1,3,0,8,40,40,250,1
Style: cap,{KYOBO},92,&H00FFFFFF,&H00000000,&H00000000,-1,1,5,2,2,60,60,470,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,{ts(0)},{ts(DUR)},t1,,0,0,0,,{h1}
Dialogue: 0,{ts(0)},{ts(DUR)},t2,,0,0,0,,{h2}
"""
    body = ""
    for s0, e0, txt in cues:
        if len(txt) > 15:
            mid = len(txt) // 2; sp = txt.rfind(' ', 0, mid + 3)
            if sp > 3:
                txt = txt[:sp] + "\\N" + txt[sp + 1:]
        body += f"Dialogue: 0,{ts(s0)},{ts(e0)},cap,,0,0,0,,{txt}\n"
    ass = f"{CY}/_{outname}.ass"; open(ass, "w", encoding="utf-8").write(head + body)
    vf = (f"[0:v]crop=1080:1080:420:0,{WARM},drawbox=c=black@{DIM}:t=fill,"
          f"scale=1080:1080,setsar=1[v];"
          f"color=c=black:s=1080x1920:d={DUR}[bg];[bg][v]overlay=0:{VY}[b1];"
          f"[b1]subtitles={ass}[vout];"
          f"[1:a]volume=0.14,afade=t=out:st={DUR-1.5}:d=1.5[bgm];"
          f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=0[aout]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(A), "-t", str(DUR),
        "-i", f"{CY}/hq_{clip}.mp4", "-i", BGM, "-filter_complex", vf,
        "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "medium",
        "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-r", "30",
        "-shortest", f"{CY}/{outname}.mp4"], check=True)
    d = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'csv=p=0', f"{CY}/{outname}.mp4"], capture_output=True, text=True).stdout.strip()
    print(f"{outname}: {d}s · {len(cues)}큐")


CFG = [
    ("9005", 35.0, 60.0, "머리 붕 뜨게 하는 법", "질감처리의 비밀", "창엽쇼츠_01_질감처리"),
    ("9005", 68.0, 98.0, "머리 무게감 빼는 법", "디스커넥션의 원리", "창엽쇼츠_02_무게감"),
    ("9006", 103.8, 132.2, "짧게 자르면 안 되는 이유", "고객 모질을 봐야 하는 법", "창엽쇼츠_03_모질"),
    ("9006", 618.5, 643.0, "여성스러운 커트의 비밀", "시스루의 원리", "창엽쇼츠_04_시스루"),
    ("9006", 744.5, 766.0, "가위 슬라이싱의 원리", "움직임을 만드는 커트", "창엽쇼츠_05_슬라이싱"),
    ("9006", 442.0, 467.0, "질감처리 명암 읽는 법", "자를 곳과 남길 곳", "창엽쇼츠_06_명암"),
    # ⛔ 07 베이직(9007 [841,878]) 폐기: hq_9007 프록시는 EP.3용 769s 트림본이라
    #    diar_9007의 841s 구간이 소스에 없어 영상이 검정으로 나옴(2026-07-27 실증).
    #    베이직 캡스톤을 살리려면 9007 원본(1078s)을 다시 프록시화해야 함.
]

if __name__ == "__main__":
    import sys
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for c in CFG:
        if only and only not in c[5]:
            continue
        build(*c)
