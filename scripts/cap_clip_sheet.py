#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""자막↔클립 대조표 — 비트마다 '무슨 그림 위에 무슨 글이 뜨는지'를 한 장으로 만든다.
왜(2026-08-10 형 지적: "자막이랑 클립이 안 맞는데 왜 쓰고 그래"):
게이트는 자막이 목소리와 맞는지, 검정이 몇 %인지는 잰다.
그런데 **이 자막이 지금 화면에 나오는 그림과 어울리는가**는 아무도 안 본다.
그건 의미 판단이라 픽셀로 못 잰다. 그래서 사람이 5초 만에 볼 수 있게 표로 만든다.
"""
import json, os, sys, subprocess
from PIL import Image, ImageDraw, ImageFont

MAC="/Users/chanho/atnown-content-pipeline"
HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def real(p): return p.replace(MAC,HERE) if p else p
FONT=os.path.join(HERE,"remotion","public","NanumSquareEB.ttf")

def sheet(job_path, out_path, cols=4, tw=300):
    j=json.load(open(job_path,encoding="utf-8"))
    d=real(j.get("clips_dir","")); beats=j.get("beats",[])
    th=int(tw*16/9); pad=8; texth=132
    rows=(len(beats)+cols-1)//cols
    W=cols*(tw+pad)+pad; H=rows*(th+texth+pad)+pad+40
    canvas=Image.new("RGB",(W,H),(13,13,15))
    dr=ImageDraw.Draw(canvas)
    try:
        f=ImageFont.truetype(FONT,19); fs=ImageFont.truetype(FONT,16); ft=ImageFont.truetype(FONT,24)
    except Exception:
        f=fs=ft=ImageFont.load_default()
    dr.text((pad,10),"%s — 자막↔클립 대조"%os.path.basename(job_path),font=ft,fill=(126,231,240))
    for i,b in enumerate(beats):
        cx=pad+(i%cols)*(tw+pad); cy=40+pad+(i//cols)*(th+texth+pad)
        if b.get("black"):
            dr.rectangle([cx,cy,cx+tw,cy+th],fill=(24,24,28),outline=(60,60,68))
            dr.text((cx+10,cy+th//2-10),"검정 화면",font=f,fill=(139,152,168))
        else:
            src=os.path.join(d,b.get("clip",""))
            tmp="/tmp/_cc%d.jpg"%i
            ss=float(b.get("start",0.5) or 0.5)
            subprocess.run(["ffmpeg","-y","-v","error","-ss","%.2f"%max(0.0,ss),"-i",src,
                            "-frames:v","1","-vf","scale=%d:%d"%(tw,th),tmp],capture_output=True)
            if os.path.exists(tmp):
                try: canvas.paste(Image.open(tmp),(cx,cy))
                except Exception: dr.rectangle([cx,cy,cx+tw,cy+th],fill=(50,20,20))
            else:
                dr.rectangle([cx,cy,cx+tw,cy+th],fill=(50,20,20))
                dr.text((cx+10,cy+10),"클립 없음: %s"%b.get("clip"),font=fs,fill=(240,123,123))
        ty=cy+th+6
        dr.text((cx,ty),"%d  %s"%(i,b.get("clip") or "BLACK"),font=fs,fill=(95,106,120)); ty+=22
        card=b.get("card")
        if card:
            for ln in (card if isinstance(card,list) else [card]):
                dr.text((cx,ty),"카드 "+ln[:20],font=f,fill=(126,231,240)); ty+=23
        cap=b.get("cap")
        if cap:
            dr.text((cx,ty),"자막 "+cap[:20],font=f,fill=(238,240,243)); ty+=23
        say=(b.get("say") or "")
        for k in range(0,min(len(say),40),20):
            dr.text((cx,ty),say[k:k+20],font=fs,fill=(139,152,168)); ty+=19
    canvas.save(out_path,quality=90)
    return out_path

if __name__=="__main__":
    for p in sys.argv[1:]:
        o="/tmp/capclip_%s.jpg"%os.path.basename(p).replace(".json","")
        print(sheet(p,o))
