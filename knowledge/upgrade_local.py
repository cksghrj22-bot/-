"""v2 로컬본(제목상단·자막없음) → v3 규격(제목 중앙 + 하단 자막)으로 로컬 합성.
9006 4K 스트리밍이 계속 실패해 재추출 불가 → 이미 있는 4K 로컬본을 재가공(1세대 손실 crf16).
상단밴드(0~460)에 옛 제목이 구워져 있음 → drawbox로 덮고(본편 구간만) 중앙 제목+자막 얹음. 아웃트로는 건드리지 않음.
사용: python3 upgrade_local.py <idx...>
"""
import sys, os, json, subprocess
sys.path.insert(0, '/home/user/-'); sys.path.insert(0, os.path.dirname(__file__))
import shorts.shortstyle as SS
from shorts.creator_short import _wrap2, _style, _ts, CANVAS
from shorts import gdrive
from manifest30 import SHORTS, ORIG
from titles import TITLES
HERE=os.path.dirname(__file__); OUT=f"{HERE}/final30"; FOLDER="1mchAPVsCAluJv3uGDvFdGM0LEg4hlEo4"
TPOS = r"{\an5\pos(540,230)}"; POS = r"{\an5\pos(540,1640)}"


def yellow_title(ty, tw):
    return f"{SS.POP_YELLOW}{ty}" + (f"\\N{SS.POP_YELLOW}{tw}" if tw else "")


def cues_from(words, keeps):
    def remap(t):
        acc = 0.0
        for (oa, ob) in keeps:
            if oa <= t <= ob: return acc + (t - oa)
            acc += ob - oa
        return acc
    kept = [w for w in words if any(oa <= w['start'] <= ob for oa, ob in keeps)]
    cues=[]; cur=[]
    END=('.', '?', '!', '요', '다', '까', '고', '든', '야', '죠', '네', '지')
    def flush(pad):
        ws=[c['text'].strip() for c in cur if c['text'].strip()]
        if ws: cues.append((round(remap(cur[0]['start']),2), round(remap(cur[-1]['end'])+pad,2), _wrap2(ws)))
    for i,x in enumerate(kept):
        cur.append(x); j=' '.join(c['text'] for c in cur); d=cur[-1]['end']-cur[0]['start']; t=x['text'].strip()
        boundary=(i+1<len(kept)) and remap(kept[i+1]['start'])-remap(x['end'])>0.25
        if (t and t[-1] in END) or len(j)>=22 or d>=3.6 or boundary: flush(0.35); cur=[]
    if cur: flush(0.5)
    fixed=[]
    for i,(s,e,ko) in enumerate(cues):
        if i+1<len(cues): e=min(e,cues[i+1][0]-0.05)
        if e-s>=0.4: fixed.append((s,e,ko))
    return fixed


def upgrade(idx):
    name, clip, keeps, _ = SHORTS[idx]; ty, tw = TITLES[idx]
    src=f"{OUT}/창엽_{idx:02d}_{name}.mp4"
    if not os.path.exists(src): print(f"❌ {idx} 로컬본 없음", flush=True); return
    words=json.load(open(f"{HERE}/orig_{clip}.words.json"))
    DB=sum(ob-oa for oa,ob in keeps)  # 본편 길이(제목·자막 이 구간까지)
    cues=cues_from(words, keeps)
    head=(f"[Script Info]\nScriptType: v4.00+\nPlayResX: {CANVAS[0]}\nPlayResY: {CANVAS[1]}\n"
          f"WrapStyle: 0\nScaledBorderAndShadow: yes\n[V4+ Styles]\n"
          "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, "
          "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
          "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
          f"{_style('title', SS.POP_TITLE)}\n{_style('cap', SS.SUB)}\n[Events]\n"
          "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
          f"Dialogue: 0,{_ts(0)},{_ts(DB)},title,,0,0,0,,{TPOS}{yellow_title(ty,tw)}\n")
    body="".join(f"Dialogue: 0,{_ts(s)},{_ts(e)},cap,,0,0,0,,{POS}{ko}\n" for s,e,ko in cues)
    ass=f"{OUT}/_up_{idx}.ass"; open(ass,"w",encoding="utf-8").write(head+body)
    # 상단밴드 옛제목 덮기(본편 구간만)+중앙제목·자막. 오디오는 그대로.
    vf=f"drawbox=x=0:y=0:w={CANVAS[0]}:h=460:color=black:t=fill:enable='lt(t,{DB})',subtitles={ass}"
    tmp=f"{OUT}/_up_{idx}.mp4"
    subprocess.run(["ffmpeg","-v","error","-y","-i",src,"-vf",vf,"-c:v","libx264","-preset","slow",
        "-crf","16","-pix_fmt","yuv420p","-r","30","-c:a","copy",tmp],check=True)
    os.replace(tmp,src); os.remove(ass)
    r=gdrive.upload_file(src,folder_id=FOLDER,name=f"창엽_{idx:02d}_{name}.mp4",overwrite=True,secrets_path="/home/user/-/secrets/gdrive.json")
    print(f"✅ {idx:02d} {name} {DB:.0f}s {len(cues)}자막(로컬합성) → {r.get('webViewLink','')}",flush=True)


if __name__=="__main__":
    for i in [int(x) for x in sys.argv[1:]]:
        try: upgrade(i)
        except Exception as e: print(f"❌ {i}: {e}",flush=True)
    print("DONE",flush=True)
