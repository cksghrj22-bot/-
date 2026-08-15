import sys, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import nakta_post as N
ROOT=HERE.parents[1]; SRC=ROOT/"_clips_job"/"magic"
EDIT=ROOT/"_out"/"매직_오해_낙타캐러셀"/"_edit"; EDIT.mkdir(parents=True,exist_ok=True)
W,H=1080,1350
def F(sz): return ImageFont.truetype(str(HERE/"fonts"/"NanumSquareRoundEB.ttf"),sz)
def fit(t,size,x,maxw=W-36):
    s=size
    while s>30:
        f=F(s); bb=ImageDraw.Draw(Image.new("RGBA",(1,1))).textbbox((0,0),t,font=f)
        if x+(bb[2]-bb[0])+2*N.PAD_X<=maxw: return f
        s-=2
    return F(s)
def bar(d,x,y,t,role,size,full=False):
    box,txt=N.STYLES[role]; f=fit(t,size,x)
    bb=d.textbbox((0,0),t,font=f); tw,th=bb[2]-bb[0],bb[3]-bb[1]
    bw=(W-36-x) if full else tw+2*N.PAD_X; bh=th+2*N.PAD_Y
    d.rectangle([x,y,x+bw,y+bh],fill=box)
    d.text((x+N.PAD_X-bb[0],y+N.PAD_Y-bb[1]),t,font=f,fill=txt)
    return bh
def frame(src,ss,vf,out):
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-ss",str(ss),"-i",str(src),"-frames:v","1","-vf",vf,str(out)],check=True)
Q="전체매직·뿌리매직만?"; A="갯수가 수만 가지다. 사람마다 다르니까."
# OPTION A: zoom + crop-left to push the male stylist out
for wpx,y in ((1700,640),(1560,560)):
    vf=f"scale={wpx}:-2,crop=1080:1350:0:{y}"
    frame(SRC/"IMG_5853.MOV",7.5,vf,EDIT/f"b_A_{wpx}.png")
    im=Image.open(EDIT/f"b_A_{wpx}.png").convert("RGBA"); ov=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov)
    x0=int(W*0.05); yy=int(H*0.02); h1=bar(d,x0,yy,Q,"설정",58); yy+=h1+N.GAP; bar(d,x0+N.STEP,yy,A,"시안",40)
    Image.alpha_composite(im,ov).convert("RGB").save(EDIT/f"pA_{wpx}.jpg",quality=90)
# OPTION B: normal frame, cyan band full-width dropped over his face
vfB="scale=1080:1350:force_original_aspect_ratio=increase,crop=1080:1350"
frame(SRC/"IMG_5853.MOV",7.5,vfB,EDIT/"b_B.png")
im=Image.open(EDIT/"b_B.png").convert("RGBA"); ov=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov)
x0=int(W*0.05); yy=int(H*0.16); h1=bar(d,x0,yy,Q,"설정",58); yy+=h1+N.GAP; bar(d,x0+N.STEP,yy,A,"시안",44,full=True)
Image.alpha_composite(im,ov).convert("RGB").save(EDIT/"pB.jpg",quality=90)
print("OK")
