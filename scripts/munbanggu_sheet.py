#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""문방구 수거분 확인 시트 — 폴더별로 묶어 클립당 1프레임.
차노 08-06 규약: 문방구 소스는 톤이 어긋날 수 있어 **쓰기 전 스샷으로 yes/no** 를 받는다."""
import json, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parent.parent
POOL = ROOT / "_clips_pool/문방구"
IDX  = ROOT / "_out/shorts/_문방구_재고.json"
FONT = ROOT / "assets/fonts/nsqr_eb.ttf"
CW, CH = 200, 300

def main():
    idx = {x["name"].replace("/","_"): (x.get("path") or "(루트)") for x in json.loads(IDX.read_text())}
    files = sorted([p for p in POOL.iterdir() if p.suffix.lower() in (".mov",".mp4")])
    groups = {}
    for p in files: groups.setdefault(idx.get(p.name, "(미상)"), []).append(p)
    order = sorted(groups, key=lambda k: -len(groups[k]))
    C = 7
    rows = sum((len(groups[g]) + C - 1)//C for g in order)
    H = rows*(CH+8) + len(order)*34 + 10
    W = C*(CW+6) + 10
    sheet = Image.new("RGB", (W,H), (18,18,22)); d = ImageDraw.Draw(sheet)
    fg = ImageFont.truetype(str(FONT), 24); fs = ImageFont.truetype(str(FONT), 14)
    y = 6
    with tempfile.TemporaryDirectory() as td:
        for g in order:
            d.rectangle([0,y,W,y+30], fill=(45,45,60))
            d.text((8,y+5), "%s  (%d개)"%(g, len(groups[g])), font=fg, fill=(255,225,120)); y += 34
            for i,p in enumerate(groups[g]):
                if i and i % C == 0: y += CH+8
                x = 6 + (i % C)*(CW+6)
                png = "%s/%d.jpg"%(td, i)
                subprocess.run(["ffmpeg","-v","error","-ss","2","-i",str(p),"-frames:v","1",
                                "-vf","scale=%d:-2"%CW,png,"-y"],capture_output=True)
                if Path(png).exists():
                    im=Image.open(png); im.thumbnail((CW,CH-18)); sheet.paste(im,(x,y+18))
                d.rectangle([x,y,x+CW,y+16], fill=(0,0,0))
                d.text((x+3,y+1), p.stem[:26], font=fs, fill=(150,230,255))
            y += CH+8
    out = ROOT/"_out/shorts/_전달/문방구_확인시트.jpg"
    sheet.save(out, quality=80); print(out, sheet.size, len(files))
    return 0
sys.exit(main())
