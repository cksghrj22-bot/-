# 열펌의 모든 것 (7/16 특강) PPT — 앳나운 교육개편안 룩
# 밝은 종이 + 손그림 + 프리즘(분해) 도식. 이찬호 구술·확정 5장 구조.
# 5장: ①분해(성희약+'열펌'글자) ②모질·약제(크림/에멀전/겔/물) ③커트=공간+접기 ④Q&A ⑤실험(제품 포함)
# 사용: python3 content/교육/2026-07-16_열펌특강/make_ppt.py
from pptx import Presentation
from pptx.util import Inches as I, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from lxml import etree


def _dash(shape):
    ln = shape.line._get_or_add_ln()
    d = ln.find(qn('a:prstDash'))
    if d is None:
        d = etree.SubElement(ln, qn('a:prstDash'))
    d.set('val', 'dash')


# ── 앳나운 교육개편안 팔레트 ──
PAPER = RGBColor(0xF4, 0xF0, 0xE6)
INK   = RGBColor(0x24, 0x20, 0x1A)
SUB   = RGBColor(0x7A, 0x72, 0x64)
LINE  = RGBColor(0xD8, 0xD0, 0xBE)
CARD  = RGBColor(0xFB, 0xF8, 0xF1)
ACC   = RGBColor(0xB2, 0x4A, 0x2E)   # 붉은 펜
ACC2  = RGBColor(0x9A, 0x7B, 0x33)   # 오커
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
        anchor=MSO_ANCHOR.TOP, spacing=1.0):
    b = s.shapes.add_textbox(I(x), I(y), I(w), I(h))
    tf = b.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    for i, ln in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.line_spacing = spacing
        r = p.add_run(); r.text = ln
        f = r.font; f.name = FONT; f.size = Pt(size); f.color.rgb = color; f.bold = bold
        rPr = r._r.get_or_add_rPr()
        ea = rPr.find(qn('a:ea'))
        if ea is None:
            ea = rPr.makeelement(qn('a:ea'), {}); rPr.append(ea)
        ea.set('typeface', FONT)
    return b


def card(s, x, y, w, h, fill=CARD, line_c=LINE, line_w=1.25):
    shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, I(x), I(y), I(w), I(h))
    try: shp.adjustments[0] = 0.045
    except Exception: pass
    shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line_c is None: shp.line.fill.background()
    else: shp.line.color.rgb = line_c; shp.line.width = Pt(line_w)
    shp.shadow.inherit = False
    return shp


def line(s, x1, y1, x2, y2, color=INK, w=2.0):
    ln = s.shapes.add_connector(1, I(x1), I(y1), I(x2), I(y2))
    ln.line.color.rgb = color; ln.line.width = Pt(w); ln.shadow.inherit = False
    return ln


def dline(s, x1, y1, x2, y2, color=SUB, w=1.6):
    ln = line(s, x1, y1, x2, y2, color=color, w=w)
    lnEl = ln.line._get_or_add_ln()
    etree.SubElement(lnEl, qn('a:prstDash')).set('val', 'dash')
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


def stickman(s, cx, top, scale=1.0, color=INK, w=2.4, pose="stand"):
    head_r = 0.16 * scale
    hy = top + head_r
    circle(s, cx, hy, head_r, fill=None, line_c=color, w=w)
    body_top = hy + head_r
    body_bot = body_top + 0.62 * scale
    line(s, cx, body_top, cx, body_bot, color=color, w=w)
    ay = body_top + 0.16 * scale
    if pose == "look":
        line(s, cx, ay, cx - 0.34*scale, ay + 0.24*scale, color=color, w=w)
        line(s, cx, ay, cx + 0.30*scale, ay - 0.30*scale, color=color, w=w)
    else:
        line(s, cx, ay, cx - 0.32*scale, ay + 0.26*scale, color=color, w=w)
        line(s, cx, ay, cx + 0.32*scale, ay + 0.26*scale, color=color, w=w)
    line(s, cx, body_bot, cx - 0.26*scale, body_bot + 0.44*scale, color=color, w=w)
    line(s, cx, body_bot, cx + 0.26*scale, body_bot + 0.44*scale, color=color, w=w)


def prism(s, cx, cy, size=1.0, rays=None, input_label="열펌", ray_labels=True,
          in_len=1.55, label_size=17):
    """분해 도식: 빛 한 줄 → 삼각 프리즘 → 여러 갈래로 갈라짐.
    input_label=None이면 입사광 라벨 대신 '?', ray_labels=False면 출사광 라벨 숨김."""
    rays = rays or [("열", ACC), ("약", ACC2), ("커트", INK), ("공간", SUB)]
    h = 1.15 * size; w = 1.0 * size
    tri = [(cx, cy - h/2), (cx - w/2, cy + h/2), (cx + w/2, cy + h/2)]
    poly(s, tri, fill=CARD, line_c=INK, w=2.6, close=True)
    # 입사광 (왼쪽 빛 한 줄)
    line(s, cx - in_len*size, cy, cx - w/2 + 0.1*size, cy, color=INK, w=2.4)
    if input_label:
        txt(s, cx - (in_len+0.15)*size, cy - 0.52, 1.4, 0.4, input_label,
            size=label_size, color=INK, bold=True, align=PP_ALIGN.CENTER)
    else:
        txt(s, cx - (in_len+0.55)*size, cy - 0.42, 0.9, 0.7, "?",
            size=int(label_size*2.2), color=ACC, bold=True, align=PP_ALIGN.CENTER)
    # 출사광 (오른쪽 여러 갈래)
    n = len(rays); spread = 1.7 * size
    for i, (lab, c) in enumerate(rays):
        t = (i - (n-1)/2) / max(1, (n-1)/2)
        ex = cx + 2.3*size; ey = cy + t * spread
        line(s, cx + w/2 - 0.1*size, cy, ex, ey, color=c, w=2.6)
        if ray_labels:
            txt(s, ex + 0.08, ey - 0.24, 1.4, 0.46, lab, size=label_size+1, color=c, bold=True)


def kicker(s, text):
    txt(s, 0.9, 0.62, 8, 0.4, text, size=14, color=ACC, bold=True)
    line(s, 0.92, 1.08, 1.9, 1.08, color=ACC, w=2.2)


def footer(s):
    n = len(prs.slides._sldIdLst)
    line(s, 0.9, H - 0.72, W - 0.9, H - 0.72, color=LINE, w=1.0)
    txt(s, 0.9, H - 0.62, 8, 0.35, "AT NOWN 교육 · 열펌의 모든 것", size=11, color=SUB)
    txt(s, W - 1.5, H - 0.62, 1.0, 0.35, f"{n:02d} / {NSLIDES}", size=11, color=SUB, align=PP_ALIGN.RIGHT)


def title(s, text, size=40):
    txt(s, 0.9, 1.35, 11.5, 1.1, text, size=size, color=INK, bold=True)


# ══ 1. 도입 — 갈라짐 도식만 (단독 한 장, 다른 요소 없음) ══
s = slide("오프닝. 워드월 직후. 갈라짐 도식 하나만 화면에. 아무 말 없이 '?'가 프리즘을 지나 여러 갈래로 갈라진다. '이게 뭘까요?' 궁금증만 남긴다. 다음 장에서 열펌이 들어간다.")
prism(s, 6.55, 3.75, size=1.55, input_label=None, ray_labels=False, in_len=1.9, label_size=20)

# ══ 2. 표지 — 이제 '열펌'이 들어간다 (앞 장의 갈라짐 = 열펌을 쪼갠 것) ══
s = slide("도입 도식의 reveal + 제목. 앞 장의 갈라짐이 곧 '열펌'을 쪼갠 것이었다. 이제 열펌이 프리즘으로 들어가 열·약·커트·공간으로 갈라진다.")
txt(s, 0.95, 0.7, 6, 0.4, "AT NOWN 교육 · 특강", size=15, color=ACC, bold=True)
line(s, 0.97, 1.12, 2.1, 1.12, color=ACC, w=2.2)
txt(s, 0.9, 2.4, 8.2, 2.4, "열펌의 모든 것", size=74, color=INK, bold=True)
txt(s, 0.95, 4.2, 8, 0.8, "— 분해하다", size=34, color=SUB)
txt(s, 0.95, 5.5, 8, 0.5, "차노 · 2026. 7. 16 · 앳나운플레이스 3F", size=16, color=SUB)
prism(s, 9.8, 3.9, size=1.0, input_label="열펌", ray_labels=True)

# ══ 2. 오늘의 지도 (5장) ══
s = slide("공부는 분해에서 시작. 오늘은 하나를 깊게 파는 날이 아니라 브레인스토밍처럼 넓게 몇 가지를 집어보는 날. 5개 순서.")
kicker(s, "오늘의 지도")
title(s, "공부한다는 건, 분해한다는 것")
steps = [("01", "분해", "약과 '열펌'을 쪼갠다"),
         ("02", "모질·약제", "크림·에멀전·겔·물"),
         ("03", "커트=공간", "펌이 살아났다 · 접기"),
         ("04", "Q&A", "궁금한 것부터"),
         ("05", "실험", "모다발 · 제품 비교")]
for i, (n, t, d) in enumerate(steps):
    x = 0.9 + i * 2.42
    card(s, x, 2.8, 2.22, 2.4)
    txt(s, x + 0.25, 3.02, 1.8, 0.5, n, size=19, color=ACC, bold=True)
    line(s, x + 0.27, 3.52, x + 0.85, 3.52, color=LINE, w=1.2)
    txt(s, x + 0.25, 3.66, 1.85, 0.9, t, size=22, color=INK, bold=True, spacing=1.05)
    txt(s, x + 0.25, 4.5, 1.85, 0.7, d, size=13.5, color=SUB, spacing=1.1)
txt(s, 0.9, 5.7, 11.5, 0.7, "쪼개봐야 내 것이 됩니다.", size=24, color=INK)
footer(s)

# ══ 3. Ch1 분해 — '열펌' 글자부터 쪼갠다 ══
s = slide("가장 먼저 '열펌'이란 글자 그 자체를 쪼갠다. 열 + 펌. 열은 왜 필요한가, 펌이란 무엇인가. 롤러볼의 간접열과 판이 직접 닿는 디지털·세팅의 열은 같은 열인가?")
kicker(s, "① 분해 — '열펌'이라는 말")
title(s, "'열펌'이라는 말부터 쪼갭니다")
txt(s, 1.0, 2.75, 2.4, 1.0, "열", size=90, color=INK, bold=True, align=PP_ALIGN.CENTER)
txt(s, 3.2, 2.75, 2.4, 1.0, "펌", size=90, color=INK, bold=True, align=PP_ALIGN.CENTER)
dline(s, 2.95, 2.7, 2.95, 5.0, color=ACC, w=2.0)
txt(s, 6.0, 3.0, 6.4, 0.9, "열은 왜 필요한가?", size=27, color=INK, bold=True)
txt(s, 6.0, 3.95, 6.4, 0.9, "펌이란 무엇인가?", size=27, color=INK, bold=True)
txt(s, 6.0, 5.0, 6.4, 1.0, "롤러볼의 열과, 판이 직접 닿는 열은\n같은 열일까요?", size=18, color=SUB, spacing=1.2)
footer(s)

# ══ 4. 열의 특성 게이지 ══
s = slide("40~55도는 수분·시간이 일하는 저온. 100도 넘으면 수분 날리며 형태 굳힘. 140도부터 단백질 변형. 열펌=열로 사람을 편하게. 열은 적이 아니라 도구.")
kicker(s, "① 분해 — 열")
title(s, "열마다 하는 일이 다릅니다")
bx, by, bw = 1.0, 3.4, 11.3
line(s, bx, by, bx + bw, by, color=INK, w=2.0)
seg = [(0.02, "40–55°C", "수분과 시간이 일하는 구간\n건강한 물결 · 저온 세팅", ACC2),
       (0.40, "100°C +", "수분을 날리며\n형태를 굳히는 구간", INK),
       (0.74, "140°C ~", "단백질 변형이\n시작되는 선", ACC)]
for off, temp, desc, c in seg:
    x = bx + off * bw
    line(s, x, by - 0.12, x, by + 0.12, color=c, w=3.0)
    txt(s, x - 0.3, by - 0.95, 3, 0.6, temp, size=24, color=c, bold=True)
    txt(s, x - 0.15, by + 0.3, 3.4, 1.2, desc, size=15, color=SUB, spacing=1.15)
txt(s, 0.9, 5.5, 11.5, 1.2, "열펌은 열로 사람을 편하게 만드는 시술입니다.\n열은 적이 아니라 도구예요.", size=24, color=INK, spacing=1.2)
footer(s)

# ══ 5. 약을 쪼개면 (성희 부원장 해석) ══
s = slide("성희 부원장이 쓰던 약을 내가 직접 분해해봤다. 열펌제=연화제+환원제. 팩(점증)이 과연화를 막는 브레이크라 꾸덕. 환원제가 결합 풀어 부드럽게, 과하지 않게 컬. 남의 약도 분해하면 내 것.")
kicker(s, "① 분해 — 약 (직접 분해해 본 것)")
title(s, "약도 쪼개집니다")
comp = [("연화제", "머리를 부드럽게\n여는 힘", ACC2),
        ("팩 · 점증", "과연화를 막는 브레이크\n약이 꾸덕한 진짜 이유", INK),
        ("환원제", "결합을 풀어\n컬을 만드는 힘", ACC)]
for i, (t, d, c) in enumerate(comp):
    x = 0.9 + i * 4.0
    card(s, x, 2.75, 3.5, 2.15)
    line(s, x + 0.3, 3.15, x + 0.85, 3.15, color=c, w=3.0)
    txt(s, x + 0.3, 3.25, 3.0, 0.6, t, size=25, color=INK, bold=True)
    txt(s, x + 0.3, 3.95, 3.0, 0.9, d, size=15, color=SUB, spacing=1.15)
    if i < 2:
        txt(s, x + 3.5, 3.4, 0.5, 0.7, "+", size=30, color=SUB, bold=True, align=PP_ALIGN.CENTER)
txt(s, 0.9, 5.5, 11.5, 1.1, "남이 쓰던 약도 분해해 보면 내 것이 됩니다.\n외우는 약은 남의 약, 쪼개본 약이 내 약입니다.", size=22, color=INK, spacing=1.2)
footer(s)

# ══ 6. Ch2 모질·약제 구분 — 텍스처(제형)와 물 ══
s = slide("두 번째: 손상·모질에 따른 약제 구분. 크림·에멀전·겔·물(수분). 크림은 침투제 많아 녹이는 힘 강함(강곱슬·건강모). 에멀전은 중간. 겔·액체는 못 녹이는 대신 섬세 컨트롤(손상모). 물=수분 컨트롤. 좋은 약이 아니라 맞는 약.")
kicker(s, "② 모질 · 약제 구분")
title(s, "손상과 모질에 약제를 맞춥니다", size=36)
types = [("크림", "침투제 ↑ · 녹이는 힘 강\n강곱슬 · 건강모", ACC),
         ("에멀전", "중간 · 균형형\n대부분의 모발", INK),
         ("겔 · 액체", "못 녹임 · 섬세 컨트롤\n손상모 · 미세 조정", ACC2),
         ("물 (수분)", "녹이지 않고\n수분·열을 조율", SUB)]
for i, (t, d, c) in enumerate(types):
    x = 0.9 + i * 3.0
    card(s, x, 2.7, 2.75, 2.5)
    line(s, x + 0.3, 3.1, x + 0.85, 3.1, color=c, w=3.0)
    txt(s, x + 0.3, 3.2, 2.3, 0.6, t, size=22, color=INK, bold=True)
    txt(s, x + 0.3, 3.95, 2.25, 1.1, d, size=14, color=SUB, spacing=1.15)
txt(s, 0.9, 5.7, 11.5, 0.7, "좋은 약은 없습니다. 이 모발에 맞는 약이 있을 뿐입니다.", size=22, color=INK)
footer(s)

# ══ 7. 그림으로 보는 곱슬 (사진 자리) ══
s = slide("이론 텍스트가 아니라 그림으로. 옛날부터 쓰던 곱슬 모양표 + 연화·볼륨 줄며 이미지 달라지는 표. 핀터레스트 스타일 이미지로 채우기.")
kicker(s, "② 모질 · 약제 구분 — 그림으로")
title(s, "말이 아니라, 그림으로 봅니다")
for x, lab in [(0.9, "곱슬 모양표\n(기존 곱슬 특성표)"), (6.9, "연화·볼륨 변화 →\n이미지가 달라지는 표")]:
    sh = card(s, x, 2.7, 5.5, 3.4, fill=PAPER, line_c=SUB, line_w=1.4)
    _dash(sh)
    txt(s, x, 4.0, 5.5, 0.9, f"◻︎  {lab}", size=17, color=SUB, align=PP_ALIGN.CENTER, spacing=1.2)
footer(s)

# ══ 8. Ch3 커트=공간 — 접기(숟가락 점선) ══
s = slide("세 번째: 커트와 펌은 공간의 문제. 같은 C컬, 접힐 자리를 커트로 얇게 걷어내면(숟가락으로 콘푸라이트 뜨듯 점선 자리) 열 100이 아니라 50으로 같은 컬. 손상 절반, 약도 순하게. 커트는 펌의 보조가 아니라 절반.")
kicker(s, "③ 커트 = 공간 — 접기")
title(s, "접힐 자리를 만들면, 힘이 절반")
# 접기 도식: 모발 다발 + 점선(걷어낼 자리) + 접힘
line(s, 1.3, 3.0, 1.3, 5.2, color=INK, w=2.4)
for yy in (3.2, 3.6, 4.0, 4.4, 4.8):
    line(s, 1.3, yy, 2.2, yy, color=INK, w=1.6)
dline(s, 2.35, 3.9, 3.4, 3.9, color=ACC, w=2.0)
txt(s, 2.35, 3.45, 2.6, 0.4, "걷어낼 자리 (점선)", size=13, color=ACC, bold=True)
poly(s, [(3.9, 4.6), (4.6, 3.7), (5.3, 4.6)], fill=None, line_c=INK, w=2.4, close=False)
txt(s, 3.7, 4.7, 1.8, 0.4, "쉽게 접힘", size=14, color=SUB, align=PP_ALIGN.CENTER)
card(s, 6.6, 2.9, 5.8, 2.5)
txt(s, 6.9, 3.15, 5.2, 0.6, "커트 없이  →  열 100의 힘", size=21, color=SUB, bold=True)
txt(s, 6.9, 3.85, 5.2, 0.6, "걷어내면  →  열 50의 힘", size=24, color=ACC, bold=True)
txt(s, 6.9, 4.6, 5.2, 0.6, "같은 C컬 · 손상 절반 · 약도 순하게", size=15, color=SUB)
txt(s, 0.9, 5.75, 11.5, 0.7, "커트는 펌의 보조가 아니라 절반입니다.", size=23, color=INK)
footer(s)

# ══ 9. 작용과 반작용 ══
s = slide("걷어내면 잘 접힌다(작용). 너무 걷어내면 부스스해진다(반작용). 매 커트마다 무엇을 취하고 무엇을 버릴지.")
kicker(s, "③ 커트 = 공간")
title(s, "모든 가위질엔 작용과 반작용이 있습니다", size=36)
card(s, 0.9, 2.7, 5.5, 2.3)
txt(s, 0.9, 2.95, 5.5, 0.6, "작용", size=23, color=ACC2, bold=True, align=PP_ALIGN.CENTER)
txt(s, 1.2, 3.65, 5.0, 1.0, "걷어내면\n컬이 잘 접힙니다", size=19, color=SUB, align=PP_ALIGN.CENTER, spacing=1.15)
card(s, 6.9, 2.7, 5.5, 2.3)
txt(s, 6.9, 2.95, 5.5, 0.6, "반작용", size=23, color=ACC, bold=True, align=PP_ALIGN.CENTER)
txt(s, 7.2, 3.65, 5.0, 1.0, "너무 걷어내면\n부스스해집니다", size=19, color=SUB, align=PP_ALIGN.CENTER, spacing=1.15)
txt(s, 0.9, 5.4, 11.6, 1.2, "매 커트마다 묻습니다. 무엇을 얻고, 무엇을 버릴 것인가.", size=23, color=INK)
footer(s)

# ══ 10. 이제야 보이는 것 (펌이 살아났다) ══
s = slide("'펌이 살아났어요'가 아니라 '이제야 보여요'. 검은 바탕 위 검은 줄은 안 보인다. 바탕이 밝아질수록 보인다. 공간이 생겨야 컬이 보인다. 강하게 말았는데 금방 풀려 보이면 공간이 없는 것 — 디자이너 몫.")
kicker(s, "③ 커트 = 공간")
title(s, "'살아난' 게 아니라, '이제야 보이는' 겁니다", size=34)
c1 = card(s, 1.2, 2.75, 4.6, 2.6, fill=RGBColor(0x20,0x1C,0x17), line_c=None)
for i in range(3):
    a = s.shapes.add_shape(MSO_SHAPE.BLOCK_ARC, I(1.75 + i*1.35), I(3.5), I(1.0), I(1.2))
    a.fill.solid(); a.fill.fore_color.rgb = RGBColor(0x2A,0x26,0x20); a.line.fill.background(); a.shadow.inherit = False
txt(s, 1.2, 5.45, 4.6, 0.5, "공간이 없으면 — 컬이 안 보입니다", size=14, color=SUB, align=PP_ALIGN.CENTER)
c2 = card(s, 7.5, 2.75, 4.6, 2.6, fill=CARD, line_c=LINE)
for i in range(3):
    a = s.shapes.add_shape(MSO_SHAPE.BLOCK_ARC, I(8.05 + i*1.35), I(3.5), I(1.0), I(1.2))
    a.fill.solid(); a.fill.fore_color.rgb = INK; a.line.fill.background(); a.shadow.inherit = False
txt(s, 7.5, 5.45, 4.6, 0.5, "공간이 생기면 — 같은 컬이 보입니다", size=14, color=INK, align=PP_ALIGN.CENTER)
txt(s, 0.9, 6.15, 11.6, 0.8, "펌이 금방 풀린 게 아니라 공간이 없었던 겁니다. 그건 디자이너의 몫입니다.", size=20, color=INK)
footer(s)

# ══ 11. Ch4 Q&A ══
s = slide("네 번째: Q&A. 워드월에 올라온 '궁금한 것'을 여기서 함께 푼다. 못 다룬 건 시트에 남아 다음 교육 소재로.")
kicker(s, "④ Q & A")
txt(s, 0.9, 2.3, 11.5, 1.4, "궁금한 것부터,\n같이 풀어봅시다", size=52, color=INK, bold=True, spacing=1.2)
line(s, 0.95, 4.7, 6.0, 4.7, color=ACC, w=2.2)
txt(s, 0.9, 4.95, 11.5, 0.9, "워드월에 올라온 질문을 화면에 띄우고, 비슷한 것끼리 묶어 함께 답합니다.", size=19, color=SUB)
stickman(s, 11.2, 2.2, scale=1.2, pose="stand")
footer(s)

# ══ 12. Ch5 실험 — 모다발 테스트 (제품 포함) ══
s = slide("다섯 번째: 실험. 모다발로 제품별 비교. PB, 이찌마루, 아모스 S, 시세이도 M — 같은 모다발을 나눠 제품만 바꿔 결과를 눈으로. 이번 과정의 확인이자 숙제.")
kicker(s, "⑤ 실험 — 모다발 테스트")
title(s, "제품을 바꿔, 눈으로 확인합니다", size=36)
prods = [("PB", ACC), ("이찌마루", INK), ("아모스 S", ACC2), ("시세이도 M", SUB)]
for i, (t, c) in enumerate(prods):
    x = 0.9 + i * 3.0
    card(s, x, 2.7, 2.75, 2.4)
    circle(s, x + 1.375, 3.5, 0.28, fill=None, line_c=c, w=2.4)
    txt(s, x, 4.0, 2.75, 0.6, t, size=20, color=INK, bold=True, align=PP_ALIGN.CENTER)
    txt(s, x, 4.55, 2.75, 0.4, "모다발 ½", size=13, color=SUB, align=PP_ALIGN.CENTER)
txt(s, 0.9, 5.55, 11.6, 1.1, "같은 모다발을 나눠 제품만 바꿉니다. 조건은 하나만 — 그래야 차이가 제품의 것이 됩니다.", size=20, color=INK, spacing=1.2)
footer(s)

# ══ 13. 실험 기록법 ══
s = slide("실험은 기록이 실력. 한 모다발=한 데이터. 진단→선택(제품·온도·시간)→결과 사진→다음에 바꿀 것 한 줄. 감이 아니라 데이터로 는다.")
kicker(s, "⑤ 실험 — 기록법")
title(s, "한 모다발 = 한 데이터", size=38)
rec = [("진단", "모질 · 손상 · 곱슬 비율"),
       ("선택", "제품 · 온도 · 시간"),
       ("결과", "비교 사진"),
       ("다음", "바꿀 것 한 줄")]
for i, (t, d) in enumerate(rec):
    x = 0.9 + i * 3.0
    card(s, x, 2.9, 2.5, 1.9)
    txt(s, x + 0.25, 3.1, 2.0, 0.5, f"0{i+1}", size=16, color=ACC, bold=True)
    txt(s, x + 0.25, 3.55, 2.1, 0.5, t, size=23, color=INK, bold=True)
    txt(s, x + 0.25, 4.15, 2.1, 0.6, d, size=13, color=SUB, spacing=1.1)
    if i < 3:
        txt(s, x + 2.5, 3.55, 0.5, 0.5, "→", size=22, color=SUB, align=PP_ALIGN.CENTER)
txt(s, 0.9, 5.35, 11.6, 1.1, "같은 모다발을 반 갈라 조건 하나만 바꿔 비교하세요.\n감이 아니라 데이터로 늡니다.", size=20, color=INK, spacing=1.2)
footer(s)

# ══ 14. 마무리 ══
s = slide("클로징. 워드월로 돌아가 '지금 다시 쓰면 열펌이란?' 한 번 더. 숙제: 배운 점 정리 + 모다발 비교 사진 PDF(조건 하나만 바꿔).")
txt(s, 0.9, 0.9, 6, 0.4, "닫으며", size=15, color=ACC, bold=True)
line(s, 0.92, 1.35, 1.7, 1.35, color=ACC, w=2.2)
txt(s, 0.9, 2.1, 11.6, 2.0, "열펌은, 쪼갤수록 쉬워집니다.", size=46, color=INK, bold=True)
prism(s, 10.6, 2.15, size=0.58)
line(s, 0.9, 4.5, 12.4, 4.5, color=LINE, w=1.0)
txt(s, 0.9, 4.8, 11.5, 0.5, "숙제", size=15, color=SUB, bold=True)
txt(s, 0.9, 5.3, 11.6, 1.3, "① 배운 점 · 느낀 점 정리\n② 모다발 비교 사진 PDF — 조건은 하나만 바꿔서 (같은 모다발, 제품만)", size=21, color=INK, spacing=1.35)
footer(s)

out = "content/교육/2026-07-16_열펌특강/열펌의모든것_v3.pptx"
prs.save(out)
print(f"저장: {out} · {len(prs.slides._sldIdLst)}장")
