#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""앳나운 만화카드 공통 틀 — 긴얼굴형 시리즈와 같은 규격.

가시성 최우선: 큰 제목, 굵은 선, 여백 크게. 한 장에 한 가지만.
"""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 2160, 2700
BG = (251, 251, 249)
INK = (26, 26, 26)
GRAY = (150, 150, 154)
CY = (126, 226, 240)
M = 156

_FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
def _rf(name, linux):
    p = os.path.join(_FD, name)
    return p if os.path.exists(p) else linux
EB = _rf("NanumSquareRoundEB.ttf", "/usr/share/fonts/truetype/nanum/NanumSquareRoundEB.ttf")
RB = _rf("NanumSquareRoundB.ttf", "/usr/share/fonts/truetype/nanum/NanumSquareRoundB.ttf")
PEN = _rf("NanumPen.ttf", "/usr/share/fonts/truetype/nanum/NanumPen.ttf")
F = lambda p, s: ImageFont.truetype(p, s)


def new():
    im = Image.new("RGB", (W, H), BG)
    return im, ImageDraw.Draw(im)


def head(d, series, page):
    d.text((M, 96), series, font=F(RB, 62), fill=(46, 46, 46))
    t = page
    bb = d.textbbox((0, 0), t, font=F(PEN, 78))
    d.text((W - M - (bb[2] - bb[0]), 88), t, font=F(PEN, 78), fill=(120, 120, 124))


def strike(d, text, y=266):
    """통념에 X + 취소선"""
    f = F(PEN, 64)
    tx = M + 76
    d.text((tx, y), text, font=f, fill=GRAY)
    bb = d.textbbox((tx, y), text, font=f)
    mid = (bb[1] + bb[3]) // 2 + 4
    d.line([(tx - 12, mid), (bb[2] + 10, mid)], fill=GRAY, width=6)
    d.line([(M + 8, y + 26), (M + 54, y + 74)], fill=GRAY, width=9)
    d.line([(M + 54, y + 26), (M + 8, y + 74)], fill=GRAY, width=9)


def title(d, lines, y=384, size=168, gap=200):
    for ln in lines:
        d.text((M, y), ln, font=F(EB, size), fill=INK)
        y += gap
    return y


def sub(d, text, y):
    d.text((M, y), text, font=F(PEN, 82), fill=(58, 58, 60))


def note(d, lines, top, bottom, size=76, lead=98):
    """'한 번 더' 손글씨 박스"""
    x0, x1 = M - 34, W - M + 34
    d.rounded_rectangle([x0, top, x1, bottom], radius=54, outline=INK, width=7)
    tag, ft = "한 번 더", F(RB, 58)
    tb = d.textbbox((0, 0), tag, font=ft)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    d.rounded_rectangle([x0 + 46, top - 44, x0 + 46 + tw + 68, top + 46], radius=22, fill=INK)
    d.text((x0 + 80 - tb[0], top - 44 + (90 - th) // 2 - tb[1]), tag, font=ft, fill=(255, 255, 255))
    y = top + 76
    fb = F(PEN, size)
    for ln in lines:
        if ln:
            d.text((x0 + 74, y), ln, font=fb, fill=(38, 38, 40))
        y += lead


def foot(d, text="@차노쌤 · 앳나운"):
    ff = F(PEN, 58)
    bb = d.textbbox((0, 0), text, font=ff)
    d.text(((W - (bb[2] - bb[0])) // 2 - bb[0], (H - 112) - bb[3]), text, font=ff, fill=(170, 170, 173))


def caption(d, text, y, size=58):
    f = F(PEN, size)
    bb = d.textbbox((0, 0), text, font=f)
    d.text(((W - (bb[2] - bb[0])) // 2 - bb[0], y), text, font=f, fill=(122, 122, 126))


def cap_at(d, text, cx, y, size=54, fill=(122, 122, 126)):
    f = F(PEN, size)
    bb = d.textbbox((0, 0), text, font=f)
    d.text((cx - (bb[2] - bb[0]) // 2 - bb[0], y), text, font=f, fill=fill)


# ── 그림 조각 ──────────────────────────────────────────────
def strands(d, cx, top, bot, n=7, spread=190, knot_y=None, loose=False, lw=9):
    """머리카락 다발. knot_y 를 주면 그 높이에서 묶인다."""
    import math
    for i in range(n):
        t = (i - (n - 1) / 2) / max((n - 1) / 2, 1)
        x_top = cx + t * 40
        x_bot = cx + t * spread * (1.6 if loose else 1.0)
        pts = []
        for k in range(0, 21):
            u = k / 20
            x = x_top + (x_bot - x_top) * (u ** 1.7)
            if knot_y is not None:
                ky = (knot_y - top) / (bot - top)
                if u < ky:                       # 매듭 위쪽은 붙어 있다
                    x = x_top + (cx - x_top) * (u / max(ky, .01)) * 0.9
                elif u < ky + 0.06:
                    x = cx + t * 8
            y = top + (bot - top) * u
            x += math.sin(u * 6 + i) * (6 if not loose else 14)
            pts.append((x, y))
        d.line(pts, fill=INK, width=lw, joint="curve")


def knot(d, cx, cy, r=54):
    """매듭 표시 — 겹친 두 고리"""
    d.ellipse([cx - r, cy - r * 0.62, cx, cy + r * 0.62], outline=INK, width=11)
    d.ellipse([cx, cy - r * 0.62, cx + r, cy + r * 0.62], outline=INK, width=11)


def scissors(d, x, y, s=1.0, ang=0):
    """티닝가위 약식"""
    L = int(150 * s)
    d.line([(x, y), (x + L, y - int(46 * s))], fill=INK, width=11)
    d.line([(x, y + int(30 * s)), (x + L, y + int(76 * s))], fill=INK, width=11)
    d.ellipse([x - int(58 * s), y - int(34 * s), x - int(6 * s), y + int(18 * s)], outline=INK, width=11)
    d.ellipse([x - int(58 * s), y + int(14 * s), x - int(6 * s), y + int(66 * s)], outline=INK, width=11)
    for k in range(5):                                   # 티닝 날
        xx = x + int((36 + k * 22) * s)
        d.line([(xx, y - int(20 * s)), (xx, y + int(2 * s))], fill=INK, width=6)


def arrow(d, x0, y0, x1, y1, w=9, head=26):
    import math
    d.line([(x0, y0), (x1, y1)], fill=INK, width=w)
    a = math.atan2(y1 - y0, x1 - x0)
    for s in (+1, -1):
        d.line([(x1, y1),
                (x1 - head * math.cos(a - s * 0.5), y1 - head * math.sin(a - s * 0.5))],
               fill=INK, width=w)
