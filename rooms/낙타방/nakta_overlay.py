#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""낙타 자막바 오버레이 PNG 생성 — 영상 슬라이드용.
그리기 수치는 공유 정본 scripts/cards/nakta_post.py 상수를 그대로 읽어 쓴다. 여기서 새로 정하지 않는다.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts" / "cards"))
from PIL import Image, ImageDraw
import nakta_post as N

def overlay(lines, out, size=58, top=0.30, left=0.07):
    ov = Image.new("RGBA", (N.W, N.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    x0 = int(N.W * left); y = int(N.H * top)
    for i, (role, text) in enumerate(lines):
        if not text: continue
        box, txt = N.STYLES.get(role, N.STYLES["설정"])
        bx = x0 + i * N.STEP
        fnt = N._fit_font(text, role, size, bx)
        bb = d.textbbox((0, 0), text, font=fnt)
        tw, th = bb[2]-bb[0], bb[3]-bb[1]
        bw, bh = tw + 2*N.PAD_X, th + 2*N.PAD_Y
        d.rectangle([bx, y, bx+bw, y+bh], fill=box)
        d.text((bx + N.PAD_X - bb[0], y + N.PAD_Y - bb[1]), text, font=fnt, fill=txt)
        y += bh + N.GAP
    ov.save(out); return out
