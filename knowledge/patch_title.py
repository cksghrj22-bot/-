"""제목-ONLY 교체 패치: v3 로컬본(자막 이미 구움)에서 상단밴드 옛 제목만 덮고 새 노랑 제목 얹음.
자막은 손대지 않음(중복 방지). 형이 미정 제목(17·20·21·22·24·25·29 등)을 주면 titles.py 갱신 후 이 툴로 해당 편만 덮어씌운다.
사용: 1) titles.py의 TITLES[idx] 수정 → 2) python3 patch_title.py <idx...>
"""
import sys, os, subprocess
sys.path.insert(0, '/home/user/-'); sys.path.insert(0, os.path.dirname(__file__))
import shorts.shortstyle as SS
from shorts.creator_short import _style, _ts, CANVAS
from shorts import gdrive
from manifest30 import SHORTS
from titles import TITLES
HERE=os.path.dirname(__file__); OUT=f"{HERE}/final30"; FOLDER="1mchAPVsCAluJv3uGDvFdGM0LEg4hlEo4"
TPOS = r"{\an5\pos(540,230)}"


def yellow_title(ty, tw):
    return f"{SS.POP_YELLOW}{ty}" + (f"\\N{SS.POP_YELLOW}{tw}" if tw else "")


def patch(idx):
    name, clip, keeps, _ = SHORTS[idx]; ty, tw = TITLES[idx]
    src=f"{OUT}/창엽_{idx:02d}_{name}.mp4"
    if not os.path.exists(src): print(f"❌ {idx} 로컬본 없음", flush=True); return
    DB=sum(ob-oa for oa,ob in keeps)  # 본편 길이(제목 이 구간까지·아웃트로 보호)
    head=(f"[Script Info]\nScriptType: v4.00+\nPlayResX: {CANVAS[0]}\nPlayResY: {CANVAS[1]}\n"
          f"WrapStyle: 0\nScaledBorderAndShadow: yes\n[V4+ Styles]\n"
          "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, "
          "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
          "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
          f"{_style('title', SS.POP_TITLE)}\n[Events]\n"
          "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
          f"Dialogue: 0,{_ts(0)},{_ts(DB)},title,,0,0,0,,{TPOS}{yellow_title(ty,tw)}\n")
    ass=f"{OUT}/_pt_{idx}.ass"; open(ass,"w",encoding="utf-8").write(head)
    # 상단밴드(0~460) 옛제목만 덮기(본편 구간)+새 제목. 자막(하단)·아웃트로는 그대로.
    vf=f"drawbox=x=0:y=0:w={CANVAS[0]}:h=460:color=black:t=fill:enable='lt(t,{DB})',subtitles={ass}"
    tmp=f"{OUT}/_pt_{idx}.mp4"
    subprocess.run(["ffmpeg","-v","error","-y","-i",src,"-vf",vf,"-c:v","libx264","-preset","slow",
        "-crf","16","-pix_fmt","yuv420p","-r","30","-c:a","copy",tmp],check=True)
    os.replace(tmp,src); os.remove(ass)
    r=gdrive.upload_file(src,folder_id=FOLDER,name=f"창엽_{idx:02d}_{name}.mp4",overwrite=True,secrets_path="/home/user/-/secrets/gdrive.json")
    print(f"✅ {idx:02d} {name} 제목='{ty} {tw}' 교체 → {r.get('webViewLink','')}",flush=True)


if __name__=="__main__":
    for i in [int(x) for x in sys.argv[1:]]:
        try: patch(i)
        except Exception as e: print(f"❌ {i}: {e}",flush=True)
    print("DONE",flush=True)
