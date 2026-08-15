#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""에이엠톤식 좌하단 두 줄 카드 — 낙타형과 별개 줄기.

낙타형(scripts/cards/nakta_post.py)과 섞지 말 것.
 · 낙타형 = 글자폭 흰/검정 박스 · 계단 · 상단~중단 배치
 · 에이엠톤식 = 박스 없음 · 좌하단 고정 두 줄 · 하단 스크림 · 노란 포인트 단어

모든 수치는 매니페스트(JSON)에서 온다. 여기 하드코딩 금지.
  python3 scripts/cards/amton_post.py content/amton/<manifest>.json
"""
import json, os, sys, pathlib
from PIL import Image, ImageDraw, ImageFont

HERE  = pathlib.Path(__file__).resolve().parent
ROOT  = HERE.parents[1]
FONTS = HERE / "fonts"

def hexc(s, a=255):
    s = s.lstrip("#")
    return tuple(int(s[i:i+2], 16) for i in (0, 2, 4)) + (a,)

def fit_cover(im, W, H, anchor=0.5):
    w, h = im.size
    s = max(W / w, H / h)
    im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
    w, h = im.size
    return im.crop(((w - W) // 2, int((h - H) * anchor), (w - W) // 2 + W, int((h - H) * anchor) + H))

def scrim(size, height, alpha, from_bottom=True):
    W, H = size
    ov = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    top = int(H * (1 - height))
    for y in range(top, H):
        t = (y - top) / max(H - top - 1, 1)
        d.line([(0, y), (W, y)], fill=(0, 0, 0, int(alpha * (t ** 1.6))))
    return ov

def draw_line(d, x, y, text, accent, font, col, acol):
    """accent 부분문자열만 노랑. 나머지는 흰색."""
    cur = x
    parts = []
    if accent and accent in text:
        i = text.index(accent)
        parts = [(text[:i], col), (accent, acol), (text[i+len(accent):], col)]
    else:
        parts = [(text, col)]
    for seg, c in parts:
        if not seg:
            continue
        d.text((cur, y), seg, font=font, fill=c)
        cur += d.textlength(seg, font=font)
    return cur

def render_card(c, dflt, W, H, out):
    src = ROOT / c["src"] if not os.path.isabs(c["src"]) else pathlib.Path(c["src"])
    base = fit_cover(Image.open(src).convert("RGB"), W, H, c.get("anchor", dflt.get("anchor", 0.45)))
    base = base.convert("RGBA")
    sc = dflt["scrim"]
    base = Image.alpha_composite(base, scrim((W, H), sc["height"], sc["alpha"]))

    d = ImageDraw.Draw(base)
    f1 = ImageFont.truetype(str(FONTS / dflt["font"]), c.get("size_1", dflt["size_1"]))
    f2 = ImageFont.truetype(str(FONTS / dflt["font"]), c.get("size_2", dflt["size_2"]))
    col  = hexc(dflt["color"]); acol = hexc(c.get("accent_color", dflt["accent"]))
    x    = int(W * c.get("x", dflt["x"]))
    gap  = dflt["line_gap"]

    l1, l2 = c["line1"], c.get("line2", "")
    h1 = d.textbbox((0, 0), l1, font=f1)[3]
    h2 = d.textbbox((0, 0), l2, font=f2)[3] if l2 else 0
    bottom = int(H * (1 - c.get("bottom", dflt["bottom"])))
    y2 = bottom - h2
    y1 = y2 - gap - h1 if l2 else bottom - h1

    draw_line(d, x, y1, l1, c.get("accent"), f1, col, acol)
    if l2:
        draw_line(d, x, y2, l2, c.get("accent2"), f2, col, acol)

    out.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(out, quality=93)
    return out

def main():
    mf = pathlib.Path(sys.argv[1])
    m  = json.load(open(mf, encoding="utf-8"))
    W, H = m["canvas"]["w"], m["canvas"]["h"]
    dflt = m["defaults"]
    outdir = ROOT / m["out"]
    made = []
    for i, c in enumerate(m["cards"], 1):
        made.append(render_card(c, dflt, W, H, outdir / f"amton_{i}.jpg"))
        print(f"amton_{i}.jpg  <- {c['src']}   「{c['line1']} / {c.get('line2','')}」")
    return made

if __name__ == "__main__":
    main()
