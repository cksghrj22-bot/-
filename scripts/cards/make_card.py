#!/usr/bin/env python3
"""결이 이야기 만화카드 조립기 — 원본 그림 → 1080x1350 인스타 카드.

폼 정본 = 「결이 이야기 ① 매듭 편」 최종 6장 (`_out/매듭이야기_final_복고텍스트/`).
  표지형 : 배지 2개(시리즈+편) → 제목(굵은 고딕) → 그림
  본문형 : 상단 크림 밴드 안 헤드 1줄 → 그림 → 하단 크림 패널 본문 2~3줄(손글씨)
  전후형 : 상단 크림 밴드 헤드만, 하단 패널 없음 (--no-panel 자동: body 미지정)

사용:
  python3 make_card.py --img raw/c1.png --out out/c1.png \
      --badge "결이 이야기 ②|생쥐 편" --title "쫙 폈는데|왜 생쥐가 됐죠?"

  python3 make_card.py --img raw/c3.png --out out/c3.png \
      --head "얇은 머리에 다 세게 펴면" \
      --body "두상에 납작하게 붙어서|생기가 없어져요."

`|` 가 줄바꿈. 본문은 2줄 권장(최대 3줄), 행당 18자 이내.
"""
import argparse, os
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
CREAM = (247, 239, 223)      # 카드 바탕
BAND = (250, 244, 232)       # 상단 헤드 밴드
PANEL_BG = (253, 247, 235)   # 하단 본문 패널
INK = (58, 42, 32)
BROWN = (150, 92, 48)

FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
F_HEAD = os.path.join(FONTS, "BlackHanSans-Regular.ttf")
F_SUB = os.path.join(FONTS, "Jua-Regular.ttf")
F_BODY = os.path.join(FONTS, "Gaegu-Bold.ttf")

PAD = 52
BAND_H = 168          # 헤드 밴드 높이
LINE_BODY = 74        # 본문 행간


def fit(img, w, h):
    r = max(w / img.width, h / img.height)
    im = img.resize((round(img.width * r), round(img.height * r)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


CIRCLED = {"①": "1", "②": "2", "③": "3", "④": "4", "⑤": "5",
           "⑥": "6", "⑦": "7", "⑧": "8", "⑨": "9", "⑩": "10"}


def _segs(text):
    """'결이 이야기 ②' → [('t','결이 이야기 '), ('c','2')] — ○숫자는 폰트에 없어 직접 그린다."""
    out, buf = [], ""
    for ch in text:
        if ch in CIRCLED:
            if buf:
                out.append(("t", buf)); buf = ""
            out.append(("c", CIRCLED[ch]))
        else:
            buf += ch
    if buf:
        out.append(("t", buf))
    return out


def pill(d, x, y, text, font, filled):
    """배지 알약. filled=True 브라운 채움 / False 브라운 테두리."""
    segs = _segs(text)
    r = 21  # 동그라미 숫자 반지름
    tw = sum(d.textlength(s, font=font) if k == "t" else r * 2 + 6 for k, s in segs)
    box = [x, y, x + tw + 52, y + 62]
    fg = (255, 250, 240) if filled else BROWN
    if filled:
        d.rounded_rectangle(box, 31, fill=BROWN)
    else:
        d.rounded_rectangle(box, 31, outline=BROWN, width=4)
    cx = x + 26
    for kind, s in segs:
        if kind == "t":
            d.text((cx, y + 12), s, font=font, fill=fg)
            cx += d.textlength(s, font=font)
        else:
            cy = y + 31
            d.ellipse([cx + 3, cy - r, cx + 3 + r * 2, cy + r], outline=fg, width=3)
            nw = d.textlength(s, font=font)
            d.text((cx + 3 + r - nw / 2, cy - 20), s, font=font, fill=fg)
            cx += r * 2 + 6
    return box[2]


def build(a):
    canvas = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(canvas)
    art = Image.open(a.img).convert("RGB")

    if a.title:  # ── 표지형
        f_title = ImageFont.truetype(F_HEAD, 82)
        f_badge = ImageFont.truetype(F_SUB, 34)
        y = 46
        if a.badge:
            x = PAD
            for i, b in enumerate([s.strip() for s in a.badge.split("|")]):
                x = pill(d, x, y, b, f_badge, filled=(i == 0)) + 16
            y += 86
        for ln in a.title.split("|"):
            d.text((PAD, y), ln, font=f_title, fill=INK)
            y += 98
        top = y + 18
        canvas.paste(fit(art, W - PAD * 2, H - top - PAD), (PAD, top))
    else:  # ── 본문형 / 전후형
        f_head = ImageFont.truetype(F_HEAD, 64)
        f_body = ImageFont.truetype(F_BODY, 56)
        body_lines = [s for s in (a.body or "").split("|") if s]
        panel_h = (30 + LINE_BODY * len(body_lines) + 30) if body_lines else 0
        d.rectangle([0, 0, W, BAND_H], fill=BAND)
        if a.head:
            d.text((PAD, (BAND_H - 78) // 2), a.head, font=f_head, fill=INK)
        art_bottom = H - (panel_h + 34) if panel_h else H
        canvas.paste(fit(art, W, art_bottom - BAND_H), (0, BAND_H))
        if panel_h:
            py = H - panel_h - 22
            d.rounded_rectangle([34, py, W - 34, py + panel_h], 30,
                                fill=PANEL_BG, outline=BROWN, width=4)
            ty = py + 26
            for ln in body_lines:
                d.text((74, ty), ln, font=f_body, fill=INK)
                ty += LINE_BODY

    if a.pin:
        f_pin = ImageFont.truetype(F_BODY, 44)
        px, py = [float(v) for v in a.pin_xy.split(",")]
        tw = d.textlength(a.pin, font=f_pin)
        x, y = px * W, py * H
        d.rounded_rectangle([x, y, x + tw + 48, y + 70], 35,
                            fill=(255, 252, 245), outline=BROWN, width=4)
        d.text((x + 24, y + 10), a.pin, font=f_pin, fill=INK)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    canvas.save(a.out)
    print(a.out, canvas.size)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--img", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--badge", help='표지 배지. "결이 이야기 ②|생쥐 편"')
    p.add_argument("--title", help="표지 제목. | 로 줄바꿈")
    p.add_argument("--head", help="본문형 상단 밴드 헤드 1줄")
    p.add_argument("--body", help="하단 패널 본문. | 로 줄바꿈")
    p.add_argument("--pin", help="지시선 말풍선")
    p.add_argument("--pin-xy", default="0.55,0.30")
    p.add_argument("--bleed", action="store_true", help="(호환용·무시)")
    build(p.parse_args())
