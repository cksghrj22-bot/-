import sys, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import nakta_post as N
ROOT=HERE.parents[1]; SRC=ROOT/"_clips_job"/"magic"; OUT=ROOT/"_out"/"매직_오해_낙타캐러셀"
(OUT/"_edit").mkdir(parents=True,exist_ok=True); W,H=1080,1350
FILE=SRC/"밸런스베이지.MOV"
def F(sz): return ImageFont.truetype(str(HERE/"fonts"/"NanumSquareRoundEB.ttf"),sz)
def fit(t,size,x):
    s=size
    while s>30:
        f=F(s); bb=ImageDraw.Draw(Image.new("RGBA",(1,1))).textbbox((0,0),t,font=f)
        if x+(bb[2]-bb[0])+2*N.PAD_X<=W-36: return f
        s-=2
    return F(s)
def overlay(lines,tl,tt,out):
    ov=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov); x0=int(W*tl); y=int(H*tt)
    for i,(role,t,size) in enumerate(lines):
        box,txt=N.STYLES[role]; bx=x0+i*N.STEP; f=fit(t,size,bx)
        bb=d.textbbox((0,0),t,font=f); tw,th=bb[2]-bb[0],bb[3]-bb[1]
        d.rectangle([bx,y,bx+tw+2*N.PAD_X,y+th+2*N.PAD_Y],fill=box)
        d.text((bx+N.PAD_X-bb[0],y+N.PAD_Y-bb[1]),t,font=f,fill=txt); y+=th+2*N.PAD_Y+N.GAP
    ov.save(out); return out
def dur(f):
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nk=1:nw=1",str(f)],capture_output=True,text=True)
    try: return float(r.stdout.strip())
    except: return 0.0
assert FILE.exists(), f"source missing: {FILE}"
D=dur(FILE); T=5.0; ss=max(0.0,min(1.2,D-T-0.2)) if D>T+0.4 else 0.0
ov=overlay([("설정","매직은 잘 펴는 것?",62),("결론","불필요한 곱슬을 찾는 것이다.",44)],0.045,0.090,OUT/"_edit"/"ov3.png")
vf=("[0:v]scale=1080:1350:force_original_aspect_ratio=increase,crop=1080:1350:(iw-ow)/2:(ih-oh)*0.05,setsar=1[base];"
    "[base][1:v]overlay=0:0,format=yuv420p[v]")
subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-ss",f"{ss:.3f}","-t",f"{T:.3f}","-i",str(FILE),"-i",str(ov),
 "-filter_complex",vf,"-map","[v]","-an","-c:v","libx264","-crf","18","-preset","veryfast","-movflags","+faststart",str(OUT/"slide_3.mp4")],check=True)
print("OK", OUT/"slide_3.mp4")
