"""기존 final30에 짧은 새 제목 덮어씌우기 + 아웃트로 트랜지션 오디오 페이드 + 하이패스.
4K 재추출 없음(완성본 재가공). 사용: python3 fix_titles.py <idx...>  (없으면 0~29 전체)
"""
import sys, os, subprocess
sys.path.insert(0, '/home/user/-'); sys.path.insert(0, os.path.dirname(__file__))
import shorts.shortstyle as SS
from shorts.creator_short import _style, _ts, CANVAS
from shorts import gdrive
from manifest30 import SHORTS
from titles import TITLES

HERE = os.path.dirname(__file__); OUT = f"{HERE}/final30"; FOLDER = "1mchAPVsCAluJv3uGDvFdGM0LEg4hlEo4"


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip())


def fix(idx):
    name, clip, keeps, _ = SHORTS[idx]
    md = sum(ob - oa for oa, ob in keeps)  # 본편 끝(제목은 여기까지만)
    ty, tw = TITLES[idx]
    src = f"{OUT}/창엽_{idx:02d}_{name}.mp4"
    if not os.path.exists(src):
        print(f"skip {idx} 없음"); return
    D = dur(src)
    head = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {CANVAS[0]}\nPlayResY: {CANVAS[1]}\n"
            f"WrapStyle: 0\nScaledBorderAndShadow: yes\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, "
            "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
            "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"{_style('title', SS.POP_TITLE)}\n[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            f"Dialogue: 0,{_ts(0)},{_ts(md)},title,,0,0,0,,{SS.pop_title(ty, tw)}\n")
    ass = f"{OUT}/_ttl_{idx}.ass"; open(ass, "w", encoding="utf-8").write(head)
    tmp = f"{OUT}/_o{idx}.mp4"
    vf = f"drawbox=x=0:y=0:w={CANVAS[0]}:h=456:color=black:t=fill,subtitles={ass}"
    af = f"highpass=f=95,afade=t=out:st={md-0.8:.3f}:d=0.8"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", vf, "-af", af,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", tmp], check=True)
    os.replace(tmp, src); os.remove(ass)
    r = gdrive.upload_file(src, folder_id=FOLDER, name=f"창엽_{idx:02d}_{name}.mp4",
                           overwrite=True, secrets_path="/home/user/-/secrets/gdrive.json")
    print(f"✅ {idx:02d} {name} 제목='{ty}/{tw}' → {r.get('webViewLink','')}", flush=True)


if __name__ == "__main__":
    idxs = [int(x) for x in sys.argv[1:]] or list(range(0, 30))
    for i in idxs:
        try:
            fix(i)
        except Exception as e:
            print(f"❌ {i}: {e}", flush=True)
    print("FIX DONE", flush=True)
