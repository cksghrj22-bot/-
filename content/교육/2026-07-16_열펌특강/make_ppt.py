# 열펌의 모든 것 (7/16 특강) PPT — 앳나운 교육개편안 룩 · 미니멀판
# 원칙(이찬호 2026-07-15): 설명글 없음(강사가 말로) · 메인 글자와 최소 도식만 · 그림은 1장만 · 여백 많게.
# 사용: python3 content/교육/2026-07-16_열펌특강/make_ppt.py
from pptx import Presentation
from pptx.util import Inches as I, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from lxml import etree

# ── 팔레트 (밝은 종이·잉크·붉은 펜 소량) ──
PAPER = RGBColor(0xF4, 0xF0, 0xE6)
INK   = RGBColor(0x2A, 0x26, 0x20)
SUB   = RGBColor(0x9A, 0x93, 0x85)   # 옅은 회색 (라벨·페이지)
LINE  = RGBColor(0xDD, 0xD6, 0xC7)
ACC   = RGBColor(0xB2, 0x4A, 0x2E)   # 붉은 펜 — 아주 조금만
FONT = "Apple SD Gothic Neo"

prs = Presentation()
prs.slide_width, prs.slide_height = I(13.333), I(7.5)
BLANK = prs.slide_layouts[6]
W, H = 13.333, 7.5
NSLIDES = 15


def slide(notes=""):
    s = prs.slides.add_slide(BLANK)
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    r.fill.solid(); r.fill.fore_color.rgb = PAPER; r.line.fill.background(); r.shadow.inherit = False
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


def dline(s, x1, y1, x2, y2, color=LINE, w=1.4):
    ln = line(s, x1, y1, x2, y2, color=color, w=w)
    etree.SubElement(ln.line._get_or_add_ln(), qn('a:prstDash')).set('val', 'dash')
    return ln


def circle(s, cx, cy, r, fill=None, line_c=INK, w=2.0):
    shp = s.shapes.add_shape(MSO_SHAPE.OVAL, I(cx - r), I(cy - r), I(2*r), I(2*r))
    if fill is None: shp.fill.background()
    else: shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line_c is None: shp.line.fill.background()
    else: shp.line.color.rgb = line_c; shp.line.width = Pt(w)
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


def tag(s, text):
    # 아주 작은 섹션 라벨 (회색, 조용하게)
    txt(s, 0.95, 0.72, 8, 0.35, text, size=12, color=SUB, spc=1.5)


def pageno(s):
    n = len(prs.slides._sldIdLst)
    txt(s, W - 1.3, H - 0.62, 0.9, 0.3, f"{n:02d}", size=11, color=SUB, align=PP_ALIGN.RIGHT)


def head(s, text, size=40, y=2.9):
    # 메인 글자 — 얇은 볼드, 넉넉한 자간
    txt(s, 0.95, y, 11.4, 1.6, text, size=size, color=INK, bold=True, spacing=1.18)


def prism(s, cx, cy, size=1.55, labels=False, qmark=True):
    rays = [ACC, RGBColor(0x9A,0x7B,0x33), INK, SUB]
    names = ["열", "약", "커트", "공간"]
    h = 1.15 * size; w = 1.0 * size
    poly(s, [(cx, cy - h/2), (cx - w/2, cy + h/2), (cx + w/2, cy + h/2)],
         fill=None, line_c=INK, w=2.4, close=True)
    line(s, cx - 1.9*size, cy, cx - w/2 + 0.1*size, cy, color=INK, w=2.2)
    if qmark:
        txt(s, cx - 2.5*size, cy - 0.42, 0.9, 0.7, "?", size=44, color=ACC, bold=True, align=PP_ALIGN.CENTER)
    n = len(rays); spread = 1.7 * size
    for i, c in enumerate(rays):
        t = (i - (n-1)/2) / ((n-1)/2)
        ex = cx + 2.3*size; ey = cy + t * spread
        line(s, cx + w/2 - 0.1*size, cy, ex, ey, color=c, w=2.4)
        if labels:
            txt(s, ex + 0.12, ey - 0.24, 1.4, 0.46, names[i], size=18, color=c, bold=True)


def chips(s, items, y=3.7, cw=2.3, gap=0.35, size=25, total=None):
    n = len(items)
    span = n * cw + (n - 1) * gap
    x0 = (W - span) / 2 if total is None else total
    for i, it in enumerate(items):
        x = x0 + i * (cw + gap)
        c = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, I(x), I(y), I(cw), I(1.15))
        try: c.adjustments[0] = 0.08
        except Exception: pass
        c.fill.background(); c.line.color.rgb = LINE; c.line.width = Pt(1.4); c.shadow.inherit = False
        txt(s, x, y + 0.32, cw, 0.6, it, size=size, color=INK, bold=True, align=PP_ALIGN.CENTER)


# ══ 1. 갈라짐 도식 (단독) ══
s = slide("오프닝. 갈라짐 도식만. '?'가 프리즘을 지나 갈라진다. 강사가 말로 연다.")
prism(s, 6.55, 3.75, size=1.6, labels=False, qmark=True)

# ══ 2. 표지 (제목만, 그림 없음) ══
s = slide("제목. 그림 없음. 강사가 '오늘 이걸 쪼갭니다'로 연결.")
txt(s, 0.95, 0.9, 8, 0.4, "AT NOWN 교육 · 특강", size=13, color=SUB, spc=1.5)
txt(s, 0.9, 2.85, 11.5, 1.6, "열펌의 모든 것", size=72, color=INK, bold=True)
txt(s, 0.95, 4.5, 8, 0.7, "분해하다", size=30, color=SUB)
txt(s, 0.95, 6.2, 8, 0.4, "차노 · 2026. 7. 16 · 앳나운플레이스 3F", size=14, color=SUB)

# ══ 3. 오늘 (5장, 라벨만) ══
s = slide("오늘의 순서 5개. 강사가 말로 훑는다.")
tag(s, "TODAY")
head(s, "분해한다", size=44, y=1.5)
items = ["분해", "모질 · 약제", "커트 = 공간", "Q&A", "실험"]
for i, t in enumerate(items):
    y = 3.0 + i * 0.82
    txt(s, 1.6, y, 1.0, 0.6, f"0{i+1}", size=20, color=ACC, bold=True)
    txt(s, 2.7, y, 9, 0.6, t, size=26, color=INK, bold=True)
pageno(s)

# ══ 4. '열펌' 글자 쪼개기 (도식 = 메인) ══
s = slide("'열펌'이라는 말부터 쪼갠다. 열 | 펌. 강사가 열은 왜/펌이란 무엇/롤러볼vs판을 말로.")
tag(s, "① 분해")
txt(s, 2.6, 2.6, 3.0, 2.0, "열", size=110, color=INK, bold=True, align=PP_ALIGN.CENTER)
dline(s, 6.15, 2.5, 6.15, 5.4, color=ACC, w=2.0)
txt(s, 6.7, 2.6, 3.0, 2.0, "펌", size=110, color=INK, bold=True, align=PP_ALIGN.CENTER)
pageno(s)

# ══ 5. 열 (라벨만) ══
s = slide("열마다 하는 일이 다르다. 40-55 / 100+ / 140. 강사가 각 구간 특성 말로.")
tag(s, "① 분해 — 열")
head(s, "열마다, 하는 일이 다르다", size=40, y=1.6)
by = 4.0
line(s, 1.5, by, 11.8, by, color=LINE, w=1.6)
for off, temp, c in [(0.03, "40–55°C", INK), (0.42, "100°C +", INK), (0.78, "140°C ~", ACC)]:
    x = 1.5 + off * 10.3
    circle(s, x, by, 0.05, fill=c, line_c=None)
    txt(s, x - 1.0, by - 0.75, 2.0, 0.5, temp, size=22, color=c, bold=True, align=PP_ALIGN.CENTER)
pageno(s)

# ══ 6. 약 (라벨만) ══
s = slide("약도 쪼갠다. 연화제·팩·환원제. 강사가 성희 약 분해 해석을 말로.")
tag(s, "① 분해 — 약")
head(s, "약도, 쪼개진다", size=40, y=1.6)
chips(s, ["연화제", "팩", "환원제"], y=3.7, cw=2.6, gap=0.6, size=27)
pageno(s)

# ══ 7. 모질·약제 (라벨만) ══
s = slide("손상·모질에 약제를 맞춘다. 크림·에멀전·겔·물. 강사가 각 제형 장점 말로.")
tag(s, "② 모질 · 약제")
head(s, "모질에, 약제를 맞춘다", size=40, y=1.6)
chips(s, ["크림", "에멀전", "겔", "물"], y=3.7, cw=2.35, gap=0.4, size=25)
pageno(s)

# ══ 8. 그림으로 (사진 자리) ══
s = slide("말이 아니라 그림으로. 곱슬 모양표 + 연화·볼륨 변화표. 핀터레스트 이미지로 채운다.")
tag(s, "② 모질 · 약제")
head(s, "말이 아니라, 그림으로", size=40, y=1.5)
for x in (0.95, 6.85):
    c = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, I(x), I(2.9), I(5.5), I(3.4))
    c.fill.background(); c.line.color.rgb = LINE; c.line.width = Pt(1.4); c.shadow.inherit = False
    etree.SubElement(c.line._get_or_add_ln(), qn('a:prstDash')).set('val', 'dash')

# ══ 9. 커트 = 공간 ══
s = slide("접힐 자리를 만들면 힘이 절반. 강사가 열 100 vs 50, 손상 절반 말로.")
tag(s, "③ 커트 = 공간")
head(s, "접으면, 힘이 절반", size=44, y=3.0)
pageno(s)

# ══ 10. 작용 | 반작용 ══
s = slide("모든 가위질엔 작용과 반작용. 강사가 걷어내면 접힌다 / 너무 걷어내면 부스스 말로.")
tag(s, "③ 커트 = 공간")
head(s, "작용과, 반작용", size=40, y=1.6)
txt(s, 1.6, 3.5, 5.0, 1.0, "작용", size=40, color=INK, bold=True, align=PP_ALIGN.CENTER)
txt(s, 6.0, 3.55, 1.0, 0.9, "↔", size=34, color=SUB, align=PP_ALIGN.CENTER)
txt(s, 6.7, 3.5, 5.0, 1.0, "반작용", size=40, color=ACC, bold=True, align=PP_ALIGN.CENTER)
pageno(s)

# ══ 11. 이제야 보인다 ══
s = slide("'펌이 살아났다'가 아니라 '이제야 보인다'. 공간이 있어야 컬이 보인다. 강사가 말로.")
tag(s, "③ 커트 = 공간")
head(s, "살아난 게 아니라,\n이제야 보이는 것", size=40, y=2.6)
pageno(s)

# ══ 12. Q&A ══
s = slide("Q&A. 워드월 질문을 함께 푼다.")
head(s, "궁금한 것부터", size=52, y=3.1)
pageno(s)

# ══ 13. 실험 (제품 라벨만) ══
s = slide("실험. 모다발로 제품 비교. PB·이찌마루·아모스S·시세이도M. 강사가 조건 하나만 바꾼다 말로.")
tag(s, "⑤ 실험")
head(s, "제품을 바꿔, 눈으로", size=40, y=1.6)
chips(s, ["PB", "이찌마루", "아모스 S", "시세이도 M"], y=3.7, cw=2.5, gap=0.35, size=22)
pageno(s)

# ══ 14. 기록 ══
s = slide("한 모다발 = 한 데이터. 진단→선택→결과→다음. 강사가 말로.")
tag(s, "⑤ 실험")
head(s, "한 모다발 = 한 데이터", size=40, y=1.6)
steps = ["진단", "선택", "결과", "다음"]
for i, t in enumerate(steps):
    x = 1.7 + i * 2.7
    txt(s, x, 3.7, 2.0, 0.7, t, size=26, color=INK, bold=True, align=PP_ALIGN.CENTER)
    if i < 3:
        txt(s, x + 1.9, 3.72, 0.8, 0.6, "→", size=22, color=SUB, align=PP_ALIGN.CENTER)
pageno(s)

# ══ 15. 마무리 ══
s = slide("마무리. 쪼갤수록 쉬워진다. 워드월로 돌아가 한 번 더.")
txt(s, 0.95, 0.9, 8, 0.4, "닫으며", size=13, color=SUB, spc=1.5)
head(s, "쪼갤수록,\n쉬워진다", size=54, y=2.6)
pageno(s)

out = "content/교육/2026-07-16_열펌특강/열펌의모든것_v4.pptx"
prs.save(out)
print(f"저장: {out} · {len(prs.slides._sldIdLst)}장")
