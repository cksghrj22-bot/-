#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""편별 「어느 B롤을 썼나」 한눈 시트 — 장면마다 대표 프레임 1장."""
import json, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "assets/fonts/nsqr_eb.ttf"
EPS = [("장마철떡짐","ep01"),("숏컷어울림","ep02"),("알아서해주세요","ep03"),("20년째","ep04"),
       ("도박끝내기","ep05"),("펌타버림","ep06"),("커트의본질","ep07"),("여름쿨톤","ep08"),("미용10년","ep09")]
CW, CH = 190, 338
def main():
    rows=[]
    for slug, tag in EPS:
        man = ROOT/("content/manifests/쇼츠_%s_20260818.json"%slug)
        vid = ROOT/("_out/shorts/%s_20260818.mp4"%slug)
        if not (man.exists() and vid.exists()): continue
        cuts=json.loads(man.read_text())["cuts"]
        seen=[]; scenes=[]
        for c in cuts:
            if c["scene"] in seen: continue
            seen.append(c["scene"]); scenes.append(c)
        rows.append((tag, slug, scenes, vid))
    if not rows: print("없음"); return 1
    ncol = max(len(r[2]) for r in rows)
    W = 210 + ncol*(CW+6) + 6; H = len(rows)*(CH+26) + 8
    sheet = Image.new("RGB",(W,H),(20,20,24)); d=ImageDraw.Draw(sheet)
    f  = ImageFont.truetype(str(FONT), 22); fs = ImageFont.truetype(str(FONT), 15)
    with tempfile.TemporaryDirectory() as td:
        for ri,(tag,slug,scenes,vid) in enumerate(rows):
            y = 4 + ri*(CH+26)
            d.text((8, y+CH//2-14), "%s %s"%(tag,slug), font=f, fill=(255,220,90))
            for ci,c in enumerate(scenes):
                t = (c["start"]+c["end"])/2
                png = "%s/%s_%d.jpg"%(td,tag,ci)
                subprocess.run(["ffmpeg","-v","error","-ss","%.2f"%t,"-i",str(vid),"-frames:v","1",
                                "-vf","scale=%d:-2"%CW,png,"-y"],capture_output=True)
                x = 206 + ci*(CW+6)
                if Path(png).exists():
                    im=Image.open(png); im.thumbnail((CW,CH)); sheet.paste(im,(x,y+22))
                lab = (c["clip"] or "검정카드").replace("_singular_display","").replace(".MOV","").replace(".mov","").replace(".mp4","")
                d.rectangle([x,y,x+CW,y+20], fill=(0,0,0))
                d.text((x+4,y+3), lab[:24], font=fs, fill=(150,230,255))
    out = ROOT/"_out/shorts/_전달/편별_소재시트.jpg"
    sheet.save(out, quality=85); print(out, sheet.size)
    return 0
sys.exit(main())
