# 열펌의 모든 것 (7/16 특강) PPT — 앳나운 교육개편안 룩
# 밝은 종이 바탕 + 손그림(졸라맨) + 정돈된 시스템 구성. 이찬호 구술(2026-07-15) 기반, 15장.
# 사용: python3 content/교육/2026-07-16_열펌특강/make_ppt.py
from pptx import Presentation
from pptx.util import Inches as I, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from lxml import etree


def _dash(shape):
    """도형 테두리를 점선으로 (python-pptx enum 미지원 우회)."""
    ln = shape.line._get_or_add_ln()
    d = ln.find(qn('a:prstDash'))
    if d is None:
        d = etree.SubElement(ln, qn('a:prstDash'))
    d.set('val', 'dash')

# ── 앳나운 교육개편안 팔레트 (밝은 종이·잉크·따뜻한 강조) ──
PAPER = RGBColor(0xF4, 0xF0, 0xE6)   # 따뜻한 종이 바탕
INK   = RGBColor(0x24, 0x20, 0x1A)   # 잉크(따뜻한 먹색)
SUB   = RGBColor(0x7A, 0x72, 0x64)   # 보조 회색
LINE  = RGBColor(0xD8, 0xD0, 0xBE)   # 헤어라인
CARD  = RGBColor(0xFB, 0xF8, 0xF1)   # 카드(살짝 밝은 종이)
ACC   = RGBColor(0xB2, 0x4A, 0x2E)   # 강조(교사의 붉은 펜 — 밑줄·표시)
ACC2  = RGBColor(0x9A, 0x7B, 0x33)   # 보조 강조(오커)
FONT = "Apple SD Gothic Neo"

prs = Presentation()
prs.slide_width, prs.slide_height = I(13.333), I(7.5)
BLANK = prs.slide_layouts[6]
W, H = 13.333, 7.5


def slide(notes=""):
    s = prs.slides.add_slide(BLANK)
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    r.fill.solid(); r.fill.fore_color.rgb = PAPER; r.line.fill.background(); r.shadow.inherit = False
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def txt(s, x, y, w, h, text, size=24, color=INK, bold=False, align=PP_ALIGN.LEFT,
        anchor=MSO_ANCHOR.TOP, spacing=1.0, italic=False):
    b = s.shapes.add_textbox(I(x), I(y), I(w), I(h))
    tf = b.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.line_spacing = spacing
        r = p.add_run(); r.text = line
        f = r.font; f.name = FONT; f.size = Pt(size); f.color.rgb = color; f.bold = bold; f.italic = italic
        rPr = r._r.get_or_add_rPr()
        ea = rPr.find(qn('a:ea'))
        if ea is None:
            ea = rPr.makeelement(qn('a:ea'), {}); rPr.append(ea)
        ea.set('typeface', FONT)
    return b


def card(s, x, y, w, h, fill=CARD, line=LINE, line_w=1.25):
    shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, I(x), I(y), I(w), I(h))
    try: shp.adjustments[0] = 0.045
    except Exception: pass
    shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line is None: shp.line.fill.background()
    else: shp.line.color.rgb = line; shp.line.width = Pt(line_w)
    shp.shadow.inherit = False
    return shp


def line(s, x1, y1, x2, y2, color=INK, w=2.0, dash=None):
    ln = s.shapes.add_connector(1, I(x1), I(y1), I(x2), I(y2))
    ln.line.color.rgb = color; ln.line.width = Pt(w)
    if dash: ln.line.dash_style = dash
    ln.shadow.inherit = False
    return ln


def circle(s, cx, cy, r, fill=None, line_c=INK, w=2.0):
    shp = s.shapes.add_shape(MSO_SHAPE.OVAL, I(cx - r), I(cy - r), I(2*r), I(2*r))
    if fill is None: shp.fill.background()
    else: shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line_c is None: shp.line.fill.background()
    else: shp.line.color.rgb = line_c; shp.line.width = Pt(w)
    shp.shadow.inherit = False
    return shp


def stickman(s, cx, top, scale=1.0, color=INK, w=2.4, pose="stand"):
    """졸라맨 손그림. cx=중심 x, top=머리 위 y (인치). pose: stand / look / think"""
    head_r = 0.16 * scale
    hy = top + head_r
    circle(s, cx, hy, head_r, fill=None, line_c=color, w=w)
    body_top = hy + head_r
    body_bot = body_top + 0.62 * scale
    line(s, cx, body_top, cx, body_bot, color=color, w=w)          # 몸통
    ay = body_top + 0.16 * scale
    if pose == "look":   # 한 팔 위로 (가리키기)
        line(s, cx, ay, cx - 0.34*scale, ay + 0.24*scale, color=color, w=w)
        line(s, cx, ay, cx + 0.30*scale, ay - 0.30*scale, color=color, w=w)
    elif pose == "think":
        line(s, cx, ay, cx - 0.30*scale, ay + 0.22*scale, color=color, w=w)
        line(s, cx, ay, cx + 0.22*scale, ay - 0.18*scale, color=color, w=w)
    else:
        line(s, cx, ay, cx - 0.32*scale, ay + 0.26*scale, color=color, w=w)
        line(s, cx, ay, cx + 0.32*scale, ay + 0.26*scale, color=color, w=w)
    line(s, cx, body_bot, cx - 0.26*scale, body_bot + 0.44*scale, color=color, w=w)  # 다리
    line(s, cx, body_bot, cx + 0.26*scale, body_bot + 0.44*scale, color=color, w=w)


def kicker(s, text):
    txt(s, 0.9, 0.62, 8, 0.4, text, size=14, color=ACC, bold=True)
    line(s, 0.92, 1.08, 1.9, 1.08, color=ACC, w=2.2)


def footer(s, n):
    line(s, 0.9, H - 0.72, W - 0.9, H - 0.72, color=LINE, w=1.0)
    txt(s, 0.9, H - 0.62, 8, 0.35, "AT NOWN 교육 · 열펌의 모든 것", size=11, color=SUB)
    txt(s, W - 1.4, H - 0.62, 0.9, 0.35, f"{n:02d} / 15", size=11, color=SUB, align=PP_ALIGN.RIGHT)


def title(s, text, size=40):
    txt(s, 0.9, 1.35, 11.5, 1.1, text, size=size, color=INK, bold=True)


# ══ 1. 표지 — 홀로 선 아이가 갈라진 형태를 올려다본다 ══
s = slide("오프닝. 워드월 직후. 화면엔 아이 하나가 갈라진 덩어리를 올려다본다. '오늘은 이걸 쪼갤 겁니다'로 시작.")
txt(s, 0.95, 0.7, 6, 0.4, "AT NOWN 교육 · 특강", size=15, color=ACC, bold=True)
line(s, 0.97, 1.12, 2.1, 1.12, color=ACC, w=2.2)
txt(s, 0.9, 2.5, 8.2, 2.4, "열펌의 모든 것", size=76, color=INK, bold=True)
txt(s, 0.95, 4.35, 8, 0.8, "— 분해하다", size=34, color=SUB)
txt(s, 0.95, 5.6, 8, 0.5, "차노 · 2026. 7. 16 · 앳나운플레이스 3F", size=16, color=SUB)
# 오른쪽: 아이가 갈라진 덩어리를 올려다봄
stickman(s, 9.7, 4.2, scale=1.5, pose="look")
# 갈라진 덩어리(머리 형태) — 원을 지그재그로 가른 느낌
circle(s, 11.2, 2.7, 0.95, fill=CARD, line_c=INK, w=2.4)
fb = s.shapes.build_freeform(Emu(int(I(11.2))), Emu(int(I(1.78))), scale=1)
fb.add_line_segments([(Emu(int(I(x))), Emu(int(I(y)))) for x, y in
                      [(11.05, 2.2), (11.35, 2.65), (11.0, 3.1), (11.3, 3.55)]], close=False)
crack = fb.convert_to_shape()
crack.line.color.rgb = ACC; crack.line.width = Pt(3); crack.fill.background(); crack.shadow.inherit = False
txt(s, 11.9, 1.5, 1.2, 0.9, "?", size=60, color=ACC, bold=True)

# ══ 2. 오늘의 지도 ══
s = slide("공부는 분해에서 시작. 하나를 깊게 파는 날이 아니라 브레인스토밍처럼 넓게 몇 가지를 집어보는 날.")
kicker(s, "오늘의 지도")
title(s, "공부한다는 건, 분해한다는 것")
steps = [("01", "분해", "열과 약을 쪼갠다"),
         ("02", "회귀", "그래서, 펌은 왜 하는가"),
         ("03", "커트", "펌을 돕는 절반"),
         ("04", "확인", "Q&A · 모다발 테스트")]
for i, (n, t, d) in enumerate(steps):
    x = 0.9 + i * 3.0
    card(s, x, 2.7, 2.75, 2.5)
    txt(s, x + 0.3, 2.95, 2, 0.5, n, size=20, color=ACC, bold=True)
    line(s, x + 0.32, 3.5, x + 1.0, 3.5, color=LINE, w=1.2)
    txt(s, x + 0.3, 3.65, 2.2, 0.7, t, size=28, color=INK, bold=True)
    txt(s, x + 0.3, 4.35, 2.2, 0.8, d, size=15, color=SUB, spacing=1.1)
txt(s, 0.9, 5.7, 11.5, 0.7, "쪼개봐야 내 것이 됩니다.", size=24, color=INK)
footer(s, 2)

# ══ 3. Ch1 질문 두 개 ══
s = slide("펌이란 무엇인가, 열은 왜 필요한가부터. 롤러볼의 간접열과 판이 직접 닿는 디지털·세팅의 열은 같은 열인가?")
kicker(s, "① 분해 — 열")
txt(s, 0.9, 1.7, 11.5, 1.2, "펌이란 무엇인가?", size=52, color=INK, bold=True)
txt(s, 0.9, 3.1, 11.5, 1.2, "열은 왜 필요한가?", size=52, color=INK, bold=True)
line(s, 0.95, 4.7, 6.2, 4.7, color=ACC, w=2.2)
txt(s, 0.9, 4.95, 11.5, 1.2, "롤러볼의 열과, 판이 직접 닿는 열은 같은 열일까요?", size=24, color=SUB)
footer(s, 3)

# ══ 4. 열의 특성 게이지 ══
s = slide("40~55도는 수분·시간이 일하는 저온. 100도 넘으면 수분 날리며 형태 굳힘. 140도부터 단백질 변형. 열펌=열로 사람을 편하게. 열은 적이 아니라 도구.")
kicker(s, "① 분해 — 열")
title(s, "열마다 하는 일이 다릅니다")
bx, by, bw = 1.0, 3.4, 11.3
line(s, bx, by, bx + bw, by, color=INK, w=2.0)
seg = [(0.02, "40–55°C", "수분과 시간이 일하는 구간\n건강한 물결·저온 세팅", ACC2),
       (0.40, "100°C +", "수분을 날리며\n형태를 굳히는 구간", INK),
       (0.74, "140°C ~", "단백질 변형이\n시작되는 선", ACC)]
for off, temp, desc, c in seg:
    x = bx + off * bw
    line(s, x, by - 0.12, x, by + 0.12, color=c, w=3.0)
    txt(s, x - 0.3, by - 0.95, 3, 0.6, temp, size=24, color=c, bold=True)
    txt(s, x - 0.15, by + 0.3, 3.4, 1.2, desc, size=15, color=SUB, spacing=1.15)
txt(s, 0.9, 5.5, 11.5, 1.2, "열펌은 열로 사람을 편하게 만드는 시술입니다.\n열은 적이 아니라 도구예요.", size=24, color=INK, spacing=1.2)
footer(s, 4)

# ══ 5. 약을 쪼개면 ══
s = slide("성희 부원장 해석. 열펌제=연화제+환원제. 팩(점증)이 과연화를 막는 브레이크라 꾸덕. 환원제가 결합 풀어 부드럽게, 과하지 않게 컬. 남의 약도 분해하면 내 것.")
kicker(s, "① 분해 — 약")
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
txt(s, 0.9, 5.5, 11.5, 1.1, "남의 해석도 분해해 보면 내 것이 됩니다.\n외우는 약은 남의 약, 쪼개본 약이 내 약입니다.", size=22, color=INK, spacing=1.2)
footer(s, 5)

# ══ 6. 타입별 장점 ══
s = slide("크림=침투제 많고 녹이는 약, 강곱슬·건강모 유리. 겔·액체=못 녹이는 대신 섬세 컨트롤, 손상모 유리. 좋은 약은 없다, 맞는 약이 있을 뿐.")
kicker(s, "① 분해 — 약")
title(s, "크림이냐 겔이냐가 아니라")
card(s, 0.9, 2.7, 5.5, 2.6)
txt(s, 0.9, 2.95, 5.5, 0.6, "크림 타입", size=26, color=INK, bold=True, align=PP_ALIGN.CENTER)
line(s, 2.6, 3.55, 4.7, 3.55, color=LINE, w=1.2)
txt(s, 1.3, 3.7, 4.7, 1.5, "침투제가 풍부, 녹이는 힘이 강함\n→ 강한 곱슬 · 건강모", size=17, color=SUB, align=PP_ALIGN.CENTER, spacing=1.2)
card(s, 6.9, 2.7, 5.5, 2.6)
txt(s, 6.9, 2.95, 5.5, 0.6, "겔 · 액체 타입", size=26, color=INK, bold=True, align=PP_ALIGN.CENTER)
line(s, 8.6, 3.55, 10.7, 3.55, color=LINE, w=1.2)
txt(s, 7.3, 3.7, 4.7, 1.5, "못 녹이는 대신 섬세하게 컨트롤\n→ 손상모 · 미세 조정", size=17, color=SUB, align=PP_ALIGN.CENTER, spacing=1.2)
txt(s, 0.9, 5.7, 11.5, 0.7, "좋은 약은 없습니다. 이 모발에 맞는 약이 있을 뿐입니다.", size=23, color=INK)
footer(s, 6)

# ══ 7. 그림으로 보는 곱슬 (사진 자리) ══
s = slide("이론 텍스트가 아니라 그림으로. 옛날부터 쓰던 곱슬 모양표 + 연화·볼륨 줄며 이미지 달라지는 표. 핀터레스트 스타일.")
kicker(s, "① 분해 — 곱슬")
title(s, "말이 아니라, 그림으로 봅니다")
for x, lab in [(0.9, "곱슬 모양표\n(기존 곱슬 특성표)"), (6.9, "연화·볼륨 변화 →\n이미지가 달라지는 표")]:
    sh = card(s, x, 2.7, 5.5, 3.4, fill=PAPER, line=SUB, line_w=1.4)
    _dash(sh)
    txt(s, x, 4.0, 5.5, 0.9, f"◻︎  {lab}", size=17, color=SUB, align=PP_ALIGN.CENTER, spacing=1.2)
footer(s, 7)

# ══ 8. Ch2 회귀 ══
s = slide("다 분해했으면 다시 돌아온다. 미용은 왜 하는가. 예뻐지려고, 손질 편하려고. 이 둘을 절대 잊으면 안 된다.")
kicker(s, "② 회귀")
txt(s, 0.9, 1.5, 11.5, 1.0, "그래서, 미용은 왜 할까요?", size=44, color=INK, bold=True)
card(s, 0.9, 3.0, 5.5, 1.8)
txt(s, 0.9, 3.55, 5.5, 0.8, "예뻐지려고", size=34, color=INK, bold=True, align=PP_ALIGN.CENTER)
card(s, 6.9, 3.0, 5.5, 1.8)
txt(s, 6.9, 3.55, 5.5, 0.8, "손질이 편해지려고", size=34, color=INK, bold=True, align=PP_ALIGN.CENTER)
txt(s, 0.9, 5.3, 11.5, 1.2, "이 두 가지를 절대 잊지 않습니다.\n펌은 이 둘을 벗어난 적이 없습니다.", size=23, color=SUB, spacing=1.2)
footer(s, 8)

# ══ 9. 진짜 실력 두 가지 ══
s = slide("펌 기술은 6개월이면 는다. 진짜는 ①손상 읽는 눈 — 전 과정을 이론으로 쥐어야 실수를 찾는다, 바늘구멍에 넣듯 피드백. ②무드 보는 눈.")
kicker(s, "② 회귀")
title(s, "펌 기술은 6개월이면 늡니다", size=38)
txt(s, 0.9, 2.15, 11.5, 0.5, "진짜 실력은 두 가지에서 갈립니다", size=18, color=SUB)
card(s, 0.9, 2.85, 5.5, 3.05)
txt(s, 1.2, 3.1, 5.0, 0.6, "① 손상을 읽는 눈", size=23, color=ACC, bold=True)
txt(s, 1.2, 3.8, 5.0, 1.9, "이 모발이 어디까지 버티고\n컬이 나올지 아는 것.\n전 과정을 이론으로 쥐고 있어야\n실수한 지점을 찾아냅니다.\n— 바늘구멍에 넣듯 나를 피드백.", size=15, color=SUB, spacing=1.2)
card(s, 6.9, 2.85, 5.5, 3.05)
txt(s, 7.2, 3.1, 5.0, 0.6, "② 무드를 보는 눈", size=23, color=ACC, bold=True)
txt(s, 7.2, 3.8, 5.0, 1.9, "컬이 생기면 어떤 무드가 되는가.\n매직이면, 윤기 나면,\n부스스하면 어떤 무드가 되는가.\n기술이 아니라 사람을 봅니다.", size=15, color=SUB, spacing=1.2)
footer(s, 9)

# ══ 10. 부스스함은 부스스함일 뿐 (사진 자리) ══
s = slide("부스스한 게 나쁜가? 아니다. 부스스함은 부스스함일 뿐. 어울리는 사람(여원)이 있고 직선이 어울리는 사람(윤하)이 있다.")
kicker(s, "② 회귀 — 무드")
title(s, "부스스함은 부스스함일 뿐입니다")
for x, lab in [(0.9, "여원 사진\n부스스함이 무드가 되는 사람"), (6.9, "윤하 사진\n직선이 어울리는 사람")]:
    sh = card(s, x, 2.7, 5.5, 3.0, fill=PAPER, line=SUB, line_w=1.4)
    _dash(sh)
    txt(s, x, 3.9, 5.5, 0.9, f"◻︎  {lab}", size=16, color=SUB, align=PP_ALIGN.CENTER, spacing=1.2)
txt(s, 0.9, 5.95, 11.5, 0.7, "나쁜 건 부스스함이 아니라, 안 맞는 것입니다.", size=22, color=INK)
footer(s, 10)

# ══ 11. 매직과 펌 사이의 점들 ══
s = slide("상담 스토리. '깔끔한 인상인데 매직 왜 싫으세요?' '볼륨이 죽어서요.' '30도만 펴 드릴게요.' 매직↔펌 사이 무수한 점을 보는 디자이너가 펌을 파는 디자이너. 이목구비·옷·모질·눈매 보고 제안.")
kicker(s, "② 회귀 — 제안")
title(s, "매직과 펌은 끝과 끝이 아닙니다", size=38)
ly = 3.5
line(s, 1.7, ly, 11.6, ly, color=LINE, w=2.5)
txt(s, 0.75, ly - 0.25, 1.0, 0.5, "매직", size=20, color=INK, bold=True)
txt(s, 11.75, ly - 0.25, 1.2, 0.5, "펌", size=20, color=INK, bold=True)
for i in range(9):
    x = 2.0 + i * 1.16
    circle(s, x, ly, 0.06, fill=SUB, line_c=None)
circle(s, 5.48, ly, 0.15, fill=ACC, line_c=None)
txt(s, 4.5, ly + 0.35, 2.0, 0.5, "“30도만 펴 드릴게요”", size=16, color=ACC, bold=True, align=PP_ALIGN.CENTER)
txt(s, 0.9, 4.85, 11.6, 1.6, "그 사이의 무수한 점을 보는 사람이 펌을 파는 디자이너입니다.\n이목구비 · 옷 · 모질 · 눈매까지 보고, 왜 이 점인지까지 제안합니다.", size=21, color=INK, spacing=1.25)
footer(s, 11)

# ══ 12. Ch3 커트가 펌을 돕는다 ══
s = slide("같은 C컬. 접힐 자리를 커트로 얇게 걷어내면 열 100이 아니라 50으로 같은 컬. 손상 절반, 약도 순하게. 커트는 펌의 보조가 아니라 절반.")
kicker(s, "③ 커트")
title(s, "커트가 펌을 돕습니다")
card(s, 0.9, 2.75, 5.5, 2.7)
txt(s, 0.9, 3.0, 5.5, 0.5, "커트 없이", size=19, color=SUB, bold=True, align=PP_ALIGN.CENTER)
txt(s, 0.9, 3.55, 5.5, 1.0, "열 100의 힘", size=40, color=INK, bold=True, align=PP_ALIGN.CENTER)
txt(s, 0.9, 4.7, 5.5, 0.5, "같은 C컬 · 손상 100", size=15, color=SUB, align=PP_ALIGN.CENTER)
card(s, 6.9, 2.75, 5.5, 2.7)
txt(s, 6.9, 3.0, 5.5, 0.5, "접힐 자리를 걷어내면", size=19, color=ACC, bold=True, align=PP_ALIGN.CENTER)
txt(s, 6.9, 3.55, 5.5, 1.0, "열 50의 힘", size=40, color=ACC, bold=True, align=PP_ALIGN.CENTER)
txt(s, 6.9, 4.7, 5.5, 0.5, "같은 C컬 · 손상 절반 · 약도 순하게", size=15, color=SUB, align=PP_ALIGN.CENTER)
txt(s, 0.9, 5.85, 11.5, 0.6, "커트는 펌의 보조가 아니라 절반입니다.", size=23, color=INK)
footer(s, 12)

# ══ 13. 작용과 반작용 ══
s = slide("걷어내면 잘 접힌다(작용). 너무 걷어내면 부스스해진다(반작용). 매 커트마다 무엇을 취하고 무엇을 버릴지.")
kicker(s, "③ 커트")
title(s, "모든 가위질엔 작용과 반작용이 있습니다", size=36)
card(s, 0.9, 2.7, 5.5, 2.3)
txt(s, 0.9, 2.95, 5.5, 0.6, "작용", size=23, color=ACC2, bold=True, align=PP_ALIGN.CENTER)
txt(s, 1.2, 3.65, 5.0, 1.0, "걷어내면\n컬이 잘 접힙니다", size=19, color=SUB, align=PP_ALIGN.CENTER, spacing=1.15)
card(s, 6.9, 2.7, 5.5, 2.3)
txt(s, 6.9, 2.95, 5.5, 0.6, "반작용", size=23, color=ACC, bold=True, align=PP_ALIGN.CENTER)
txt(s, 7.2, 3.65, 5.0, 1.0, "너무 걷어내면\n부스스해집니다", size=19, color=SUB, align=PP_ALIGN.CENTER, spacing=1.15)
txt(s, 0.9, 5.4, 11.6, 1.2, "매 커트마다 묻습니다. 무엇을 얻고, 무엇을 버릴 것인가.", size=23, color=INK)
footer(s, 13)

# ══ 14. 이제야 보이는 것 ══
s = slide("'펌이 살아났어요'가 아니라 '이제야 보여요'. 검은 바탕 위 검은 줄은 안 보인다. 바탕이 밝아질수록 보인다. 공간이 생겨야 컬이 보인다. 강하게 말았는데 금방 풀려 보이면 공간이 없는 것 — 디자이너 몫.")
kicker(s, "③ 커트 — 공간")
title(s, "살아난 게 아니라, 이제야 보이는 겁니다", size=36)
c1 = card(s, 1.2, 2.75, 4.6, 2.6, fill=RGBColor(0x20,0x1C,0x17), line=None)
for i in range(3):
    a = s.shapes.add_shape(MSO_SHAPE.BLOCK_ARC, I(1.75 + i*1.35), I(3.5), I(1.0), I(1.2))
    a.fill.solid(); a.fill.fore_color.rgb = RGBColor(0x2A,0x26,0x20); a.line.fill.background(); a.shadow.inherit = False
txt(s, 1.2, 5.45, 4.6, 0.5, "공간이 없으면 — 컬이 안 보입니다", size=14, color=SUB, align=PP_ALIGN.CENTER)
c2 = card(s, 7.5, 2.75, 4.6, 2.6, fill=CARD, line=LINE)
for i in range(3):
    a = s.shapes.add_shape(MSO_SHAPE.BLOCK_ARC, I(8.05 + i*1.35), I(3.5), I(1.0), I(1.2))
    a.fill.solid(); a.fill.fore_color.rgb = INK; a.line.fill.background(); a.shadow.inherit = False
txt(s, 7.5, 5.45, 4.6, 0.5, "공간이 생기면 — 같은 컬이 보입니다", size=14, color=INK, align=PP_ALIGN.CENTER)
txt(s, 0.9, 6.15, 11.6, 0.8, "펌이 금방 풀린 게 아니라 공간이 없었던 겁니다. 그건 디자이너의 몫입니다.", size=20, color=INK)
footer(s, 14)

# ══ 15. 마무리 ══
s = slide("클로징. 워드월로 돌아가 '지금 다시 쓰면 열펌이란?' 한 번 더. Q&A, 모다발 테스트. 숙제: 배운 점 + 모다발 비교 사진 PDF(조건 하나만 바꿔).")
txt(s, 0.9, 0.9, 6, 0.4, "닫으며", size=15, color=ACC, bold=True)
line(s, 0.92, 1.35, 1.7, 1.35, color=ACC, w=2.2)
txt(s, 0.9, 2.0, 11.6, 2.2, "열펌은 분해할수록 쉬워지고,\n사람을 읽을수록 완성됩니다.", size=42, color=INK, bold=True, spacing=1.25)
# 홀로 선 아이 (표지 회수)
stickman(s, 11.3, 1.9, scale=1.1, pose="stand")
line(s, 0.9, 4.7, 12.4, 4.7, color=LINE, w=1.0)
txt(s, 0.9, 4.95, 11.5, 0.5, "다음 순서", size=15, color=SUB, bold=True)
txt(s, 0.9, 5.45, 11.6, 1.3, "Q&A  →  모다발 테스트 (이번 과정의 확인)\n숙제 : 배운 점 정리 · 모다발 비교 사진 PDF (조건은 하나만 바꿔서)", size=21, color=INK, spacing=1.3)

out = "content/교육/2026-07-16_열펌특강/열펌의모든것_v2.pptx"
prs.save(out)
print(f"저장: {out} · {len(prs.slides._sldIdLst)}장")
