#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""긴얼굴형 단발공식 카드의 그림체를 그대로 따옴.

원본을 뜯어보고 얻은 어휘:
  · 선은 **매끄럽다**. 떨림이 아니라 곡선의 비대칭이 손맛을 만든다. (내가 넣던 wobble이 오히려 낙서로 보였다)
  · 굵기 균일 (2160 기준 10~12px), 채우기 거의 없음, 흰 배경
  · 얼굴 = 세로로 긴 타원 / 눈 = 작은 검은 점 두 개 / 입 = 짧은 곡선
  · 머리 = 얼굴 양옆의 아크(선), 실루엣 아님
  · 컬 = 세로 물결선(S자 반복)
  · 기준선 = 점선, 표시 = 짧은 화살표 + 작은 손글씨
"""
import math

INK = (26, 26, 26)
LW = 11


def _b3(p0, p1, p2, p3, n=48):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                    u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
    return out


def line(d, pts, w=LW, fill=INK):
    d.line(pts, fill=fill, width=w, joint="curve")


def dashed(d, p0, p1, w=7, dash=26, gap=20, fill=INK):
    x0, y0 = p0
    x1, y1 = p1
    L = math.hypot(x1 - x0, y1 - y0)
    n = int(L // (dash + gap))
    for i in range(n + 1):
        a = i * (dash + gap) / L
        b = min((i * (dash + gap) + dash) / L, 1)
        d.line([(x0 + (x1 - x0) * a, y0 + (y1 - y0) * a),
                (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b)], fill=fill, width=w)


def face(d, cx, cy, rx=150, ry=200, w=LW, smile=True, eyes=True):
    """세로로 긴 타원 얼굴"""
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=INK, width=w)
    if eyes:
        r = max(11, int(rx * 0.085))
        d.ellipse([cx - rx * .40 - r, cy - ry * .22 - r, cx - rx * .40 + r, cy - ry * .22 + r], fill=INK)
        d.ellipse([cx + rx * .40 - r, cy - ry * .22 - r, cx + rx * .40 + r, cy - ry * .22 + r], fill=INK)
    if smile:
        line(d, _b3((cx - rx * .34, cy + ry * .18), (cx - rx * .16, cy + ry * .40),
                    (cx + rx * .16, cy + ry * .40), (cx + rx * .34, cy + ry * .18)), w=w - 2)


def side_hair(d, cx, cy, rx=150, ry=200, out=1.0, w=LW, drop=1.0):
    """얼굴 양옆으로 내려오는 머리 — 아크 두 개"""
    for s in (-1, 1):
        line(d, _b3((cx + s * rx * .78, cy - ry * .86),
                    (cx + s * (rx + 60 * out), cy - ry * .2),
                    (cx + s * (rx + 46 * out), cy + ry * (.55 * drop)),
                    (cx + s * rx * .60, cy + ry * (1.06 * drop))), w=w)


def wave(d, x, y0, y1, amp=34, cycles=3.0, w=LW):
    """세로 물결선 — 컬"""
    pts = []
    n = 60
    for i in range(n + 1):
        t = i / n
        pts.append((x + math.sin(t * math.pi * 2 * cycles) * amp, y0 + (y1 - y0) * t))
    line(d, pts, w=w)


def strand(d, x0, y0, x1, y1, bow=0.0, w=LW):
    """머리 한 가닥"""
    mx = (x0 + x1) / 2 + bow
    line(d, _b3((x0, y0), (mx, y0 + (y1 - y0) * .38),
                (mx, y0 + (y1 - y0) * .70), (x1, y1)), w=w)


def tangle(d, cx, cy, r=64, w=LW):
    """매듭 — 겹친 고리 두 개 (얽힌 표시)"""
    for k, (ox, oy, rr) in enumerate(((-r * .42, 0, r * .62), (r * .42, 0, r * .62))):
        d.ellipse([cx + ox - rr, cy - oy - rr * .78, cx + ox + rr, cy - oy + rr * .78],
                  outline=INK, width=w)
    line(d, [(cx - r * 1.1, cy + r * .5), (cx + r * 1.1, cy - r * .5)], w=w - 2)


def shears(d, x, y, s=1.0, rot=-0.42, w=LW, thinning=True):
    """가위 — 원본 톤(얇은 선 + 작은 고리)"""
    ca, sa = math.cos(rot), math.sin(rot)
    P = lambda px, py: (x + (px * ca - py * sa) * s, y + (px * sa + py * ca) * s)
    line(d, [P(0, 0), P(215, -30)], w=w)
    line(d, [P(0, 32), P(215, 62)], w=w)
    for cyy in (-24, 26):
        pts = [P(-72 + math.cos(a) * 42, cyy + math.sin(a) * 32)
               for a in (i / 40 * 2 * math.pi for i in range(41))]
        line(d, pts, w=w - 2)
    if thinning:
        for k in range(6):
            px = 62 + k * 25
            line(d, [P(px, -12), P(px, 6)], w=max(5, w - 5))


def frizz(d, x0, x1, y, n=13, h=54, w=7):
    """끝만 친 잔털 — 삐침"""
    for i in range(n):
        x = x0 + (x1 - x0) * i / max(n - 1, 1)
        line(d, [(x, y), (x + (h * .22) * ((-1) ** i), y + h)], w=w)


def finger(d, x, y, wdt=58, hgt=250, w=LW):
    """손가락 하나 — 둥근 막대"""
    d.rounded_rectangle([x, y, x + wdt, y + hgt], radius=wdt // 2, outline=INK, width=w)


def arrow(d, x0, y0, x1, y1, w=8, head=30):
    line(d, [(x0, y0), (x1, y1)], w=w)
    a = math.atan2(y1 - y0, x1 - x0)
    for s in (+1, -1):
        line(d, [(x1, y1), (x1 - head * math.cos(a - s * .5), y1 - head * math.sin(a - s * .5))], w=w)


def bundle(d, x_top, y_top, x_bot, y_bot, wid, w=LW, inner=2):
    """굵은 덩어리 — 통짜로 뭉쳐 내려오는 머리. 외곽선 + 안쪽 결 몇 줄."""
    L = _b3((x_top - wid * .5, y_top), (x_top - wid * .62, y_top + (y_bot - y_top) * .42),
            (x_bot - wid * .60, y_bot - (y_bot - y_top) * .22), (x_bot - wid * .38, y_bot))
    R = _b3((x_top + wid * .5, y_top), (x_top + wid * .66, y_top + (y_bot - y_top) * .42),
            (x_bot + wid * .62, y_bot - (y_bot - y_top) * .22), (x_bot + wid * .40, y_bot))
    line(d, L, w=w)
    line(d, R, w=w)
    line(d, [L[-1], R[-1]], w=w)                       # 뭉툭한 끝 — 갈라지지 않는다
    for k in range(inner):
        t = (k + 1) / (inner + 1)
        line(d, [( (1-t)*a[0] + t*b[0], (1-t)*a[1] + t*b[1] ) for a, b in zip(L, R)],
             w=max(5, w - 5))


def magnify(d, from_xy, cx, cy, r, w=LW):
    """확대 원 — 어디를 보는지 선으로 잇고, 원 안을 크게 보여준다."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK, width=w)
    fx, fy = from_xy
    ang = math.atan2(cy - fy, cx - fx)
    for s in (-1, 1):
        a = ang + s * 0.42
        dashed(d, (fx, fy), (cx - r * math.cos(a), cy - r * math.sin(a)), w=max(5, w - 5),
               dash=22, gap=16)


def knot_detail(d, cx, cy, r, w=LW):
    """확대 원 안에 그릴 매듭 — 가닥들이 서로 얽혀 묶인 모습"""
    for k, dy in enumerate((-r * .34, r * .06, r * .44)):
        line(d, _b3((cx - r * .82, cy + dy - r * .10), (cx - r * .30, cy + dy - r * .34),
                    (cx + r * .30, cy + dy + r * .30), (cx + r * .82, cy + dy + r * .06)), w=w - 2)
    for k, dx in enumerate((-r * .30, r * .26)):
        line(d, _b3((cx + dx - r * .16, cy - r * .74), (cx + dx + r * .30, cy - r * .22),
                    (cx + dx - r * .30, cy + r * .26), (cx + dx + r * .12, cy + r * .76)), w=w - 2)
    d.ellipse([cx - r * .30, cy - r * .22, cx + r * .30, cy + r * .26], outline=INK, width=w - 2)


def split_open(d, cx, y_top, y_bot, gap, n=3, w=LW):
    """손가락이 들어가 결이 양쪽으로 벌어진 모습"""
    for s in (-1, 1):
        for k in range(n):
            off = gap * .5 + k * gap * .42
            line(d, _b3((cx + s * gap * .12, y_top),
                        (cx + s * (off * .5), y_top + (y_bot - y_top) * .38),
                        (cx + s * off, y_top + (y_bot - y_top) * .72),
                        (cx + s * (off + gap * .34), y_bot)), w=w)


def slot(d, cx, cy, rx, ry, w=7):
    """'자리' 표시 — 점선 타원"""
    n = 44
    for i in range(n):
        if i % 2:
            continue
        a0 = i / n * 2 * math.pi
        a1 = (i + 1) / n * 2 * math.pi
        d.line([(cx + rx * math.cos(a0), cy + ry * math.sin(a0)),
                (cx + rx * math.cos(a1), cy + ry * math.sin(a1))], fill=INK, width=w)
