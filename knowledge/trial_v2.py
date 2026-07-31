"""트라이얼 v2(형 2026-07-31): 노란 제목만·하단자막 제거·화질개선(crf16·concat 무재인코딩·dim0).
keep concat/final concat는 -c copy로 세대손실 제거. 사용: python3 trial_v2.py <idx...>
"""
import sys, os, subprocess
sys.path.insert(0, '/home/user/-'); sys.path.insert(0, os.path.dirname(__file__))
import shorts.shortstyle as SS
from shorts.creator_short import _style, _ts, WARM, CANVAS
from shorts import drive_stream as DS, gdrive
from manifest30 import SHORTS, ORIG
from titles import TITLES
REPO="/home/user/-"; HERE=os.path.dirname(__file__); NSQR="/root/.fonts/nsqr_eb.ttf"
OUT=f"{HERE}/final30"; FOLDER="1mchAPVsCAluJv3uGDvFdGM0LEg4hlEo4"; VY=460


def yellow_title(ty, tw):
    # 전부 노랑(흰 없음), 2줄이면 둘 다 노랑
    return f"{SS.POP_YELLOW}{ty}" + (f"\\N{SS.POP_YELLOW}{tw}" if tw else "")


def build(idx, tok):
    name, clip, keeps, _ = SHORTS[idx]; ty, tw = TITLES[idx]
    wd=f"{HERE}/_v2_{idx}"; os.makedirs(wd, exist_ok=True)
    fid=ORIG[clip]
    # 1) keep 개별추출(crf16 medium)→concat COPY(무재인코딩)
    parts=[]
    for k,(oa,ob) in enumerate(keeps):
        p=f"{wd}/k{k:02d}.mp4"
        for attempt in range(4):
            t2 = tok if attempt==0 else DS.access_token()
            r=subprocess.run(["ffmpeg","-v","error","-headers",f"Authorization: Bearer {t2}\r\n",
                "-ss",f"{oa:.3f}","-i",f"https://www.googleapis.com/drive/v3/files/{fid}?alt=media","-t",f"{ob-oa:.3f}",
                "-vf","crop=2160:2160:840:0,scale=1080:1080,fps=30,setsar=1","-c:v","libx264","-preset","medium",
                "-crf","16","-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","192k","-y",p],timeout=600)
            if r.returncode==0: break
            import time as _t; _t.sleep(2*(attempt+1))
        else:
            raise RuntimeError(f"extract 실패 {fid} {oa}-{ob}")
        parts.append(p)
    open(f"{wd}/cc.txt","w").write("".join(f"file '{p}'\n" for p in parts))
    joined=f"{wd}/joined.mp4"
    subprocess.run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",f"{wd}/cc.txt","-c","copy",joined],check=True)
    DUR=sum(ob-oa for oa,ob in keeps)
    # 2) 제목=노란색만(가운데), 자막 없음. dim 제거(밝게).
    head=(f"[Script Info]\nScriptType: v4.00+\nPlayResX: {CANVAS[0]}\nPlayResY: {CANVAS[1]}\n"
          f"WrapStyle: 0\nScaledBorderAndShadow: yes\n[V4+ Styles]\n"
          "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, "
          "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
          "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
          f"{_style('title', SS.POP_TITLE)}\n[Events]\n"
          "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
          f"Dialogue: 0,{_ts(0)},{_ts(DUR)},title,,0,0,0,,{yellow_title(ty,tw)}\n")
    ass=f"{wd}/s.ass"; open(ass,"w",encoding="utf-8").write(head)
    vf=(f"[0:v]{WARM},scale=1080:1080,setsar=1[v];"
        f"color=c=black:s={CANVAS[0]}x{CANVAS[1]}:d={DUR}[bg];[bg][v]overlay=0:{VY}[b1];"
        f"[b1]subtitles={ass},fade=t=out:st={DUR-0.6}:d=0.6[vout];"
        f"[0:a]highpass=f=95[vo];[1:a]volume=0.14,afade=t=out:st={DUR-1.5}:d=1.5[bgm];"
        f"[vo][bgm]amix=inputs=2:duration=first:dropout_transition=0,afade=t=out:st={DUR-0.8}:d=0.8[aout]")
    main=f"{wd}/main.mp4"
    subprocess.run(["ffmpeg","-v","error","-y","-i",joined,"-i",f"{REPO}/shorts/assets/bgm_piano_long.mp3",
        "-filter_complex",vf,"-map","[vout]","-map","[aout]","-c:v","libx264","-preset","slow","-crf","16",
        "-pix_fmt","yuv420p","-r","30","-c:a","aac","-b:a","192k","-shortest",main],check=True)
    # 3) 아웃트로(crf16)
    OD=3.4
    ov=(f"drawtext=fontfile={NSQR}:text='AT NOWN':fontsize=92:fontcolor=white:x=(w-text_w)/2:y=850:"
        f"alpha='if(lt(t,1.1),t/1.1,if(gt(t,{OD-0.5}),({OD}-t)/0.5,1))',"
        f"drawtext=fontfile={NSQR}:text='창엽 부원장 · 커트의 정석':fontsize=36:fontcolor=0xF0D040:x=(w-text_w)/2:y=978:"
        f"alpha='if(lt(t,1.4),t/1.4,if(gt(t,{OD-0.5}),({OD}-t)/0.5,1))'")
    outro=f"{wd}/outro.mp4"
    subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi","-i",f"color=black:s=1080x1920:d={OD}:r=30",
        "-f","lavfi","-i","anullsrc=r=44100:cl=stereo","-t",str(OD),"-vf",ov,"-c:v","libx264","-pix_fmt","yuv420p",
        "-crf","16","-r","30","-c:a","aac","-b:a","192k","-shortest",outro],check=True)
    final=f"{OUT}/창엽_{idx:02d}_{name}.mp4"
    open(f"{wd}/fc.txt","w").write(f"file '{main}'\nfile '{outro}'\n")
    subprocess.run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",f"{wd}/fc.txt","-c","copy",final],check=True)
    r=gdrive.upload_file(final,folder_id=FOLDER,name=f"창엽_{idx:02d}_{name}.mp4",overwrite=True,secrets_path="/home/user/-/secrets/gdrive.json")
    subprocess.run(["rm","-rf",wd],check=False)
    print(f"✅ {idx:02d} {name} {DUR:.0f}s → {r.get('webViewLink','')}",flush=True)


if __name__=="__main__":
    for i in [int(x) for x in sys.argv[1:]]:
        try: build(i, DS.access_token())
        except Exception as e: print(f"❌ {i}: {e}",flush=True)
    print("DONE",flush=True)
