import sys, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import nakta_post as N
ROOT=HERE.parents[1]; SRC=ROOT/"_clips_job"/"magic"
EDIT=ROOT/"_out"/"매직_오해_낙타캐러셀"/"_edit"; EDIT.mkdir(parents=True,exist_ok=True)
W,H=1080,1350
def F(sz): return ImageFont.truetype(str(HERE/"fonts"/"NanumSquareRoundEB.ttf"),sz)
def fit(t,size,x):
    s=size
    while s>30:
        f=F(s); bb=ImageDraw.Draw(Image.new("RGBA",(1,1))).textbbox((0,0),t,font=f)
        if x+(bb[2]-bb[0])+2*N.PAD_X<=W-36: return f
        s-=2
    return F(s)
def overlay(lines,tl,tt):
    ov=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov); x0=int(W*tl); y=int(H*tt)
    for i,(role,t,size) in enumerate(lines):
        box,txt=N.STYLES[role]; bx=x0+i*N.STEP; f=fit(t,size,bx)
        bb=d.textbbox((0,0),t,font=f); tw,th=bb[2]-bb[0],bb[3]-bb[1]
        bw=tw+2*N.PAD_X; bh=th+2*N.PAD_Y
        d.rectangle([bx,y,bx+bw,y+bh],fill=box)
        d.text((bx+N.PAD_X-bb[0],y+N.PAD_Y-bb[1]),t,font=f,fill=txt); y+=bh+N.GAP
    return ov
def frame(src,ss,vf,out):
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-ss",str(ss),"-i",str(src),"-frames:v","1","-vf",vf,str(out)],check=True)
# scale to height 1350 (=>2400 wide), then crop 1080 wide at x
for x in (200,340):
    vf=f"scale=-2:1350,crop=1080:1350:{x}:0"
    frame(SRC/"IMG_5853.MOV",7.5,vf,EDIT/f"b4x_{x}.png")
    b=Image.open(EDIT/f"b4x_{x}.png").convert("RGBA")
    Image.alpha_composite(b,overlay([("설정","전체매직·뿌리매직만?",58),("시안","갯수가 수만 가지다. 사람마다 다르니까.",40)],0.050,0.020)).convert("RGB").save(EDIT/f"p4x_{x}.jpg",quality=90)
print("OK")
