import sys, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import nakta_post as N
ROOT=HERE.parents[1]; SRC=ROOT/"_clips_job"/"magic"; OUT=ROOT/"_out"/"매직_오해_낙타캐러셀"
EDIT=OUT/"_edit"; W,H=1080,1350
def F(sz): return ImageFont.truetype(str(HERE/"fonts"/"NanumSquareRoundEB.ttf"),sz)
def fit(t,size,x):
    s=size
    while s>30:
        f=F(s); bb=ImageDraw.Draw(Image.new("RGBA",(1,1))).textbbox((0,0),t,font=f)
        if x+(bb[2]-bb[0])+2*N.PAD_X<=W-36: return f
        s-=2
    return F(s)
def ovl(lines,tl,tt,out):
    ov=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov); x0=int(W*tl); y=int(H*tt)
    for i,(role,t,size) in enumerate(lines):
        box,txt=N.STYLES[role]; bx=x0+i*N.STEP; f=fit(t,size,bx)
        bb=d.textbbox((0,0),t,font=f); tw,th=bb[2]-bb[0],bb[3]-bb[1]
        d.rectangle([bx,y,bx+tw+2*N.PAD_X,y+th+2*N.PAD_Y],fill=box)
        d.text((bx+N.PAD_X-bb[0],y+N.PAD_Y-bb[1]),t,font=f,fill=txt); y+=th+2*N.PAD_Y+N.GAP
    ov.save(out); return out
ov1=ovl([("설정","여름철 곱슬 때문에 힘드시죠?",66)],0.05,0.07,EDIT/"ov1.png")
ov4=ovl([("설정","전체매직·뿌리매직만?",58),("시안","갯수가 수만 가지다. 사람마다 다르니까.",40)],0.05,0.02,EDIT/"ov4.png")
def run(c): subprocess.run(c,check=True)
# slide 1
run(["ffmpeg","-y","-hide_banner","-loglevel","error","-ss","0","-t","4","-i",str(SRC/"사랑해.MOV"),"-i",str(ov1),
 "-filter_complex","[0:v]split[a][b];[a]scale=1080:1350:force_original_aspect_ratio=increase,crop=1080:1350,boxblur=26:2,eq=brightness=-0.05[bg];[b]scale=1080:1350:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2[base];[base][1:v]overlay=0:0,format=yuv420p[v]",
 "-map","[v]","-an","-c:v","libx264","-crf","18","-preset","veryfast","-movflags","+faststart",str(OUT/"slide_1.mp4")])
print("slide_1 done")
