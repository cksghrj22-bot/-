import sys, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import nakta_post as N
ROOT=HERE.parents[1]
SRC=ROOT/"_clips_job"/"magic"
OUT=ROOT/"_out"/"매직_오해_낙타캐러셀"
EDIT=OUT/"_edit"; EDIT.mkdir(parents=True,exist_ok=True)
W,H=1080,1350
def F(sz): return ImageFont.truetype(str(HERE/"fonts"/"NanumSquareRoundEB.ttf"),sz)
def fit(text,size,x):
    s=size
    while s>30:
        f=F(s); bb=ImageDraw.Draw(Image.new("RGBA",(1,1))).textbbox((0,0),text,font=f)
        if x+(bb[2]-bb[0])+2*N.PAD_X<=W-36: return f
        s-=2
    return F(s)
def overlay(lines,text_left,text_top):
    ov=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov)
    x0=int(W*text_left); y=int(H*text_top)
    for i,(role,text,size) in enumerate(lines):
        box,txt=N.STYLES[role]; bx=x0+i*N.STEP; f=fit(text,size,bx)
        bb=d.textbbox((0,0),text,font=f); tw,th=bb[2]-bb[0],bb[3]-bb[1]
        bw=tw+2*N.PAD_X; bh=th+2*N.PAD_Y
        d.rectangle([bx,y,bx+bw,y+bh],fill=box)
        d.text((bx+N.PAD_X-bb[0],y+N.PAD_Y-bb[1]),text,font=f,fill=txt)
        y+=bh+N.GAP
    return ov
def frame(src,ss,vf,out):
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-ss",str(ss),"-i",str(src),"-frames:v","1","-vf",vf,str(out)],check=True)
# SLIDE 1: contain + blurred fill (less zoom, centered)
vf1=("split[a][b];[a]scale=1080:1350:force_original_aspect_ratio=increase,crop=1080:1350,boxblur=26:2,eq=brightness=-0.05[bg];"
     "[b]scale=1080:1350:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2")
frame(SRC/"사랑해.MOV",1.0,vf1,EDIT/"b1.png")
b=Image.open(EDIT/"b1.png").convert("RGBA")
Image.alpha_composite(b,overlay([("설정","여름철 곱슬 때문에 힘드시죠?",66)],0.050,0.070)).convert("RGB").save(EDIT/"p1.jpg",quality=90)
# SLIDE 4: pan left to drop the male stylist
for panx in (300,440):
    vf4=f"scale=1080:1350:force_original_aspect_ratio=increase,crop=1080:1350:{panx}:0"
    frame(SRC/"IMG_5853.MOV",7.5,vf4,EDIT/f"b4_{panx}.png")
    b=Image.open(EDIT/f"b4_{panx}.png").convert("RGBA")
    Image.alpha_composite(b,overlay([("설정","전체매직·뿌리매직만?",58),("시안","갯수가 수만 가지다. 사람마다 다르니까.",40)],0.050,0.020)).convert("RGB").save(EDIT/f"p4_{panx}.jpg",quality=90)
print("OK", list(p.name for p in EDIT.glob("p*.jpg")))
