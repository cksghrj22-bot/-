"""창엽 컨셉 쇼츠 30편 4K 양산. keep 구간별 4K 추출→concat→원본전사 자막→훅제목+AT NOWN 아웃트로→업로드→로컬삭제.
사용: python3 build_all.py <start> <end>   (manifest30 인덱스, end 미포함. 엘레강스=0은 이미 완성이라 skip)
"""
import sys, os, json, subprocess
sys.path.insert(0, '/home/user/-')
import shorts.shortstyle as SS
from shorts import drive_stream as DS, gdrive
from shorts.creator_short import _wrap2, _style, _ts, WARM, DIM, VY, CANVAS
sys.path.insert(0, os.path.dirname(__file__))
from manifest30 import SHORTS, ORIG

REPO = "/home/user/-"; HERE = os.path.dirname(__file__)
NSQR = "/root/.fonts/nsqr_eb.ttf"
DRIVE_FOLDER = "1mchAPVsCAluJv3uGDvFdGM0LEg4hlEo4"  # 창엽_컨셉쇼츠_4K
OUT = f"{HERE}/final30"; os.makedirs(OUT, exist_ok=True)


def extract_keep(fid, oa, ob, out, tok):
    dur = ob - oa
    subprocess.run(["ffmpeg", "-v", "error", "-headers", f"Authorization: Bearer {tok}\r\n",
        "-ss", f"{oa:.3f}", "-i", f"https://www.googleapis.com/drive/v3/files/{fid}?alt=media",
        "-t", f"{dur:.3f}", "-vf", "crop=2160:2160:840:0,scale=1080:1080,fps=30,setsar=1",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", "-y", out], check=True, timeout=600)


def cues_from(words, keeps):
    # 유지구간 단어만, concat 타임라인으로 remap
    def remap(t):
        acc = 0.0
        for (oa, ob) in keeps:
            if oa <= t <= ob:
                return acc + (t - oa)
            acc += ob - oa
        return acc
    kept = [w for w in words if any(oa <= w['start'] <= ob for oa, ob in keeps)]
    cues = []; cur = []
    END = ('.', '?', '!', '요', '다', '까', '고', '든', '야', '죠', '네', '지')
    def flush(pad):
        ws = [c['text'].strip() for c in cur if c['text'].strip()]
        if ws:
            cues.append((round(remap(cur[0]['start']), 2), round(remap(cur[-1]['end']) + pad, 2), _wrap2(ws)))
    for i, x in enumerate(kept):
        cur.append(x); j = ' '.join(c['text'] for c in cur); d = cur[-1]['end'] - cur[0]['start']
        t = x['text'].strip()
        # 다음 단어가 다른 keep이면(경계) 강제 flush
        boundary = (i + 1 < len(kept)) and remap(kept[i+1]['start']) - remap(x['end']) > 0.25
        if (t and t[-1] in END) or len(j) >= 22 or d >= 3.6 or boundary:
            flush(0.35); cur = []
    if cur: flush(0.5)
    fixed = []
    for i, (s, e, ko) in enumerate(cues):
        if i + 1 < len(cues): e = min(e, cues[i+1][0] - 0.05)
        if e - s >= 0.4: fixed.append((s, e, ko))
    return fixed


def build_one(idx, tok):
    name, clip, keeps, (ty, tw) = SHORTS[idx]
    wd = f"{HERE}/_wd_{idx}"; os.makedirs(wd, exist_ok=True)
    fid = ORIG[clip]; words = json.load(open(f"{HERE}/orig_{clip}.words.json"))
    # 1) keep 구간 개별 추출→concat
    parts = []
    for k, (oa, ob) in enumerate(keeps):
        p = f"{wd}/k{k:02d}.mp4"; extract_keep(fid, oa, ob, p, tok); parts.append(p)
    open(f"{wd}/cc.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
    joined = f"{wd}/joined.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{wd}/cc.txt",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", joined], check=True)
    DUR = sum(ob - oa for oa, ob in keeps)
    # 2) 자막
    cues = cues_from(words, keeps)
    head = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {CANVAS[0]}\nPlayResY: {CANVAS[1]}\n"
            f"WrapStyle: 0\nScaledBorderAndShadow: yes\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, "
            "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
            "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"{_style('title', SS.POP_TITLE)}\n{_style('cap', SS.SUB)}\n[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            f"Dialogue: 0,{_ts(0)},{_ts(DUR)},title,,0,0,0,,{SS.pop_title(ty, tw)}\n")
    POS = r"{\an5\pos(540,1640)}"
    body = "".join(f"Dialogue: 0,{_ts(s)},{_ts(e)},cap,,0,0,0,,{POS}{ko}\n" for s, e, ko in cues)
    ass = f"{wd}/s.ass"; open(ass, "w", encoding="utf-8").write(head + body)
    vf = (f"[0:v]{WARM},drawbox=c=black@{DIM}:t=fill,setsar=1[v];"
          f"color=c=black:s={CANVAS[0]}x{CANVAS[1]}:d={DUR}[bg];[bg][v]overlay=0:{VY}[b1];"
          f"[b1]subtitles={ass},fade=t=out:st={DUR-0.6}:d=0.6[vout];"
          f"[1:a]volume=0.14,afade=t=out:st={DUR-1.5}:d=1.5[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=0[aout]")
    main = f"{wd}/main.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", joined, "-i", f"{REPO}/shorts/assets/bgm_piano_long.mp3",
        "-filter_complex", vf, "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", "-shortest", main], check=True)
    # 3) AT NOWN 아웃트로
    OD = 3.4
    ov = (f"drawtext=fontfile={NSQR}:text='AT NOWN':fontsize=92:fontcolor=white:"
          f"x=(w-text_w)/2:y=850:alpha='if(lt(t,1.1),t/1.1,if(gt(t,{OD-0.5}),({OD}-t)/0.5,1))',"
          f"drawtext=fontfile={NSQR}:text='창엽 부원장 · 커트의 정석':fontsize=36:fontcolor=0xF0D040:"
          f"x=(w-text_w)/2:y=978:alpha='if(lt(t,1.4),t/1.4,if(gt(t,{OD-0.5}),({OD}-t)/0.5,1))'")
    outro = f"{wd}/outro.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=black:s=1080x1920:d={OD}:r=30",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", str(OD), "-vf", ov,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", outro], check=True)
    final = f"{OUT}/창엽_{idx:02d}_{name}.mp4"
    open(f"{wd}/fc.txt", "w").write(f"file '{main}'\nfile '{outro}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{wd}/fc.txt",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", final], check=True)
    # 4) 업로드 + 로컬정리
    r = gdrive.upload_file(final, folder_id=DRIVE_FOLDER, name=f"창엽_{idx:02d}_{name}.mp4", overwrite=True, secrets_path="/home/user/-/secrets/gdrive.json")
    subprocess.run(["rm", "-rf", wd], check=False)
    print(f"✅ {idx:02d} {name} {DUR:.0f}s {len(cues)}큐 → {r.get('webViewLink','')}", flush=True)
    return r.get('webViewLink', '')


if __name__ == "__main__":
    a, b = int(sys.argv[1]), int(sys.argv[2])
    for i in range(a, b):
        if i == 0:
            continue  # 엘레강스는 완성본
        try:
            build_one(i, DS.access_token())
        except Exception as e:
            print(f"❌ {i} {SHORTS[i][0]}: {e}", flush=True)
    print("BATCH DONE", flush=True)
