#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""캡쳐시트.py — 영상 한 편을 균등 간격으로 캡처해 한 장으로. 컷 정보 없어도 된다.
   python3 scripts/캡쳐시트.py <mp4> <out.png> "<제목>" "<상태>"
"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
B = os.environ.get("ATNOWN_BASE") or os.path.expanduser("~/atnown-content-pipeline")
FONT = os.path.join(B, "assets/fonts/nsqr_eb.ttf")
BG,PN,LN=(13,15,18),(21,24,29),(39,44,53)
TX,DM,D2=(232,234,238),(143,151,165),(97,107,122)
CY,OK,WN,BD=(126,231,240),(95,211,154),(240,192,90),(240,123,123)
COLS,TW,TH,GAP,PAD,HEAD=6,190,338,10,26,132
def F(s): return ImageFont.truetype(FONT,s)
def pr(mp4,a):
    return subprocess.run(["ffprobe","-v","error"]+a+["-of","csv=p=0",mp4],
                          capture_output=True,text=True).stdout.strip()
def main():
    mp4,out,title,state = sys.argv[1],sys.argv[2],sys.argv[3],(sys.argv[4] if len(sys.argv)>4 else "")
    dur=float(pr(mp4,["-show_entries","format=duration"]) or 0)
    wh=pr(mp4,["-select_streams","v:0","-show_entries","stream=width,height"]).replace(",","×")
    hz=pr(mp4,["-select_streams","a:0","-show_entries","stream=sample_rate"])
    br=int(pr(mp4,["-show_entries","format=bit_rate"]) or 0)/1e6
    mb=os.path.getsize(mp4)/1048576
    n=18
    times=[dur*(i+0.5)/n for i in range(n)]
    rows=(n+COLS-1)//COLS
    W=PAD*2+COLS*TW+(COLS-1)*GAP
    H=HEAD+rows*(TH+22+GAP)+PAD
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    d.text((PAD,24),title,font=F(30),fill=TX)
    if state:
        col = OK if "가능" in state or "충족" in state else (BD if ("교체" in state or "초과" in state or "미달" in state) else WN)
        tw=d.textlength(state,font=F(17))
        d.rounded_rectangle([W-PAD-tw-26,24,W-PAD,60],9,fill=PN,outline=LN)
        d.text((W-PAD-tw-13,32),state,font=F(17),fill=col)
    items=[("길이","%.1f초"%dur, OK if 33<=dur<=48 else BD),
           ("해상도",wh, OK if wh=="1080×1920" else BD),
           ("오디오","%skHz"%(hz[:2] if hz else "?"), OK if hz=="48000" else BD),
           ("화질","%.1f Mbps"%br, OK if br>=8 else (WN if br>=4 else BD)),
           ("용량","%.1fMB"%mb, DM)]
    x=PAD
    for k,v,c in items:
        bw=max(int(d.textlength(v,font=F(19)))+30,int(d.textlength(k,font=F(13)))+30)
        d.rounded_rectangle([x,72,x+bw,120],8,fill=PN,outline=LN)
        d.text((x+13,79),k,font=F(13),fill=D2); d.text((x+13,95),v,font=F(19),fill=c)
        x+=bw+9
    for i,t in enumerate(times):
        cx=PAD+(i%COLS)*(TW+GAP); cy=HEAD+(i//COLS)*(TH+22+GAP)
        p="/tmp/_cap_%d.png"%i
        subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-ss","%.2f"%t,"-i",mp4,
                        "-frames:v","1","-vf","scale=%d:%d"%(TW,TH),p],capture_output=True)
        if os.path.exists(p): im.paste(Image.open(p).convert("RGB"),(cx,cy))
        d.text((cx+3,cy+TH+3),"%.1fs"%t,font=F(14),fill=D2)
    im.save(out,quality=92)
    print("%s (%dx%d)"%(out,W,H))
if __name__=="__main__": sys.exit(main())
