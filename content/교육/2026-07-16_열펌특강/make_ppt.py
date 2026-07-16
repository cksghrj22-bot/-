# 열펌의 모든 것 (7/16 특강) — 앳나운 교육개편안 디자인 시스템 정본 이식
# 개편안 실물 기준: 순백 배경 · 검정 볼드 · 골드 점 + 검정 원 강조 · 연회색 카드 ·
# 제목+얇은 구분선 · 하단 중앙 AT NOWN 푸터 · 속 찬 검은 졸라맨 · 큰 중앙 문장 · 노드 플로우.
# 설명글 최소(강사가 말로). 사용: python3 content/교육/2026-07-16_열펌특강/make_ppt.py
from pptx import Presentation
from pptx.util import Inches as I, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from lxml import etree

# ── 개편안 팔레트 ──
BG    = RGBColor(0xFF, 0xFF, 0xFF)   # 순백
INK   = RGBColor(0x1C, 0x1C, 0x1C)   # 검정
SUB   = RGBColor(0x80, 0x80, 0x80)   # 회색 (보조·푸터)
CARD  = RGBColor(0xF2, 0xF1, 0xED)   # 연회색 카드
GOLD  = RGBColor(0xB8, 0x91, 0x2E)   # 골드 점 강조
DIV   = RGBColor(0xE4, 0xE3, 0xDF)   # 구분선
FONT = "Noto Sans CJK KR"

prs = Presentation()
prs.slide_width, prs.slide_height = I(13.333), I(7.5)
BLANK = prs.slide_layouts[6]
W, H = 13.333, 7.5


def slide(notes=""):
    s = prs.slides.add_slide(BLANK)
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    r.fill.solid(); r.fill.fore_color.rgb = BG; r.line.fill.background(); r.shadow.inherit = False
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def txt(s, x, y, w, h, text, size=24, color=INK, bold=False, align=PP_ALIGN.LEFT,
        anchor=MSO_ANCHOR.TOP, spacing=1.0, spc=0.0):
    b = s.shapes.add_textbox(I(x), I(y), I(w), I(h))
    tf = b.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    for i, ln in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.line_spacing = spacing
        r = p.add_run(); r.text = ln
        f = r.font; f.name = FONT; f.size = Pt(size); f.color.rgb = color; f.bold = bold
        rPr = r._r.get_or_add_rPr()
        if spc:
            rPr.set('spc', str(int(spc * 100)))
        ea = rPr.find(qn('a:ea'))
        if ea is None:
            ea = rPr.makeelement(qn('a:ea'), {}); rPr.append(ea)
        ea.set('typeface', FONT)
    return b


def line(s, x1, y1, x2, y2, color=INK, w=2.0):
    ln = s.shapes.add_connector(1, I(x1), I(y1), I(x2), I(y2))
    ln.line.color.rgb = color; ln.line.width = Pt(w); ln.shadow.inherit = False
    return ln


def dline(s, x1, y1, x2, y2, color=GOLD, w=1.6):
    ln = line(s, x1, y1, x2, y2, color=color, w=w)
    etree.SubElement(ln.line._get_or_add_ln(), qn('a:prstDash')).set('val', 'dash')
    return ln


def disc(s, cx, cy, r, fill=INK, line_c=None, w=2.0):
    shp = s.shapes.add_shape(MSO_SHAPE.OVAL, I(cx - r), I(cy - r), I(2*r), I(2*r))
    if fill is None: shp.fill.background()
    else: shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line_c is None: shp.line.fill.background()
    else: shp.line.color.rgb = line_c; shp.line.width = Pt(w)
    shp.shadow.inherit = False
    return shp


def rrect(s, x, y, w, h, fill=CARD, line_c=None, line_w=1.0, rad=0.06):
    shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, I(x), I(y), I(w), I(h))
    try: shp.adjustments[0] = rad
    except Exception: pass
    if fill is None: shp.fill.background()
    else: shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line_c is None: shp.line.fill.background()
    else: shp.line.color.rgb = line_c; shp.line.width = Pt(line_w)
    shp.shadow.inherit = False
    return shp


def poly(s, pts, fill=None, line_c=INK, w=2.0, close=True):
    x0, y0 = pts[0]
    fb = s.shapes.build_freeform(Emu(int(I(x0))), Emu(int(I(y0))), scale=1)
    fb.add_line_segments([(Emu(int(I(x))), Emu(int(I(y)))) for x, y in pts[1:]], close=close)
    shp = fb.convert_to_shape()
    if fill is None: shp.fill.background()
    else: shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line_c is None: shp.line.fill.background()
    else: shp.line.color.rgb = line_c; shp.line.width = Pt(w)
    shp.shadow.inherit = False
    return shp


def figure(s, cx, ground_y, scale=1.0):
    """개편안 졸라맨 — 속이 꽉 찬 검은 실루엣이 바닥선 위에 선다."""
    hr = 0.30 * scale
    body_w = 0.52 * scale; body_h = 0.82 * scale
    leg_h = 0.55 * scale
    body_bot = ground_y - leg_h
    body_top = body_bot - body_h
    head_cy = body_top - hr + 0.06 * scale
    # 바닥선
    line(s, cx - 3.4*scale, ground_y, cx + 3.4*scale, ground_y, color=INK, w=1.4)
    # 다리
    line(s, cx - 0.13*scale, body_bot, cx - 0.13*scale, ground_y, color=INK, w=int(7*scale))
    line(s, cx + 0.13*scale, body_bot, cx + 0.13*scale, ground_y, color=INK, w=int(7*scale))
    # 몸통
    rrect(s, cx - body_w/2, body_top, body_w, body_h, fill=INK, rad=0.22)
    # 팔 (살짝 벌림)
    ay = body_top + 0.18*scale
    line(s, cx - body_w/2, ay, cx - body_w/2 - 0.42*scale, ay - 0.02*scale, color=INK, w=int(7*scale))
    line(s, cx + body_w/2, ay, cx + body_w/2 + 0.42*scale, ay - 0.02*scale, color=INK, w=int(7*scale))
    # 머리
    disc(s, cx, head_cy, hr, fill=INK)


def split_buddy(s, cx, cy, scale=1.0):
    """쪼개다 캐릭터 — 동그란 친구 하나가 둘로 사이좋게 쪼개진다.
    검정 블롭 + 흰 눈·입 + 가운데 골드 점선 틈 + 좌우 갈라짐 모션."""
    r = 0.62 * scale
    gap = 0.5 * scale
    for side in (-1, 1):
        bx = cx + side * (r + gap / 2)
        disc(s, bx, cy, r, fill=INK)                       # 몸
        ey = cy - 0.10 * scale
        disc(s, bx - 0.18 * scale, ey, 0.068 * scale, fill=BG)   # 왼눈
        disc(s, bx + 0.18 * scale, ey, 0.068 * scale, fill=BG)   # 오른눈
        disc(s, bx, cy + 0.19 * scale, 0.05 * scale, fill=BG)    # 입
    # 쪼개진 자리 (골드 점선 틈)
    dline(s, cx, cy - r - 0.22 * scale, cx, cy + r + 0.22 * scale, color=GOLD, w=2.0)
    # 갈라짐 모션 — 좌우로 튀어나가는 작은 점선
    dline(s, cx - r * 2.15, cy, cx - r * 2.75, cy, color=GOLD, w=2.0)
    dline(s, cx + r * 2.15, cy, cx + r * 2.75, cy, color=GOLD, w=2.0)


def title(s, text, size=28):
    txt(s, 0.9, 0.66, 11.5, 0.9, text, size=size, color=INK, bold=True)
    line(s, 0.9, 1.58, 12.43, 1.58, color=DIV, w=1.4)


def subline(s, text):
    txt(s, 0.9, 1.7, 11.5, 0.5, text, size=13, color=SUB)


def footer(s):
    n = len(prs.slides._sldIdLst)
    txt(s, 0, H - 0.62, W, 0.35, "AT NOWN", size=11, color=SUB, bold=True, align=PP_ALIGN.CENTER, spc=2.0)
    txt(s, W - 1.3, H - 0.62, 0.9, 0.3, f"{n}", size=11, color=SUB, align=PP_ALIGN.RIGHT)


def numbered(s, n, y, head, sub):
    disc(s, 1.25, y + 0.26, 0.25, fill=INK)
    txt(s, 1.0, y + 0.04, 0.5, 0.45, str(n), size=15, color=BG, bold=True, align=PP_ALIGN.CENTER)
    txt(s, 1.85, y, 10, 0.5, head, size=20, color=INK, bold=True)
    txt(s, 1.85, y + 0.48, 10, 0.45, sub, size=13, color=SUB)


def dotcard(s, x, y, w, h, label, sub=""):
    rrect(s, x, y, w, h, fill=CARD)
    disc(s, x + w/2, y + 0.52, 0.06, fill=GOLD)
    txt(s, x, y + h/2 - 0.26, w, 0.5, label, size=18, color=INK, bold=True, align=PP_ALIGN.CENTER)
    if sub:
        txt(s, x, y + h/2 + 0.2, w, 0.4, sub, size=12, color=SUB, align=PP_ALIGN.CENTER)


def bigcenter(s, text, size=42):
    txt(s, 0.6, 0, 12.1, H - 0.4, text, size=size, color=INK, bold=True,
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, spacing=1.2)


def node(s, cx, cy, r, label, sub="", dark=False):
    disc(s, cx, cy, r, fill=(INK if dark else CARD), line_c=(None if dark else DIV), w=1.5)
    col = BG if dark else INK
    if sub:
        txt(s, cx - r, cy - 0.32, 2*r, 0.4, label, size=15, color=col, bold=True, align=PP_ALIGN.CENTER)
        txt(s, cx - r, cy + 0.06, 2*r, 0.35, sub, size=12, color=(BG if dark else SUB), align=PP_ALIGN.CENTER)
    else:
        txt(s, cx - r, cy - 0.2, 2*r, 0.45, label, size=16, color=col, bold=True, align=PP_ALIGN.CENTER)


# ══ 1. 표지 ══
s = slide()
txt(s, 0.9, 2.6, 11.5, 1.5, "열펌의 모든 것", size=56, color=INK, bold=True)
txt(s, 0.92, 4.05, 8, 0.7, "분해하다", size=23, color=SUB)
txt(s, 0.92, 6.35, 8, 0.4, "차노 · 2026. 7. 16 · 앳나운플레이스 3F", size=14, color=SUB)
txt(s, 0, H - 0.62, W, 0.35, "AT NOWN", size=11, color=SUB, bold=True, align=PP_ALIGN.CENTER, spc=2.0)

# ══ 2. 열펌 = 열 | 펌 ══
s = slide()
title(s, "열펌")
txt(s, 2.7, 2.9, 3.0, 2.0, "열", size=100, color=INK, bold=True, align=PP_ALIGN.CENTER)
dline(s, 6.2, 2.9, 6.2, 5.7, color=GOLD, w=2.0)
txt(s, 6.7, 2.9, 3.0, 2.0, "펌", size=100, color=INK, bold=True, align=PP_ALIGN.CENTER)
footer(s)

# ══ 3. 약을 쪼갠다 — 연화제·팩·환원제 ══
s = slide()
title(s, "약")
for i, t in enumerate(["연화제", "팩", "환원제"]):
    dotcard(s, 1.55 + i * 3.5, 3.3, 3.0, 2.0, t)
footer(s)

# ══ 4. 모질과 손상도 ══
s = slide()
title(s, "모질 · 손상도")
for i, t in enumerate(["모질", "손상도"]):
    dotcard(s, 2.3 + i * 4.8, 3.3, 4.0, 2.0, t)
footer(s)

# ══ 5. 제품은 점성으로 셋 — 크림·에멀전·겔 ══
s = slide()
title(s, "제품 · 점성")
for i, t in enumerate(["크림", "에멀전", "겔"]):
    dotcard(s, 1.55 + i * 3.5, 3.3, 3.0, 2.0, t)
footer(s)

# ══ 6. 커트, 두 가지 — 접기 / 공간 ══
s = slide()
title(s, "커트")
for i, t in enumerate(["접는 커트", "공간을 만드는 커트"]):
    dotcard(s, 2.3 + i * 4.8, 3.3, 4.0, 2.0, t)
footer(s)

# ══ 7. 모다발 테스트 ══
s = slide()
title(s, "모다발")
for i, t in enumerate(["모다발 ½", "모다발 ½"]):
    dotcard(s, 2.3 + i * 4.8, 3.4, 4.0, 2.0, t)
footer(s)

# ══ 8. 마무리 ══
s = slide()
split_buddy(s, 6.66, 3.7, scale=1.15)
txt(s, 0.6, 5.1, 12.1, 1.2, "쪼갤수록, 쉬워진다", size=35, color=INK, bold=True, align=PP_ALIGN.CENTER)
txt(s, 0, H - 0.62, W, 0.35, "AT NOWN", size=11, color=SUB, bold=True, align=PP_ALIGN.CENTER, spc=2.0)

out = "content/교육/2026-07-16_열펌특강/열펌의모든것_v9.pptx"
prs.save(out)
print(f"저장: {out} · {len(prs.slides._sldIdLst)}장")
