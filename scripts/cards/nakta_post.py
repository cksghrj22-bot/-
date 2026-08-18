#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""낙타폼 자막바 게시물 렌더 — 차노 배치규칙 정본 그대로.

규칙(정본):
 · 글자폭 직각 박스. 전체 폭 바자막 금지. 하단 고정 금지.
 · 좌측정렬 · 계단배치. 사진 여백에 어긋나게.
 · 흰 박스(240)+검정 = 설정(윗줄) / 검정 박스(210)+흰 = 결론(아랫줄) / 시안 옵션.
 · 패딩 좌우22 상하16, 줄간격 49.  · 얼굴·피사체 위 금지.  · 무게중심 45~85%(위쪽).
"""
import os, sys, json
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
def _meta_path(out):
    from pathlib import Path as _P
    return _P(str(out)).with_suffix(".meta.json")


def F(name, size): return ImageFont.truetype(os.path.join(FONTS, name), size)

W, H = 1080, 1350
PAD_X, PAD_Y = 22, 16
GAP = 49
LONG_TEXT = 22       # 이보다 길면 「부연」 — 줄인다 (nakta_gate.LONG_TEXT 와 동일)
STEP = 46            # 계단 들여쓰기
STYLES = {
    "설정": ((255, 255, 255, 240), (20, 20, 20)),
    "결론": ((0, 0, 0, 210), (255, 255, 255)),
    "시안": ((120, 230, 245, 245), (20, 20, 20)),
}

def placeholder():
    im = Image.new("RGB", (W, H), (206, 202, 196))
    d = ImageDraw.Draw(im)
    for y in range(H):                       # 살짝 그라데이션
        d.line([(0, y), (W, y)], fill=(206 - y // 20, 202 - y // 22, 196 - y // 24))
    d.ellipse([int(W*.40), int(H*.52), int(W*.86), int(H*.98)], fill=(150, 139, 130))  # 피사체(얼굴) 자리 — 우하단
    d.text((int(W*.60), int(H*.66)), "피사체", font=F("NanumSquareRoundB.ttf", 40), fill=(232, 228, 222))
    return im

def _role_size(size, role, text=""):
    """글자 크기 위계 — 정본 「글자 크기 위계 개정2」(형 확정 2026-08-10).

      질문(설정) + 짧은 단언문 = 크게.  긴 부연·설명 = 작게.
      "결론은 무조건 작게"가 아니라 **핵심 단언은 크게, 긴 부연만 작게.**

    2026-08-18: 이 함수가 역할·길이와 무관하게 원본 size 를 그대로 돌려주고 있었다.
    그래서 전 슬라이드 글자가 같은 크기로 나갔다(정본이 금지한 「신문」).
    dict 를 넘기면 예전처럼 역할별 고정값이 이긴다.
    """
    if isinstance(size, dict):
        return size.get(role, size.get("default", 58))
    # 임계 22자 = nakta_gate.LONG_TEXT 와 같은 값. 렌더러와 게이트가 어긋나면 안 된다.
    n = len(text or "")
    if n <= LONG_TEXT:         # 질문·핵심 단언 = 크게 (역할 무관)
        return size
    if n <= LONG_TEXT + 8:     # 조금 긴 설명
        return max(36, int(size * 0.79))
    return max(32, int(size * 0.69))   # 긴 부연

def _fit_font(text, role, size, x):
    font_size = _role_size(size, role, text)
    while font_size > 30:
        fnt = F("NanumSquareRoundEB.ttf", font_size)
        bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), text, font=fnt)
        if x + (bb[2] - bb[0]) + 2 * PAD_X <= W - 36:
            return fnt
        font_size -= 2
    return F("NanumSquareRoundEB.ttf", font_size)

def render(photo, lines, out, size=58, top=0.30, left=0.07):
    """카드 1장 렌더 + **박스 좌표 사이드카**(<out>.meta.json) 기록.

    게이트가 픽셀에서 박스를 되짚어 추정하면 머리카락·옷을 박스로 오인한다(2026-08-18 실측).
    그릴 때 이미 아는 좌표를 남기면 게이트가 정확히 검사한다.
    """
    base = photo.convert("RGBA")
    ov = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    x0 = int(W * left); y = int(H * top)
    meta = {"canvas": [W, H], "top": top, "left": left, "base_size": size, "boxes": []}
    for i, (role, text) in enumerate(lines):
        if not text:
            continue
        box, txt = STYLES.get(role, STYLES["설정"])
        bx = x0 + i * STEP                    # 계단
        fnt = _fit_font(text, role, size, bx)
        bb = d.textbbox((0, 0), text, font=fnt)
        tw, th = bb[2]-bb[0], bb[3]-bb[1]
        bw, bh = tw + 2*PAD_X, th + 2*PAD_Y
        d.rectangle([bx, y, bx+bw, y+bh], fill=box)          # 직각 박스, 글자폭
        d.text((bx + PAD_X - bb[0], y + PAD_Y - bb[1]), text, font=fnt, fill=txt)  # 좌측정렬
        meta["boxes"].append({
            "role": role, "text": text, "font_size": fnt.size,
            "rect": [int(bx), int(y), int(bx + bw), int(y + bh)],
        })
        y += bh + GAP
    Image.alpha_composite(base, ov).convert("RGB").save(out, quality=92)
    _meta_path(out).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    O = os.path.join(HERE, "_out", "nakta"); os.makedirs(O, exist_ok=True)
    demo = [("설정", "윗줄은 설정 — 흰 박스"),
            ("결론", "아랫줄은 결론 — 검정 박스"),
            ("시안", "강조는 시안 박스")]
    render(placeholder(), demo, os.path.join(O, "demo.png"))
    print("렌더:", os.path.join(O, "demo.png"))
