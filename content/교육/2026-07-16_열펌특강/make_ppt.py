# 열펌의 모든 것 (7/16 특강) PPT 생성기 — 이찬호 구술(2026-07-15) 기반, 15장
# 사용: python3 content/교육/2026-07-16_열펌특강/make_ppt.py
# 룩: 워드월과 동일 (짙은 배경 #101014 + 샴페인 골드 + 고딕 볼드). 사진은 빈 박스로 자리만.
from pptx import Presentation
from pptx.util import Inches as I, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

BG = RGBColor(0x10, 0x10, 0x14)
GOLD = RGBColor(0xDF, 0xC5, 0x7E)
IVORY = RGBColor(0xF0, 0xEB, 0xE0)
GREY = RGBColor(0x8A, 0x8F, 0xA0)
DIM = RGBColor(0x2C, 0x2C, 0x38)
PANEL = RGBColor(0x1A, 0x1A, 0x22)
RED = RGBColor(0xC8, 0x7B, 0x6B)
SAGE = RGBColor(0xA9, 0xBC, 0xA4)
FONT = "Apple SD Gothic Neo"

prs = Presentation()
prs.slide_width, prs.slide_height = I(13.333), I(7.5)
BLANK = prs.slide_layouts[6]
W, H = 13.333, 7.5


def slide(notes=""):
    s = prs.slides.add_slide(BLANK)
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    r.fill.solid(); r.fill.fore_color.rgb = BG; r.line.fill.background()
    r.shadow.inherit = False
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def txt(s, x, y, w, h, text, size=24, color=IVORY, bold=False, align=PP_ALIGN.LEFT,
        anchor=MSO_ANCHOR.TOP, spacing=1.0):
    b = s.shapes.add_textbox(I(x), I(y), I(w), I(h))
    tf = b.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.line_spacing = spacing
        r = p.add_run(); r.text = line
        f = r.font; f.name = FONT; f.size = Pt(size); f.color.rgb = color; f.bold = bold
        rPr = r._r.get_or_add_rPr()  # 한글(동아시아) 폰트 강제
        ea = rPr.find(qn('a:ea'))
        if ea is None:
            ea = rPr.makeelement(qn('a:ea'), {}); rPr.append(ea)
        ea.set('typeface', FONT)
    return b


def box(s, x, y, w, h, fill=PANEL, line=DIM, line_w=1.0, round_=True):
    shp = s.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if round_ else MSO_SHAPE.RECTANGLE, I(x), I(y), I(w), I(h))
    if round_:
        try: shp.adjustments[0] = 0.08
        except Exception: pass
    shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line is None: shp.line.fill.background()
    else: shp.line.color.rgb = line; shp.line.width = Pt(line_w)
    shp.shadow.inherit = False
    return shp


def photo_box(s, x, y, w, h, label):
    box(s, x, y, w, h, fill=PANEL, line=GREY, line_w=1.2)
    txt(s, x, y + h/2 - 0.45, w, 0.9, f"📷\n{label}", size=15, color=GREY, align=PP_ALIGN.CENTER)


def chapter_tag(s, text):
    txt(s, 0.6, 0.45, 6, 0.4, text, size=14, color=GOLD, bold=True)


def footer(s, n):
    txt(s, W - 1.2, H - 0.5, 0.8, 0.35, str(n), size=11, color=GREY, align=PP_ALIGN.RIGHT)
    txt(s, 0.6, H - 0.5, 3, 0.35, "AT NOWN 교육 · 열펌의 모든 것", size=11, color=GREY)


# ── 1. 표지: 분해하다 (쪼개지는 첫 장면 — 물음표) ─────────────────────
s = slide("오프닝. 화면엔 '열펌'이 쪼개진 그림뿐. '오늘 우리는 이걸 쪼갤 겁니다'로 시작. 워드월 QR은 이 직전에 진행.")
t1 = txt(s, 2.2, 2.0, 3.6, 2.0, "열", size=170, color=IVORY, bold=True, align=PP_ALIGN.CENTER)
t1.rotation = -8
t2 = txt(s, 7.4, 2.2, 3.6, 2.0, "펌", size=170, color=IVORY, bold=True, align=PP_ALIGN.CENTER)
t2.rotation = 7
# 가운데 갈라지는 금 (지그재그)
from pptx.shapes.freeform import FreeformBuilder
fb = s.shapes.build_freeform(Emu(int(I(6.55))), Emu(int(I(1.4))), scale=1)
fb.add_line_segments([(Emu(int(I(x))), Emu(int(I(y)))) for x, y in
                      [(6.85, 2.5), (6.5, 3.3), (6.95, 4.1), (6.6, 5.0), (6.95, 5.9)]], close=False)
crack = fb.convert_to_shape()
crack.line.color.rgb = GOLD; crack.line.width = Pt(4); crack.fill.background(); crack.shadow.inherit = False
txt(s, 6.3, 0.65, 1.2, 1.0, "?", size=64, color=GOLD, bold=True, align=PP_ALIGN.CENTER)
txt(s, 0, 5.6, W, 0.8, "열펌의 모든 것 — 분해하다", size=34, color=GOLD, bold=True, align=PP_ALIGN.CENTER)
txt(s, 0, 6.4, W, 0.5, "AT NOWN 교육 · 차노 · 2026. 7. 16", size=16, color=GREY, align=PP_ALIGN.CENTER)

# ── 2. 오늘의 지도 ─────────────────────────────────────────────
s = slide("공부는 분해에서 시작한다. 오늘은 하나를 깊게 파는 날이 아니라, 브레인스토밍처럼 넓게 몇 가지를 집어보는 날.")
txt(s, 0.6, 0.9, 12, 1.0, "공부한다 = 분해한다", size=44, color=GOLD, bold=True)
items = [("①", "분해", "열과 약을 쪼개본다"),
         ("②", "회귀", "그래서, 펌은 왜 하는가"),
         ("③", "커트", "펌을 돕는 절반"),
         ("④", "확인", "Q&A · 모다발 테스트")]
for i, (n, t, d) in enumerate(items):
    x = 0.7 + i * 3.1
    box(s, x, 2.4, 2.8, 2.6)
    txt(s, x, 2.7, 2.8, 0.6, n, size=26, color=GOLD, bold=True, align=PP_ALIGN.CENTER)
    txt(s, x, 3.3, 2.8, 0.7, t, size=30, color=IVORY, bold=True, align=PP_ALIGN.CENTER)
    txt(s, x + 0.2, 4.1, 2.4, 0.8, d, size=15, color=GREY, align=PP_ALIGN.CENTER)
txt(s, 0.6, 5.7, 12, 0.7, "쪼개봐야 내 것이 됩니다.", size=24, color=IVORY, align=PP_ALIGN.LEFT)
footer(s, 2)

# ── 3. Ch1 질문 두 개 ──────────────────────────────────────────
s = slide("펌이란 무엇인가, 열은 왜 필요한가부터 묻는다. 롤러볼의 간접열과 판이 직접 닿는 디지털·세팅의 열은 같은 열인가? 쪼개보기 전엔 답할 수 없다.")
chapter_tag(s, "① 분해 — 열")
txt(s, 0.6, 1.6, 12, 1.2, "펌이란 무엇인가?", size=54, color=IVORY, bold=True)
txt(s, 0.6, 3.0, 12, 1.2, "열은 왜 필요한가?", size=54, color=IVORY, bold=True)
txt(s, 0.6, 4.9, 12, 1.2, "롤러볼의 열과, 판이 직접 닿는 열은\n같은 열인가?", size=26, color=GOLD)
footer(s, 3)

# ── 4. 열의 특성 게이지 ─────────────────────────────────────────
s = slide("40~55도 저온 구간은 수분과 시간이 일하는 구간. 100도를 넘으면 수분을 날리며 형태를 굳힌다. 140도부터는 단백질 변형이 시작된다. 열펌은 열로 사람을 편하게 만드는 시술 — 열은 적이 아니라 도구다.")
chapter_tag(s, "① 분해 — 열")
txt(s, 0.6, 0.9, 12, 0.9, "열마다 하는 일이 다릅니다", size=40, color=GOLD, bold=True)
bar_y, bar_x, bar_w = 3.1, 1.0, 11.3
box(s, bar_x, bar_y, bar_w, 0.22, fill=DIM, line=None, round_=False)
seg = [(0.0, 0.34, SAGE, "40~55°C", "수분과 시간이 일하는 구간\n(저온 세팅·건강한 물결)"),
       (0.38, 0.30, GOLD, "100°C+", "수분을 날리며\n형태를 굳히는 구간"),
       (0.72, 0.28, RED, "140°C~", "단백질 변형이\n시작되는 선")]
for off, wf, c, temp, desc in seg:
    x = bar_x + off * bar_w; w = wf * bar_w
    box(s, x, bar_y - 0.06, w, 0.34, fill=c, line=None, round_=False)
    txt(s, x, bar_y - 1.0, w, 0.8, temp, size=26, color=c, bold=True, align=PP_ALIGN.CENTER)
    txt(s, x, bar_y + 0.55, w, 1.2, desc, size=15, color=GREY, align=PP_ALIGN.CENTER)
txt(s, 0.6, 5.5, 12, 1.2, "열펌 = 열로 사람을 편하게 만드는 시술.\n열은 적이 아니라 도구입니다.", size=24, color=IVORY)
footer(s, 4)

# ── 5. 약을 쪼개면 ─────────────────────────────────────────────
s = slide("성희 부원장의 해석 사례. 열펌제 = 연화제+환원제. 팩(점증 성분)이 과연화를 막는 브레이크라 꾸덕한 것. 환원제가 결합을 풀어 부드럽게, 그러나 과하지 않게 컬을 만든다. 남의 약도 이렇게 분해하면 내 것이 된다.")
chapter_tag(s, "① 분해 — 약")
txt(s, 0.6, 0.9, 12, 0.9, "약도 쪼개집니다", size=40, color=GOLD, bold=True)
comp = [("연화제", "머리를 부드럽게 여는 힘", GOLD),
        ("팩 · 점증 성분", "과연화를 막는 브레이크\n(약이 꾸덕한 진짜 이유)", SAGE),
        ("환원제", "결합을 풀어\n컬을 만드는 힘", RED)]
for i, (t, d, c) in enumerate(comp):
    x = 0.9 + i * 4.1
    box(s, x, 2.3, 3.6, 2.3)
    txt(s, x, 2.6, 3.6, 0.7, t, size=27, color=c, bold=True, align=PP_ALIGN.CENTER)
    txt(s, x + 0.25, 3.4, 3.1, 1.1, d, size=16, color=IVORY, align=PP_ALIGN.CENTER)
    if i < 2:
        txt(s, x + 3.6, 3.1, 0.5, 0.7, "+", size=34, color=GREY, bold=True, align=PP_ALIGN.CENTER)
txt(s, 0.6, 5.3, 12, 1.3, "남의 해석도 분해해 보면 내 것이 됩니다.\n외우는 약은 남의 약, 쪼개본 약이 내 약입니다.", size=24, color=IVORY)
footer(s, 5)

# ── 6. 타입별 장점 ─────────────────────────────────────────────
s = slide("크림 타입은 침투제가 많고 머리를 녹이는(연화) 약 — 강한 곱슬·건강모에 유리. 겔·액체 타입은 녹이지 못하는 대신 섬세한 컨트롤 — 손상모에 유리. 좋은 약은 없다, 맞는 약이 있을 뿐.")
chapter_tag(s, "① 분해 — 약")
txt(s, 0.6, 0.9, 12, 0.9, "크림이냐, 겔이냐가 아니라", size=40, color=GOLD, bold=True)
box(s, 0.9, 2.2, 5.6, 3.2)
txt(s, 0.9, 2.5, 5.6, 0.7, "크림 타입", size=28, color=IVORY, bold=True, align=PP_ALIGN.CENTER)
txt(s, 1.3, 3.3, 4.8, 1.8, "침투제가 풍부\n녹이는 힘(연화력)이 강함\n→ 강한 곱슬 · 건강모", size=18, color=GREY, align=PP_ALIGN.CENTER)
box(s, 6.9, 2.2, 5.6, 3.2)
txt(s, 6.9, 2.5, 5.6, 0.7, "겔 · 액체 타입", size=28, color=IVORY, bold=True, align=PP_ALIGN.CENTER)
txt(s, 7.3, 3.3, 4.8, 1.8, "녹이지 못하는 대신\n섬세하게 컨트롤\n→ 손상모 · 미세 조정", size=18, color=GREY, align=PP_ALIGN.CENTER)
txt(s, 0.6, 5.8, 12, 0.8, "좋은 약은 없습니다. 이 모발에 맞는 약이 있을 뿐입니다.", size=24, color=IVORY)
footer(s, 6)

# ── 7. 그림으로 보는 곱슬 (사진 자리) ────────────────────────────
s = slide("이론 텍스트가 아니라 그림으로 보여줄 장. 옛날부터 쓰던 곱슬 모양표 + 연화·볼륨이 줄면서 사람 이미지가 달라지는 표. 핀터레스트 스타일 이미지로 채우기.")
chapter_tag(s, "① 분해 — 곱슬")
txt(s, 0.6, 0.9, 12, 0.9, "말이 아니라, 그림으로 봅니다", size=40, color=GOLD, bold=True)
photo_box(s, 0.9, 2.1, 5.6, 4.0, "곱슬 모양표 넣기\n(기존 곱슬 특성표)")
photo_box(s, 6.9, 2.1, 5.6, 4.0, "연화·볼륨 변화에 따라\n이미지가 달라지는 표 넣기")
footer(s, 7)

# ── 8. Ch2 회귀: 미용은 왜 ───────────────────────────────────────
s = slide("다 분해해 봤으면 다시 돌아온다. 미용은 왜 하는가. 예뻐지려고, 손질이 편해지려고 — 이 두 가지를 절대 잊으면 안 된다. 펌은 이 둘을 벗어난 적이 없다.")
chapter_tag(s, "② 회귀")
txt(s, 0.6, 1.3, 12, 1.0, "그래서, 미용은 왜 할까요?", size=44, color=GOLD, bold=True)
box(s, 0.9, 2.9, 5.6, 1.9)
txt(s, 0.9, 3.35, 5.6, 1.0, "예뻐지려고", size=36, color=IVORY, bold=True, align=PP_ALIGN.CENTER)
box(s, 6.9, 2.9, 5.6, 1.9)
txt(s, 6.9, 3.35, 5.6, 1.0, "손질이 편해지려고", size=36, color=IVORY, bold=True, align=PP_ALIGN.CENTER)
txt(s, 0.6, 5.4, 12, 1.2, "이 두 가지를 절대 잊지 않습니다.\n펌은 이 둘을 벗어난 적이 없습니다.", size=24, color=GREY)
footer(s, 8)

# ── 9. 진짜 실력 두 가지 ─────────────────────────────────────────
s = slide("펌 기술은 6개월이면 는다 — 선생님이 어떻게 말고 약 쓰는지 보면. 진짜 어려운 건 ①이 모발이 어느 손상까지 버티며 컬이 나올지 읽는 눈 — 전 과정을 이론으로 쥐고 있어야 어디서 실수했는지 찾는다. 바늘구멍에 넣듯 나를 피드백하라. ②무드를 보는 눈.")
chapter_tag(s, "② 회귀")
txt(s, 0.6, 0.9, 12.2, 0.9, "펌 기술은 6개월이면 늡니다", size=40, color=GOLD, bold=True)
txt(s, 0.6, 1.85, 12, 0.6, "진짜 실력은 두 가지에서 갈립니다", size=20, color=GREY)
box(s, 0.9, 2.7, 5.6, 3.1)
txt(s, 1.2, 3.0, 5.0, 0.6, "① 손상을 읽는 눈", size=24, color=GOLD, bold=True)
txt(s, 1.2, 3.7, 5.0, 1.9, "이 모발이 어디까지 버티고\n컬이 나올지 아는 것.\n전 과정을 이론으로 쥐고 있어야\n실수한 지점을 찾아냅니다.\n— 바늘구멍에 넣듯 나를 피드백.", size=16, color=IVORY, spacing=1.15)
box(s, 6.9, 2.7, 5.6, 3.1)
txt(s, 7.2, 3.0, 5.0, 0.6, "② 무드를 보는 눈", size=24, color=GOLD, bold=True)
txt(s, 7.2, 3.7, 5.0, 1.9, "컬이 생기면 어떤 무드가 되는가.\n매직이면, 윤기 나면,\n부스스하면 어떤 무드가 되는가.\n기술이 아니라 사람을 봅니다.", size=16, color=IVORY, spacing=1.15)
footer(s, 9)

# ── 10. 부스스함은 부스스함일 뿐 (사진 자리) ─────────────────────────
s = slide("부스스한 게 나쁜 건가? 아니다. 부스스함은 부스스함일 뿐. 그게 어울리는 사람(여원)이 있고, 직선이 어울리는 사람(윤하)이 있다. 나쁜 건 부스스함이 아니라 안 맞는 것.")
chapter_tag(s, "② 회귀 — 무드")
txt(s, 0.6, 0.9, 12, 0.9, "부스스함은 부스스함일 뿐입니다", size=40, color=GOLD, bold=True)
photo_box(s, 0.9, 2.1, 5.6, 3.6, "여원 사진 넣기\n(부스스함이 무드가 되는 사람)")
photo_box(s, 6.9, 2.1, 5.6, 3.6, "윤하 사진 넣기\n(직선이 어울리는 사람)")
txt(s, 0.6, 6.0, 12, 0.7, "나쁜 건 부스스함이 아니라, 안 맞는 것입니다.", size=22, color=IVORY)
footer(s, 10)

# ── 11. 매직과 펌 사이의 점들 ────────────────────────────────────
s = slide("상담 스토리로. '고객님은 이목구비가 깔끔해서 직선이 어울리는데, 매직은 왜 싫으세요?' '볼륨이 죽어서요.' '그럼 30도만 펴 드릴게요 — 깔끔함은 살고 볼륨도 사는 매직이 있습니다.' 매직이면 매직, 펌이면 펌이 아니라 그 사이의 무수한 점을 보는 디자이너가 펌을 파는 디자이너다. 이목구비·옷·모질·눈매까지 보고 제안한다.")
chapter_tag(s, "② 회귀 — 제안")
txt(s, 0.6, 0.9, 12, 0.9, "매직과 펌은 끝과 끝이 아닙니다", size=40, color=GOLD, bold=True)
ly = 3.4
ln = s.shapes.add_connector(1, I(1.6), I(ly), I(11.7), I(ly))
ln.line.color.rgb = DIM; ln.line.width = Pt(3)
txt(s, 0.7, ly - 0.25, 1.2, 0.5, "매직", size=22, color=IVORY, bold=True)
txt(s, 11.85, ly - 0.25, 1.2, 0.5, "펌", size=22, color=IVORY, bold=True)
for i in range(9):
    x = 2.0 + i * 1.15
    d = s.shapes.add_shape(MSO_SHAPE.OVAL, I(x), I(ly - 0.07), I(0.14), I(0.14))
    d.fill.solid(); d.fill.fore_color.rgb = GREY; d.line.fill.background(); d.shadow.inherit = False
big = s.shapes.add_shape(MSO_SHAPE.OVAL, I(5.35), I(ly - 0.19), I(0.38), I(0.38))
big.fill.solid(); big.fill.fore_color.rgb = GOLD; big.line.fill.background(); big.shadow.inherit = False
txt(s, 4.3, ly + 0.45, 2.6, 0.5, "\"30도만 펴 드릴게요\"", size=17, color=GOLD, bold=True, align=PP_ALIGN.CENTER)
txt(s, 0.6, 4.9, 12.2, 1.6, "그 사이의 무수한 점을 보는 사람이 펌을 파는 디자이너입니다.\n이목구비 · 옷 · 모질 · 눈매까지 보고, 왜 이 점인지까지 제안합니다.", size=22, color=IVORY, spacing=1.2)
footer(s, 11)

# ── 12. Ch3 커트가 펌을 돕는다 ───────────────────────────────────
s = slide("같은 C컬을 만들 때, 접힐 자리를 커트로 얇게 걷어내면 열 100의 힘이 아니라 50의 힘으로 같은 컬이 나온다. 손상은 절반, 컬은 그대로. 약도 약하게 쓸 수 있다. 커트는 펌의 보조가 아니라 절반이다.")
chapter_tag(s, "③ 커트")
txt(s, 0.6, 0.9, 12, 0.9, "커트가 펌을 돕습니다", size=40, color=GOLD, bold=True)
box(s, 0.9, 2.3, 5.6, 2.9)
txt(s, 0.9, 2.6, 5.6, 0.6, "커트 없이", size=22, color=GREY, bold=True, align=PP_ALIGN.CENTER)
txt(s, 0.9, 3.3, 5.6, 1.0, "열 100의 힘", size=40, color=RED, bold=True, align=PP_ALIGN.CENTER)
txt(s, 0.9, 4.4, 5.6, 0.5, "같은 C컬 · 손상 100", size=16, color=GREY, align=PP_ALIGN.CENTER)
box(s, 6.9, 2.3, 5.6, 2.9)
txt(s, 6.9, 2.6, 5.6, 0.6, "접힐 자리를 걷어내면", size=22, color=GREY, bold=True, align=PP_ALIGN.CENTER)
txt(s, 6.9, 3.3, 5.6, 1.0, "열 50의 힘", size=40, color=SAGE, bold=True, align=PP_ALIGN.CENTER)
txt(s, 6.9, 4.4, 5.6, 0.5, "같은 C컬 · 손상 절반 · 약도 순하게", size=16, color=GREY, align=PP_ALIGN.CENTER)
txt(s, 0.6, 5.7, 12, 0.8, "커트는 펌의 보조가 아니라 절반입니다.", size=24, color=IVORY)
footer(s, 12)

# ── 13. 작용과 반작용 ────────────────────────────────────────────
s = slide("커트로 걷어내면 컬이 잘 접힌다(작용). 너무 걷어내면 부스스해진다(반작용). 모든 가위질에는 작용과 반작용이 있다 — 매 커트마다 무엇을 취하고 무엇을 버릴지 생각해야 한다.")
chapter_tag(s, "③ 커트")
txt(s, 0.6, 0.9, 12, 0.9, "모든 가위질엔 작용과 반작용이 있습니다", size=38, color=GOLD, bold=True)
box(s, 0.9, 2.4, 5.6, 2.4)
txt(s, 0.9, 2.7, 5.6, 0.6, "작용", size=24, color=SAGE, bold=True, align=PP_ALIGN.CENTER)
txt(s, 1.2, 3.4, 5.0, 1.0, "걷어내면\n컬이 잘 접힙니다", size=20, color=IVORY, align=PP_ALIGN.CENTER)
box(s, 6.9, 2.4, 5.6, 2.4)
txt(s, 6.9, 2.7, 5.6, 0.6, "반작용", size=24, color=RED, bold=True, align=PP_ALIGN.CENTER)
txt(s, 7.2, 3.4, 5.0, 1.0, "너무 걷어내면\n부스스해집니다", size=20, color=IVORY, align=PP_ALIGN.CENTER)
txt(s, 0.6, 5.3, 12.2, 1.3, "매 커트마다 묻습니다.\n무엇을 얻고, 무엇을 버릴 것인가.", size=24, color=IVORY, spacing=1.2)
footer(s, 13)

# ── 14. 살아난 게 아니라 이제야 보이는 것 ─────────────────────────
s = slide("'커트하니 펌이 살아났어요'가 아니다. 펌이 인간인가, 살아나게. 이제야 '보이는' 거다. 검은 바탕 위 검은 줄은 안 보인다. 바탕이 밝아질수록 보인다. 공간이 생겨야 컬이 보인다. 강하게 말았는데 금방 풀려 보이는 머리는 펌이 없는 게 아니라 공간이 없는 것 — 손님 잘못이 아니라 디자이너 잘못이다.")
chapter_tag(s, "③ 커트 — 공간")
txt(s, 0.6, 0.9, 12.2, 0.9, "살아난 게 아니라, 이제야 보이는 겁니다", size=38, color=GOLD, bold=True)
bx1 = box(s, 1.4, 2.4, 4.6, 2.9, fill=RGBColor(0x0A, 0x0A, 0x0C), line=DIM, round_=False)
for i in range(3):
    a = s.shapes.add_shape(MSO_SHAPE.BLOCK_ARC, I(1.9 + i * 1.35), I(3.2), I(1.0), I(1.3))
    a.fill.solid(); a.fill.fore_color.rgb = RGBColor(0x14, 0x14, 0x18); a.line.fill.background(); a.shadow.inherit = False
txt(s, 1.4, 5.4, 4.6, 0.5, "공간이 없으면 — 컬이 안 보입니다", size=15, color=GREY, align=PP_ALIGN.CENTER)
bx2 = box(s, 7.3, 2.4, 4.6, 2.9, fill=RGBColor(0x6B, 0x6B, 0x72), line=None, round_=False)
for i in range(3):
    a = s.shapes.add_shape(MSO_SHAPE.BLOCK_ARC, I(7.8 + i * 1.35), I(3.2), I(1.0), I(1.3))
    a.fill.solid(); a.fill.fore_color.rgb = RGBColor(0x0E, 0x0E, 0x10); a.line.fill.background(); a.shadow.inherit = False
txt(s, 7.3, 5.4, 4.6, 0.5, "공간이 생기면 — 같은 컬이 보입니다", size=15, color=IVORY, align=PP_ALIGN.CENTER)
txt(s, 0.6, 6.15, 12.2, 0.9, "펌이 금방 풀린 게 아니라 공간이 없었던 겁니다. 그건 디자이너의 몫입니다.", size=21, color=IVORY)
footer(s, 14)

# ── 15. 마무리 ──────────────────────────────────────────────────
s = slide("클로징. 워드월로 돌아가 '지금 다시 쓰면 열펌이란 무엇인가' 한 번 더. 이후 Q&A, 그리고 이번 과정의 확인은 모다발 테스트. 숙제: 배운 점 정리 + 모다발 실습 비교 사진 PDF(조건 1개만 바꿔 비교).")
txt(s, 0.6, 1.5, 12.2, 2.4, "열펌은 분해할수록 쉬워지고,\n사람을 볼수록 팔립니다.", size=44, color=GOLD, bold=True, spacing=1.25)
txt(s, 0.6, 4.4, 12, 0.6, "다음 순서", size=16, color=GREY, bold=True)
txt(s, 0.6, 4.9, 12, 1.4, "Q&A  →  모다발 테스트 (이번 과정의 확인)\n숙제: 배운 점 정리 · 모다발 비교 사진 PDF (조건은 하나만 바꿔서)", size=22, color=IVORY, spacing=1.3)
footer(s, 15)

out = "content/교육/2026-07-16_열펌특강/열펌의모든것_v1.pptx"
prs.save(out)
print(f"저장: {out} ({len(prs.slides.slides if hasattr(prs.slides,'slides') else prs.slides._sldIdLst)}장)" if False else f"저장: {out} · {len(prs.slides._sldIdLst)}장")
