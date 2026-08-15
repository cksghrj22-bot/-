#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""만화카드 — 겉매직 (7장)

원천: 2026-08-06 구술 「손질편한 부분펌 4가지」
      "겉매직 — 겉만 펴서 시간은 2/1, 볼륨은 볼륨매직의 2배"
보조: 2026-07-21 구술 「잔곱슬 매직」
      "얇은 머리에 전체 매직을 세게 하면 두상·두피에 달라붙어 납작해진다"
      "사람은 얼굴에 크기(입체)가 있어서 기본적인 곱슬(볼륨)이 필요하다"
잇는 재정의(대장 확정): 펌 = 순서 / 필요한 부분에 필요한 만큼만
dedup: 겉매직 8편 존재하나 전부 "겉매직 하세요" 반복.
       '뿌리는 두고 겉만' + 시간·볼륨 숫자 프레임 = 새 각도

톤: 전체매직을 나쁘다고 하지 않는다. "뿌리까지 펴면 눌린다"는 사실만 말한다.
"""
import os, math
from PIL import Image
from cardkit import *
import glyph as G
import knot as K

K.BG = BG

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "glyphlib")
S = "겉매직이 뭔가요"
O = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_out", "geot")
os.makedirs(O, exist_ok=True)
save = lambda im, n: (im.save(f"{O}/g{n}.png"), print("ok", n))
FACE_H = 330


def paste(im, name, cx, cy, h=None, flip=False):
    g = Image.open(f"{LIB}/{name}.png")
    if flip:
        g = g.transpose(Image.FLIP_LEFT_RIGHT)
    if h:
        r = h / g.height
        g = g.resize((max(1, int(g.width * r)), max(1, int(g.height * r))), Image.LANCZOS)
    im.paste(g, (int(cx - g.width / 2), int(cy - g.height / 2)), g)


def person(im, d, cx, cy, root=1.0, wavy=0.0, face_h=FACE_H, n=9, skull=True):
    """머리 한 사람.

    root  0 = 뿌리가 눌려 두피에 달라붙음(납작) / 1 = 뿌리가 떠 있음(볼륨)

    ★ 핵심: 납작과 볼륨의 차이는 **두상선과 머리선 사이의 간격**으로 보여야 한다.
      아치 높이만 조금 바꾸면 두 그림이 똑같아 보인다(실측 확인함).
      그래서 두상(점선)을 기준선으로 깔고, 머리는 그 위에 떠 있는 만큼 벌어진다.
    """
    lw = max(6, int(face_h * .046))
    clear = face_h * .56
    spread = face_h * .95
    bot = cy + int(face_h * 1.42)
    ax, ay = cx, cy - face_h * .16
    SX, SY = face_h * .60, face_h * .58            # 두상 반경 (고정)
    # 눌리면 두상선 안쪽으로 파고들고, 뜨면 크게 부푼다.
    # 차이를 크게 벌려야 한 장만 봐도 납작인지 볼륨인지 읽힌다.
    k = 0.94 + root * .56

    def arc(rx, ry):
        return K._b3((ax - rx, ay), (ax - rx * .82, ay - ry * 1.40),
                     (ax + rx * .82, ay - ry * 1.40), (ax + rx, ay))

    if skull:                                       # 기준선 — 두상은 안 변한다
        sk = arc(SX, SY)
        for i in range(0, len(sk) - 3, 4):
            d.line([sk[i], sk[i + 2]], fill=(186, 186, 190), width=max(3, lw // 2))

    cr = arc(SX * k, SY * k)
    # 두상과 머리선 사이를 채우는 결. 납작하면 이 선들이 두상에 겹쳐 붙고,
    # 볼륨이면 벌어져 사이가 빈다. 이게 없으면 머리가 헬멧처럼 떠 보인다.
    for j in (.30, .62):
        G.line(d, arc(SX * (1 + (k - 1) * j), SY * (1 + (k - 1) * j)), w=max(4, int(lw * .68)))
    K.clump(d, cr, face_h * .15, w=lw, taper=1.0, cap=False, vein=False)
    top = cr[len(cr) // 2][1]
    h = bot - top
    for i in range(n):
        t_ = i / (n - 1)
        u = (t_ - .5) * 2
        a = cr[int(t_ * (len(cr) - 1))]
        s = 1 if (u > 0 or (u == 0 and i % 2)) else -1
        ex = cx + s * max(abs(u) * spread, clear * 1.28) * (.84 + root * .26)
        pts = K._b3(a,
                    (cx + s * clear * (1.02 + root * .30), top + h * .42),   # 얼굴을 비껴간다
                    (ex - s * spread * .12, top + h * .82),
                    (ex, bot))
        if wavy:
            pts = [(x + math.sin(j / 5.2 + i) * face_h * .085 * wavy, y)
                   for j, (x, y) in enumerate(pts)]
        G.line(d, pts, w=lw)
    paste(im, "face_only", cx, cy, h=face_h)


def big(d, text, cx, y, size=210, fill=INK):
    f = F(EB, size)
    bb = d.textbbox((0, 0), text, font=f)
    d.text((cx - (bb[2] - bb[0]) // 2 - bb[0], y), text, font=f, fill=fill)


# ── 2  왜 납작해지나 ───────────────────────────────────────
im, d = new()
head(d, S, "2 / 7")
strike(d, "매직하면 원래 머리가 죽는다")
y = title(d, ["뿌리까지 펴서", "눌린 거예요"])
sub(d, "머리가 죽은 게 아니에요", y + 20)
person(im, d, 1080, 1150, root=0.0)
cap_at(d, "두피에 그대로 붙어요", 1080, 1690, 56)
note(d, ["모발이 얇을수록 전체를 세게 펴면",
         "두상과 두피에 그대로 달라붙어요.",
         "숱이 없어진 게 아니라",
         "뿌리가 누운 거예요."], 1790, 2280)
foot(d)
save(im, 2)

# ── 3  볼륨이 왜 필요한가 ──────────────────────────────────
im, d = new()
head(d, S, "3 / 7")
strike(d, "곱슬은 다 없애는 게 좋다")
y = title(d, ["얼굴에는", "크기가 있어요"])
sub(d, "그래서 기본 볼륨이 필요해요", y + 20)
person(im, d, 1080, 1130, root=1.0, wavy=0.35)
cap_at(d, "뜬 만큼 입체가 살아요", 1080, 1690, 56)
note(d, ["사람 얼굴은 평평하지 않고 크기가 있어요.",
         "그래서 머리에도 기본 볼륨이 필요해요.",
         "그 기본까지 눌러버리면",
         "얼굴이 납작해 보여요."], 1790, 2280)
foot(d)
save(im, 3)

# ── 4  겉만 편다 ──────────────────────────────────────────
im, d = new()
head(d, S, "4 / 7")
strike(d, "매직은 전체를 펴는 것")
y = title(d, ["뿌리는 두고", "겉만 펴요"])
sub(d, "이게 겉매직이에요", y + 20)
person(im, d, 900, 1160, root=1.0, wavy=0.0)
# 어디를 두고 어디를 펴는지 — 머리 위에 직접 짚어준다. 옆에 화살표만 띄우면 안 읽힌다.
d.line([(1210, 960), (1520, 960)], fill=INK, width=7)
cap_at(d, "뿌리 볼륨은 그대로", 1720, 926, 62)
d.line([(1230, 1340), (1520, 1340)], fill=INK, width=7)
cap_at(d, "겉면만 폅니다", 1690, 1306, 62)
cap_at(d, "뿌리는 떠 있고 겉은 곧아요", 900, 1700, 56)
note(d, ["필요한 부분에 필요한 만큼만 해요.",
         "뿌리 볼륨은 그대로 두고",
         "겉으로 보이는 면만 정리하는 거예요."], 1830, 2270, lead=104)
foot(d)
save(im, 4)

# ── 5  숫자 ──────────────────────────────────────────────
im, d = new()
head(d, S, "5 / 7")
strike(d, "덜 하면 손해다")
y = title(d, ["시간은 절반,", "볼륨은 두 배"])
sub(d, "덜 하는 게 손해가 아니에요", y + 20)
d.rounded_rectangle([M - 34, 900, W // 2 - 26, 1560], radius=48, outline=INK, width=7)
d.rounded_rectangle([W // 2 + 26, 900, W - M + 34, 1560], radius=48, outline=INK, width=7)
cap_at(d, "시술 시간", 590, 972, 62)
big(d, "1/2", 590, 1080, 230)
cap_at(d, "전체매직 대비", 590, 1400, 54)
cap_at(d, "뿌리 볼륨", 1570, 972, 62)
big(d, "×2", 1570, 1080, 230)
cap_at(d, "볼륨매직 대비", 1570, 1400, 54)
note(d, ["겉만 펴니까 시간이 절반이에요.",
         "뿌리를 안 눌렀으니 볼륨은 두 배고요.",
         "덜 한 게 아니라, 필요한 데만 한 거예요."], 1830, 2270, lead=104)
foot(d)
save(im, 5)

# ── 6  누구한테 맞나 ──────────────────────────────────────
im, d = new()
head(d, S, "6 / 7")
strike(d, "매직은 누구나 똑같이")
y = title(d, ["이런 분께", "맞아요"])
sub(d, "한 번 확인해보세요", y + 20)
rows = ["매직만 하면 머리가 납작해지는 분",
        "모발이 얇고 잔곱슬이 있는 분",
        "볼륨은 살리고 싶은데 곱슬은 부담인 분",
        "시술 시간이 부담스러운 분"]
yy = 900
for r in rows:
    d.ellipse([M + 6, yy + 14, M + 62, yy + 70], outline=INK, width=8)
    d.line([(M + 20, yy + 42), (M + 34, yy + 58)], fill=INK, width=9)
    d.line([(M + 34, yy + 58), (M + 52, yy + 26)], fill=INK, width=9)
    d.text((M + 100, yy), r, font=F(RB, 74), fill=(38, 38, 40))
    yy += 152
person(im, d, 1080, 1650, root=1.0, wavy=0.0, face_h=175)
note(d, ["세 개 이상이면 겉매직이 잘 맞아요.",
         "다만 모발 상태에 따라 달라지니",
         "만져보고 정하는 게 정확해요."], 2010, 2380, lead=104)
foot(d)
save(im, 6)

# ── 1  표지 ──────────────────────────────────────────────
im, d = new()
d.text((M - 40, 108), "매직하면", font=F(EB, 168), fill=INK)
d.text((M - 40, 300), "머리 죽죠?", font=F(EB, 168), fill=INK)
d.rounded_rectangle([M - 40, 516, W - M + 40, 700], radius=40, fill=INK)
d.text((M + 10, 556), "겉만 펴면 시간 절반, 볼륨 두 배", font=F(RB, 82), fill=(255, 255, 255))

CW, CH = 930, 660
CXs, CYs = [120, 1110], [770, 1490]
for label, ci, cj in (("1  왜 납작해질까", 0, 0), ("2  볼륨은 필요해요", 1, 0),
                      ("3  겉만 펴요", 0, 1), ("4  시간 절반·볼륨 2배", 1, 1)):
    x0, y0 = CXs[ci], CYs[cj]
    d.rounded_rectangle([x0, y0, x0 + CW, y0 + CH], radius=40, outline=(214, 214, 218), width=6)
    d.text((x0 + 44, y0 + 30), label, font=F(RB, 60), fill=INK)

FH = 150
person(im, d, 585, 1030, root=0.0, face_h=FH)
cap_at(d, "뿌리까지 눌렸어요", 585, 1310, 50)
person(im, d, 1575, 1062, root=1.0, wavy=0.35, face_h=FH)
cap_at(d, "얼굴엔 크기가 있어요", 1575, 1330, 50)
person(im, d, 585, 1782, root=1.0, wavy=0.0, face_h=FH)
cap_at(d, "뿌리는 두고 겉만", 585, 2048, 50)
big(d, "1/2", 1430, 1780, 150)
big(d, "×2", 1720, 1780, 150)
cap_at(d, "시간", 1430, 1960, 50)
cap_at(d, "볼륨", 1720, 1960, 50)
caption(d, "저장했다가, 상담 때 보여주세요.  @차노쌤", 2300, 62)
save(im, 1)

# ── 7  마무리 ─────────────────────────────────────────────
im, d = new()
ctr = lambda t, f, y, c: d.text((((W - (d.textbbox((0, 0), t, font=f)[2]
                                       - d.textbbox((0, 0), t, font=f)[0])) // 2)
                                 - d.textbbox((0, 0), t, font=f)[0], y), t, font=f, fill=c)
ctr(S, F(RB, 58), 286, (120, 120, 124))
d.line([(W // 2 - 60, 414), (W // 2 + 60, 414)], fill=GRAY, width=5)
ctr("전체가 아니라,", F(EB, 152), 526, INK)
ctr("겉만이에요.", F(EB, 152), 704, INK)
for x in (-70, 0, 70):
    d.ellipse([W // 2 + x - 11, 964, W // 2 + x + 11, 986], fill=(178, 178, 182))
ctr("얼마나 펴야 할지는", F(RB, 86), 1124, (52, 52, 54))
ctr("만져봐야 알아요.", F(RB, 86), 1248, (52, 52, 54))
btn, fb = "상담 먼저 받아보세요", F(RB, 92)
bb = d.textbbox((0, 0), btn, font=fb)
bw, bh = (bb[2] - bb[0]) + 220, (bb[3] - bb[1]) + 122
bx, by = (W - bw) // 2, 1556
d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=bh // 2, fill=INK)
d.text((bx + 110 - bb[0], by + 61 - bb[1]), btn, font=fb, fill=(255, 255, 255))
ctr("저장해두셨다가 상담 때 보여주세요", F(PEN, 70), 1836, (140, 140, 144))
d.line([(W // 2 - 60, 2176), (W // 2 + 60, 2176)], fill=(206, 206, 210), width=4)
ctr("@차노쌤 · 앳나운", F(PEN, 62), 2282, (168, 168, 171))
save(im, 7)
