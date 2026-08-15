#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""숱 만화카드 — 긴얼굴 카드에서 오려낸 **진짜 손그림**을 얹어 조립.

얼굴·가위·화살표는 원본 그대로 붙인다(내가 흉내내지 않는다).
덩어리·매듭만 원본 선 굵기(17~24px)에 맞춰 새로 그린다.
"""
import os, math
from PIL import Image
from cardkit import *
import glyph as G
import knot as K

K.BG = BG          # 카드 배경색과 같아야 오클루더 자국이 안 남는다 (251,251,249)

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "glyphlib")
S = "숱을 쳐도 덩어리지는 이유"
O = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_out", "sut3")
os.makedirs(O, exist_ok=True)
save = lambda im, n: (im.save(f"{O}/s{n}.png"), print("ok", n))


def paste(im, name, cx, cy, h=None, w=None, flip=False):
    g = Image.open(f"{LIB}/{name}.png")
    if flip:
        g = g.transpose(Image.FLIP_LEFT_RIGHT)
    if h:
        r = h / g.height
    elif w:
        r = w / g.width
    else:
        r = 1
    g = g.resize((max(1, int(g.width * r)), max(1, int(g.height * r))), Image.LANCZOS)
    im.paste(g, (int(cx - g.width / 2), int(cy - g.height / 2)), g)
    return g.size


def clump(d, cx, cy_top, cy_bot, wid, w=17):
    """덩어리 — 통짜로 뭉쳐 내려오는 머리.

    막대 두 개로 그리면 기둥처럼 보인다. 정수리에서 나와 바깥으로 흘렀다가
    다시 안으로 모이는 곡선이어야 '머리'로 읽힌다.
    """
    h = cy_bot - cy_top
    s = 1 if cx > 1080 else -1
    spine = K._b3((cx - s * wid * .18, cy_top),
                  (cx + s * wid * .30, cy_top + h * .34),
                  (cx + s * wid * .26, cy_top + h * .74),
                  (cx - s * wid * .10, cy_bot))
    K.clump(d, spine, wid, w=w, taper=.80)


def strands_open(d, cx, cy_bot, spread, crown, n=11, w=17, gap=0.0, clear=180):
    """매듭이 풀려 흩어진 결.

    출발점을 한 점에 모으면 야자수가 된다. 머리는 정수리 '점'이 아니라 '선'에서 나온다.
    그래서 시작점을 정수리 아치(crown) 위에 흩는다. 이게 부챗살과 머리를 가른다.
    gap 을 주면 가운데가 비어 손가락이 들어갈 자리가 생긴다.
    """
    top = crown[len(crown) // 2][1]
    h = cy_bot - top
    for i in range(n):
        t = i / (n - 1)
        u = (t - .5) * 2
        a = crown[int(t * (len(crown) - 1))]
        # 얼굴을 덮으면 안 된다. 가운데서 난 결도 얼굴을 비껴 흘러야 한다.
        # 이걸 안 잡으면 커튼처럼 얼굴을 가린다.
        s = 1 if (u > 0 or (u == 0 and i % 2)) else -1
        ex = cx + s * max(abs(u) * spread, clear * 1.30) + s * gap
        G.line(d, K._b3(a,
                        (a[0] + s * clear * .80, top + h * .44),
                        (ex - s * spread * .14, top + h * .82),
                        (ex, cy_bot)), w=w)


def knot_ring(d, cx, cy, r, w=17):
    """매듭 — 원 안에 얽힌 가닥. 확대해서 보여준다."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK, width=w)
    for dy in (-r * .38, r * .02, r * .42):
        G.line(d, G._b3((cx - r * .80, cy + dy - r * .08), (cx - r * .28, cy + dy - r * .36),
                        (cx + r * .28, cy + dy + r * .32), (cx + r * .80, cy + dy + r * .04)),
               w=max(9, w - 4))
    for dx in (-r * .28, r * .24):
        G.line(d, G._b3((cx + dx - r * .14, cy - r * .72), (cx + dx + r * .32, cy - r * .20),
                        (cx + dx - r * .32, cy + r * .24), (cx + dx + r * .10, cy + r * .74)),
               w=max(9, w - 4))


def callout(d, x0, y0, cx, cy, r, w=9):
    a = math.atan2(cy - y0, cx - x0)
    for s in (-1, 1):
        b = a + s * .40
        G.dashed(d, (x0, y0), (cx - r * math.cos(b), cy - r * math.sin(b)), w=w, dash=24, gap=18)


FACE_H = 330            # 원본 얼굴 높이 기준


def person(im, d, cx, cy, mode="clump", face_h=FACE_H, gap=0.0):
    bot = cy + int(face_h * 1.42)          # note 박스 위에서 끝난다
    lw = max(7, int(face_h * .052))
    # 정수리 — 머리는 두피에서 나온다. 이 아치가 없으면 머리가 턱에서 자란 것처럼 보인다.
    # 덩어리든 흩어진 결이든 똑같이 필요하다.
    cr = K._b3((cx - face_h * .62, cy - face_h * .18),
               (cx - face_h * .48, cy - face_h * .82),
               (cx + face_h * .48, cy - face_h * .82),
               (cx + face_h * .62, cy - face_h * .18))
    K.clump(d, cr, face_h * .17, w=lw, taper=1.0, cap=False, vein=False)
    if mode == "clump":
        for s in (-1, 1):
            clump(d, cx + s * int(face_h * .56), cy - int(face_h * .20), bot,
                  face_h * .32, w=lw)
    else:
        # 선 굵기는 얼굴 크기에 비례해야 한다. 고정하면 표지의 작은 그림이 걸레처럼 뭉친다.
        strands_open(d, cx, bot, face_h * .95, cr, w=lw, gap=gap, clear=face_h * .56)
    paste(im, "face_only", cx, cy, h=face_h)


# ── 2 덩어리 ──────────────────────────────────────────────
im, d = new()
head(d, S, "2 / 7")
strike(d, "숱이 많아서 무겁다")
y = title(d, ["숱이 많으면", "덩어리가 져요"])
sub(d, "무거운 것보다 이게 더 불편해요", y + 20)
person(im, d, 1080, 1130)
cap_at(d, "가닥이 붙어서 통짜로 내려와요", 1080, 1670, 56)
note(d, ["숱 많은 분들이 진짜 불편해하는 건",
         "무게보다 '덩어리'예요.",
         "머리가 갈라지지 않고",
         "한 덩이로 뭉쳐 내려오거든요."], 1780, 2270)
foot(d)
save(im, 2)

# ── 3 매듭 ────────────────────────────────────────────────
im, d = new()
head(d, S, "3 / 7")
strike(d, "덩어리는 양이 많아서다")
y = title(d, ["덩어리는", "매듭 때문이에요"])
sub(d, "뿌리 쪽이 묶여 있어요", y + 20)
person(im, d, 760, 1130)
K.knot(d, 1520, 1200, 268, lead=(1010, 1000))
cap_at(d, "뿌리가 묶여 있어요", 1520, 1520, 56)
note(d, ["뿌리 쪽에 누가 매듭을 지어놓은 것처럼",
         "묶여 있어요.",
         "그 매듭이 잡고 있으니",
         "아래가 갈라지지 못하고 뭉쳐요."], 1780, 2270)
foot(d)
save(im, 3)

# ── 4 끝만 치면 ────────────────────────────────────────────
im, d = new()
head(d, S, "4 / 7")
strike(d, "끝을 치면 가벼워진다")
y = title(d, ["아무리 쳐도", "덩어리는 그대로"])
sub(d, "친 모발은 끝만 날려요", y + 20)
person(im, d, 940, 1130)
for s in (-1, 1):
    G.frizz(d, 940 + s * 150, 940 + s * 300, 1130 + int(FACE_H * 1.42) + 6, n=5, h=52, w=9)
paste(im, "shears", 1500, 1640, h=290)
cap_at(d, "끝만 잘림", 1500, 1720, 54)
note(d, ["매듭을 그대로 두고 끝만 치면",
         "덩어리는 안 풀려요.",
         "잘려 나간 짧은 모발만 끝에서 날리고,",
         "무게는 그대로예요."], 1800, 2280)
foot(d)
save(im, 4)

# ── 5 흩어내기 ─────────────────────────────────────────────
im, d = new()
head(d, S, "5 / 7")
strike(d, "많이 쳐야 가벼워진다")
y = title(d, ["매듭을", "흩어내야 풀려요"])
sub(d, "한두 가닥이면 됩니다", y + 20)
person(im, d, 1000, 1130, mode="open")
paste(im, "shears", 1600, 1150, h=290, flip=True)
cap_at(d, "묶인 자리에 한두 번", 1000, 1680, 56)
note(d, ["묶인 자리에서 한두 가닥만 흩어내도",
         "머리가 풀려요.",
         "중간 볼륨이 살고 흐름이 생겨요.",
         "많이 치는 게 아니라, 어디를 치느냐예요."], 1800, 2280)
foot(d)
save(im, 5)

# ── 6 공간 ────────────────────────────────────────────────
im, d = new()
head(d, S, "6 / 7")
strike(d, "잘게 여러 번 비운다")
y = title(d, ["손가락이", "들어갈 자리"])
sub(d, "공간은 크게 내는 거예요", y + 20)
person(im, d, 1080, 1120, mode="open", gap=FACE_H * .40)
# 손가락과 '자리'는 얼굴 아래에서 시작한다. 얼굴에 걸치면 얼굴을 찌르는 그림이 된다.
G.slot(d, 1080, 1500, 205, 150, w=9)
G.finger(d, 1080 - 128, 1360, 96, 268, w=17)
G.finger(d, 1080 + 32, 1332, 96, 296, w=17)
cap_at(d, "손가락이 쑥 들어가요", 1080, 1680, 56)
note(d, ["잘게 여러 번 비우면 잔털만 생겨요.",
         "손가락이 들어갈 만큼 크게 비워야",
         "머리가 갈라지고 숨을 쉬어요."], 1830, 2260, lead=104)
foot(d)
save(im, 6)

# ── 1 표지 ────────────────────────────────────────────────
# 표지는 마지막에 그린다 — 안쪽 카드 그림이 확정된 뒤 그걸 축소해 얹어야 톤이 맞는다.
im, d = new()
d.text((M - 40, 108), "숱 쳤는데", font=F(EB, 168), fill=INK)
d.text((M - 40, 300), "왜 뭉칠까요?", font=F(EB, 168), fill=INK)
d.rounded_rectangle([M - 40, 516, W - M + 40, 700], radius=40, fill=INK)
d.text((M + 10, 556), "양이 아니라 뿌리 매듭 때문이에요", font=F(RB, 82), fill=(255, 255, 255))

CW, CH = 930, 660
CXs, CYs = [120, 1110], [770, 1490]
for label, ci, cj in (("1  덩어리", 0, 0), ("2  매듭", 1, 0),
                      ("3  끝만 치면", 0, 1), ("4  흩어내기", 1, 1)):
    x0, y0 = CXs[ci], CYs[cj]
    d.rounded_rectangle([x0, y0, x0 + CW, y0 + CH], radius=40, outline=(214, 214, 218), width=6)
    d.text((x0 + 44, y0 + 30), label, font=F(RB, 60), fill=INK)

FH = 150
person(im, d, 585, 1010, face_h=FH)
cap_at(d, "붙어서 뭉쳐 내려와요", 585, 1300, 50)

K.knot(d, 1575, 1090, 150)   # 표지에는 리더선 없음 — 가리킬 머리가 없다
cap_at(d, "뿌리가 묶여 있어요", 1575, 1300, 50)

person(im, d, 520, 1730, face_h=FH)
for s in (-1, 1):
    G.frizz(d, 520 + s * 74, 520 + s * 150, 1730 + int(FH * 1.42) + 4, n=5, h=40, w=6)
paste(im, "shears", 830, 1900, h=190)
cap_at(d, "덩어리는 그대로", 585, 2020, 50)

person(im, d, 1520, 1730, mode="open", face_h=FH)
paste(im, "shears", 1840, 1720, h=190, flip=True)
cap_at(d, "흩어내면 풀려요", 1575, 2020, 50)

caption(d, "저장했다가, 상담 때 보여주세요.  @차노쌤", 2300, 62)
save(im, 1)

# ── 7 마무리 ──────────────────────────────────────────────
im, d = new()
ctr = lambda t, f, y, c: d.text((((W - (d.textbbox((0, 0), t, font=f)[2]
                                       - d.textbbox((0, 0), t, font=f)[0])) // 2)
                                 - d.textbbox((0, 0), t, font=f)[0], y), t, font=f, fill=c)
ctr(S, F(RB, 58), 286, (120, 120, 124))
d.line([(W // 2 - 60, 414), (W // 2 + 60, 414)], fill=GRAY, width=5)
ctr("양이 아니라,", F(EB, 152), 526, INK)
ctr("매듭이에요.", F(EB, 152), 704, INK)
for x in (-70, 0, 70):
    d.ellipse([W // 2 + x - 11, 964, W // 2 + x + 11, 986], fill=(178, 178, 182))
ctr("어디가 묶였는지는", F(RB, 86), 1124, (52, 52, 54))
ctr("만져봐야 알아요.", F(RB, 86), 1248, (52, 52, 54))
btn, fb = "상담 먼저 받아보세요", F(RB, 92)
bb = d.textbbox((0, 0), btn, font=fb)
bw, bh = (bb[2] - bb[0]) + 220, (bb[3] - bb[1]) + 122
bx, by = (W - bw) // 2, 1556
d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=bh // 2, fill=INK)
d.text((bx + 110 - bb[0], by + 61 - bb[1]), btn, font=fb, fill=(255, 255, 255))
ctr("저장해두셨다가 상담 때 보여주세요", F(PEN, 70), 1836, (140, 140, 144))
d.line([(W // 2 - 60, 2176), (W // 2 + 60, 2176)], fill=(206, 206, 210), width=4)
ctr("@차노쌤 · 예약은 프로필 링크에서", F(PEN, 62), 2282, (168, 168, 171))
save(im, 7)
