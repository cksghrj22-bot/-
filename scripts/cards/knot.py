#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""매듭 — 형이 확정한 레퍼런스 그림체.

레퍼런스를 뜯어보고 얻은 어휘:
  · 가닥은 **선 한 줄이 아니라 리본**이다. 양쪽 윤곽 두 줄로 그려야 굵기가 보인다.
  · 교차는 **위빙**이다. 위로 지나가는 가닥이 아래 가닥을 흰색으로 가린다.
    이 오클루더가 없으면 그냥 겹친 낙서로 보인다. 이게 핵심.
  · 선은 매끄럽다. 떨림 없음.
  · 확대원 = 얇은 원 + 아래쪽으로 뻗는 실선 리더(점선 아님).
  · 큰 가닥 두 줄이 원 위에서 들어와 아래에서 만나 좁은 V(목걸이 모양)를 만들고,
    그 한가운데에 촘촘한 뭉치가 있다.
"""
import math

INK = (26, 26, 26)
BG = (255, 255, 255)


def _b3(p0, p1, p2, p3, n=60):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                    u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
    return out


def _offset(pts, dist):
    """폴리라인을 법선 방향으로 dist 만큼 민다."""
    out, n = [], len(pts)
    for i, (x, y) in enumerate(pts):
        if i == 0:
            dx, dy = pts[1][0] - x, pts[1][1] - y
        elif i == n - 1:
            dx, dy = x - pts[-2][0], y - pts[-2][1]
        else:
            dx, dy = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
        L = math.hypot(dx, dy) or 1.0
        out.append((x - dy / L * dist, y + dx / L * dist))
    return out


def ribbon(d, pts, rw, w=7, ink=INK, occlude=True):
    """가닥 하나. rw = 가닥 두께, w = 윤곽선 굵기.

    흰 오클루더를 먼저 깔아 **뒤에 있는 가닥을 가린다** → 위로 지나가는 느낌.
    """
    if occlude:
        d.line(pts, fill=BG, width=int(rw + w * 1.6), joint="curve")
    d.line(_offset(pts, rw / 2), fill=ink, width=w, joint="curve")
    d.line(_offset(pts, -rw / 2), fill=ink, width=w, joint="curve")


def _offset_var(pts, prof):
    """점마다 다른 폭으로 민다. prof(t) -> 밀 거리."""
    out, n = [], len(pts)
    for i, (x, y) in enumerate(pts):
        if i == 0:
            dx, dy = pts[1][0] - x, pts[1][1] - y
        elif i == n - 1:
            dx, dy = x - pts[-2][0], y - pts[-2][1]
        else:
            dx, dy = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
        L = math.hypot(dx, dy) or 1.0
        t = i / (n - 1)
        dist = prof(t)
        out.append((x - dy / L * dist, y + dx / L * dist))
    return out


def clump(d, pts, wid, w=9, taper=0.72, cap=True, vein=True):
    """덩어리 한 뭉치 — 통짜로 뭉쳐 내려오는 머리.

    가는 선 여러 줄이 아니라 **폭을 가진 한 덩어리**로 그린다.
    끝을 막아야(cap) 갈라지지 않고 뭉툭하게 끝나는 게 보인다. 그게 덩어리의 증거다.
    """
    prof = lambda t: wid / 2 * (1 - (1 - taper) * t)
    A = _offset_var(pts, prof)
    B = _offset_var(pts, lambda t: -prof(t))
    d.polygon(A + B[::-1], fill=BG)
    d.line(A, fill=INK, width=w, joint="curve")
    d.line(B, fill=INK, width=w, joint="curve")
    if cap:
        d.line([A[-1], B[-1]], fill=INK, width=w)
    # 안쪽 결 한 줄 — 덩어리 안에도 머리카락이 있다는 표시. 두 줄 이상은 지저분하다.
    # 정수리 아치처럼 다른 덩어리와 나란히 붙는 자리에서는 끈다(선이 세 겹으로 보인다).
    if vein:
        d.line(_offset_var(pts, lambda t: prof(t) * .34), fill=(150, 150, 154),
               width=max(4, w - 4), joint="curve")


def _loop(cx, cy, rx, ry, rot=0.0, n=72, a0=0.0, a1=2 * math.pi):
    ca, sa = math.cos(rot), math.sin(rot)
    pts = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        px, py = rx * math.cos(a), ry * math.sin(a)
        pts.append((cx + px * ca - py * sa, cy + px * sa + py * ca))
    return pts


def _r(i):
    """결정론적 0..1 — 같은 그림은 항상 같게."""
    x = math.sin(i * 127.1 + 78.233) * 43758.5453
    return x - math.floor(x)


def tangle(d, cx, cy, r, rw=None, w=None, dense=11):
    """뭉치 — 고리들이 서로 얽혀 묶인 덩어리.

    고리 크기·중심·기울기를 다 다르게 흩어야 '얽힘'이 된다.
    규칙적으로 겹치면 실패다 — 실타래를 감아놓은 것처럼 보인다.
    """
    rw = rw or r * 0.22
    w = w or max(4, int(r * 0.062))
    for k in range(dense):
        a = _r(k) * math.pi
        ox = (_r(k + 50) - .5) * r * .66
        oy = (_r(k + 90) - .5) * r * .52
        rx = r * (.44 + _r(k + 130) * .52)
        ry = rx * (.46 + _r(k + 170) * .40)
        ribbon(d, _loop(cx + ox, cy + oy, rx, ry, rot=a), rw, w)
    # 뭉치 밖으로 삐져나온 짧은 가닥 — 고리 위에 그려야 끊기지 않는다.
    # 사방으로 흩어야 한다. 좌우로만 뻗으면 가로 막대가 되어 뭉치를 덮는다.
    for k, a in enumerate((-2.62, 2.42, -0.42, 0.62)):
        x0, y0 = cx + r * .22 * math.cos(a), cy + r * .22 * math.sin(a)
        x1, y1 = cx + r * 1.14 * math.cos(a), cy + r * .92 * math.sin(a)
        mx = (x0 + x1) / 2 - (y1 - y0) * .24
        my = (y0 + y1) / 2 + (x1 - x0) * .24
        ribbon(d, _b3((x0, y0), (mx, my), (mx, my), (x1, y1)), rw * .80, w)


def knot(d, cx, cy, R, w=None, rw=None, lead=None):
    """확대원 + 그 안의 매듭. 레퍼런스 재현.

    lead = (x, y) 리더선이 향할 지점 (원 바깥). None 이면 안 그림.
    """
    w = w or max(5, int(R * 0.038))
    rw = rw or R * 0.115
    # 원 안쪽만 흰 바탕 (뒤에 뭐가 있어도 매듭이 또렷하게)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=BG, outline=None)

    # 큰 가닥 두 줄 — 원 위에서 들어와 아래에서 만나 좁은 V 를 만든다.
    # 뭉치보다 **먼저** 그린다. 나중에 그리면 뭉치를 갈라버려 매듭이 안 보인다.
    for s in (-1, 1):
        ribbon(d, _b3((cx + s * R * 0.56, cy - R * 0.96),
                      (cx + s * R * 0.50, cy - R * 0.28),
                      (cx + s * R * 0.34, cy + R * 0.44),
                      (cx + s * R * 0.05, cy + R * 0.88)), rw, w)
    tangle(d, cx, cy + R * 0.10, R * 0.52, rw=rw * 0.90, w=w)

    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=INK, width=w)
    if lead:
        lx, ly = lead
        a = math.atan2(ly - cy, lx - cx)
        d.line([(cx + R * math.cos(a), cy + R * math.sin(a)), (lx, ly)],
               fill=INK, width=w, joint="curve")
