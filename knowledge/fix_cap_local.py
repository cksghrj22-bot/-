"""자막-ONLY 정정 오버레이: v3 로컬본에 정정 전사로 만든 자막을 다시 얹는다.
SUB 박스가 완전 불투명(box_opacity=100)이라 옛 자막을 정확히 덮음(같은 위치·시간). 제목·아웃트로는 그대로.
전사 오타 교정 후(예: orig_9004 디스코넥션→디스커넥션) 스트리밍 없이 로컬로 반영. 사용: python3 fix_cap_local.py <idx...>
"""
import sys, os, json, subprocess
sys.path.insert(0, '/home/user/-'); sys.path.insert(0, os.path.dirname(__file__))
import shorts.shortstyle as SS
from shorts.creator_short import _wrap2, _style, _ts, CANVAS
from shorts import gdrive
from manifest30 import SHORTS
HERE=os.path.dirname(__file__); OUT=f"{HERE}/final30"; FOLDER="1mchAPVsCAluJv3uGDvFdGM0LEg4hlEo4"
POS = r"{\an5\pos(540,1640)}"


def cues_from(words, keeps):
    def remap(t):
        acc=0.0
        for (oa,ob) in keeps:
            if oa<=t<=ob: return acc+(t-oa)
            acc+=ob-oa
        return acc
    kept=[w for w in words if any(oa<=w['start']<=ob for oa,ob in keeps)]
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


def fix(idx):
    name, clip, keeps, _ = SHORTS[idx]
    src=f"{OUT}/창엽_{idx:02d}_{name}.mp4"
    if not os.path.exists(src): print(f"❌ {idx} 로컬본 없음", flush=True); return
    words=json.load(open(f"{HERE}/orig_{clip}.words.json"))
    cues=cues_from(words, keeps)
    head=(f"[Script Info]\nScriptType: v4.00+\nPlayResX: {CANVAS[0]}\nPlayResY: {CANVAS[1]}\n"
          f"WrapStyle: 0\nScaledBorderAndShadow: yes\n[V4+ Styles]\n"
          "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, "
          "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
          "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
          f"{_style('cap', SS.SUB)}\n[Events]\n"
          "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    body="".join(f"Dialogue: 0,{_ts(s)},{_ts(e)},cap,,0,0,0,,{POS}{ko}\n" for s,e,ko in cues)
    ass=f"{OUT}/_fc_{idx}.ass"; open(ass,"w",encoding="utf-8").write(head+body)
    vf=f"subtitles={ass}"  # 불투명 자막박스가 옛 자막 완전 커버
    tmp=f"{OUT}/_fc_{idx}.mp4"
    subprocess.run(["ffmpeg","-v","error","-y","-i",src,"-vf",vf,"-c:v","libx264","-preset","slow",
        "-crf","16","-pix_fmt","yuv420p","-r","30","-c:a","copy",tmp],check=True)
    os.replace(tmp,src); os.remove(ass)
    r=gdrive.upload_file(src,folder_id=FOLDER,name=f"창엽_{idx:02d}_{name}.mp4",overwrite=True,secrets_path="/home/user/-/secrets/gdrive.json")
    print(f"✅ {idx:02d} {name} 자막정정 {len(cues)}큐 → {r.get('webViewLink','')}",flush=True)


if __name__=="__main__":
    for i in [int(x) for x in sys.argv[1:]]:
        try: fix(i)
        except Exception as e: print(f"❌ {i}: {e}",flush=True)
    print("DONE",flush=True)
