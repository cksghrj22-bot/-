"""카드뉴스 생성기 — 쇼츠 대본을 5장짜리 인스타 카드뉴스로 '바로바로' 뽑는다.

이찬호 지시(2026-07-20): "카드뉴스 양식 하나 통일해서 쇼츠에 올린 것들을 바로바로
카드뉴스로 만들어서 다섯 장 정도로 배포." 통일 양식 = 이 모듈의 template 하나로 고정.

규격: 인스타 캐러셀 1080×1350(4:5) · 5장(커버/본문3/마무리) · 흑백 브랜드톤.
템플릿 3종(브랜드/에디토리얼/다크)을 만들어 형님이 하나 고르면 그걸 정본으로 박제한다.

사용:
    python3 -m shorts.cardnews            # 데모(13 디자이너) 3종 프리뷰 생성
    from shorts.cardnews import render_deck, CardSpec
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1350  # 인스타 캐러셀 4:5

FONT_HAND = "/root/.fonts/KyoboHandwriting2019.ttf"      # 손글씨 제목(브랜드)
FONT_POOR = "/usr/share/fonts/truetype/google/PoorStory-Regular.ttf"
FONT_SQB = "/usr/share/fonts/truetype/nanum/NanumSquareB.ttf"   # 본문 볼드
FONT_SQR = "/usr/share/fonts/truetype/nanum/NanumSquareR.ttf"
FONT_BARUN_B = "/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf"
FONT_MYEONGJO_B = "/usr/share/fonts/truetype/nanum/NanumMyeongjoBold.ttf"

YELLOW = (245, 215, 66)   # 브랜드 노랑(제목)
INK = (20, 20, 22)
PAPER = (238, 233, 224)   # 크림 종이
NEAR_BLACK = (16, 16, 18)


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def _hand_len(d, text, font, space_ratio=0.32):
    """손글씨 폰트는 U+0020 글리프가 없어 □로 뜬다 → 공백을 수동 폭으로 계산."""
    sp = font.size * space_ratio
    return sum(d.textlength(w, font=font) for w in text.split(" ")) + sp * (text.count(" "))


def _draw_hand(d, text, font, x, y, fill, space_ratio=0.32):
    """공백을 글리프로 그리지 않고 수동 전진 — 손글씨 폰트 □ 방지."""
    sp = font.size * space_ratio
    for i, word in enumerate(text.split(" ")):
        if i:
            x += sp
        d.text((x, y), word, font=font, fill=fill)
        x += d.textlength(word, font=font)


def _grad_bg(top=(52, 52, 56), bottom=(14, 14, 16)):
    """세로 그라데이션(1픽셀 컬럼→리사이즈) — 브랜드 흑백 프리미엄 배경(자막 잔상 없음)."""
    col = Image.new("RGB", (1, H))
    px = col.load()
    for yy in range(H):
        t = yy / H
        px[0, yy] = (int(top[0] * (1 - t) + bottom[0] * t),
                     int(top[1] * (1 - t) + bottom[1] * t),
                     int(top[2] * (1 - t) + bottom[2] * t))
    return col.resize((W, H))


def _wrap(draw, text, font, max_w):
    """공백 우선, 없으면 글자 단위로 max_w에 맞춰 줄바꿈."""
    if not text:
        return []
    lines, cur = [], ""
    tokens = text.split(" ")
    for i, tok in enumerate(tokens):
        trial = tok if not cur else cur + " " + tok
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
            continue
        # 토큰 하나가 너무 길면 글자로 쪼갬
        if draw.textlength(tok, font=font) > max_w:
            if cur:
                lines.append(cur); cur = ""
            piece = ""
            for ch in tok:
                if draw.textlength(piece + ch, font=font) <= max_w:
                    piece += ch
                else:
                    lines.append(piece); piece = ch
            cur = piece
        else:
            if cur:
                lines.append(cur)
            cur = tok
    if cur:
        lines.append(cur)
    return lines


def _draw_block(draw, lines, font, x, y, fill, line_gap, align="left", center_x=None):
    for ln in lines:
        w = draw.textlength(ln, font=font)
        lx = x
        if align == "center":
            lx = (center_x or W // 2) - w / 2
        draw.text((lx, y), ln, font=font, fill=fill)
        asc, desc = font.getmetrics()
        y += asc + desc + line_gap
    return y


@dataclass
class CardSpec:
    kind: str            # cover / body / outro
    kicker: str = ""     # 상단 작은 라벨
    title: str = ""      # 큰 제목/문장
    body: str = ""       # 보조 문장
    highlight: str = ""  # 다크 템플릿에서 노랑 강조할 키워드
    page: str = ""       # 우하단 페이지 표시


@dataclass
class Deck:
    brand: str
    handle: str
    cards: list = field(default_factory=list)


# ── 템플릿 A: 브랜드(사진 흑백 배경 + 노랑 손글씨 + 검은 박스 자막) ──
def _bg_photo(frame_path):
    if not frame_path:
        return _grad_bg()
    if frame_path and os.path.exists(frame_path):
        img = Image.open(frame_path).convert("L").convert("RGB")
        # 4:5로 크롭
        iw, ih = img.size
        target = W / H
        if iw / ih > target:
            nw = int(ih * target); img = img.crop(((iw - nw) // 2, 0, (iw - nw) // 2 + nw, ih))
        else:
            nh = int(iw / target); img = img.crop((0, (ih - nh) // 2, iw, (ih - nh) // 2 + nh))
        img = img.resize((W, H))
    else:
        img = Image.new("RGB", (W, H), (40, 40, 42))
    # 어둡게(자막 가독성)
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    img = Image.blend(img, dark, 0.5)
    return img


def render_brand(card: CardSpec, deck: Deck, frame_path=None) -> Image.Image:
    img = _bg_photo(frame_path)
    d = ImageDraw.Draw(img)
    m = 96
    if card.kind == "cover":
        # 상단 노랑 손글씨 제목(공백 수동 처리)
        f_title = _font(FONT_HAND, 108)
        lines = _wrap(d, card.title, f_title, W - m * 2)
        y = 150
        for ln in lines:
            w = _hand_len(d, ln, f_title)
            _draw_hand(d, ln, f_title, (W - w) / 2, y, YELLOW)
            y += 122
        # 하단 검은 박스 훅
        if card.body:
            f_h = _font(FONT_SQB, 52)
            hl = _wrap(d, card.body, f_h, W - m * 2 - 60)
            box_h = len(hl) * 74 + 56
            d.rectangle([m - 30, H - 300 - box_h, W - m + 30, H - 300], fill=(0, 0, 0))
            yy = H - 300 - box_h + 28
            for ln in hl:
                w = d.textlength(ln, font=f_h)
                d.text(((W - w) / 2, yy), ln, font=f_h, fill=(255, 255, 255)); yy += 74
    elif card.kind == "outro":
        f_t = _font(FONT_SQB, 58)
        lines = _wrap(d, card.title, f_t, W - m * 2)
        y = 330
        for ln in lines:
            w = d.textlength(ln, font=f_t)
            d.text(((W - w) / 2, y), ln, font=f_t, fill=(255, 255, 255)); y += 84
        # 노랑 판정형 질문(손글씨·공백 수동)
        f_q = _font(FONT_HAND, 82)
        ql = _wrap(d, card.body, f_q, W - m * 2)
        y += 60
        for ln in ql:
            w = _hand_len(d, ln, f_q)
            _draw_hand(d, ln, f_q, (W - w) / 2, y, YELLOW); y += 96
    else:  # body
        f_t = _font(FONT_SQB, 66)
        lines = _wrap(d, card.title, f_t, W - m * 2)
        total = len(lines) * 92
        y = (H - total) / 2 - 40
        for ln in lines:
            w = d.textlength(ln, font=f_t)
            # 검은 박스 라인
            d.rectangle([(W - w) / 2 - 24, y - 6, (W + w) / 2 + 24, y + 78], fill=(0, 0, 0))
            d.text(((W - w) / 2, y), ln, font=f_t, fill=(255, 255, 255)); y += 92
        if card.body:
            f_b = _font(FONT_SQR, 44)
            bl = _wrap(d, card.body, f_b, W - m * 2)
            y += 30
            for ln in bl:
                w = d.textlength(ln, font=f_b)
                d.text(((W - w) / 2, y), ln, font=f_b, fill=(220, 220, 220)); y += 60
    _footer(d, deck, card, light=True)
    return img


# ── 템플릿 B: 에디토리얼(크림 종이 + 검은 명조 + 노랑 밑줄) ──
def render_editorial(card: CardSpec, deck: Deck, frame_path=None) -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    m = 110
    # 얇은 테두리
    d.rectangle([40, 40, W - 40, H - 40], outline=(200, 193, 182), width=3)
    if card.kicker:
        f_k = _font(FONT_BARUN_B, 34)
        d.text((m, 130), card.kicker, font=f_k, fill=(150, 120, 40))
        d.line([m, 178, m + 90, 178], fill=YELLOW, width=6)
    if card.kind == "cover":
        f_t = _font(FONT_MYEONGJO_B, 92)
        lines = _wrap(d, card.title, f_t, W - m * 2)
        y = 300
        for ln in lines:
            d.text((m, y), ln, font=f_t, fill=INK); y += 116
        if card.body:
            f_b = _font(FONT_SQR, 46)
            bl = _wrap(d, card.body, f_b, W - m * 2)
            y += 40
            for ln in bl:
                d.text((m, y), ln, font=f_b, fill=(90, 84, 74)); y += 64
    elif card.kind == "outro":
        f_t = _font(FONT_MYEONGJO_B, 64)
        lines = _wrap(d, card.title, f_t, W - m * 2)
        y = 320
        for ln in lines:
            d.text((m, y), ln, font=f_t, fill=INK); y += 88
        f_q = _font(FONT_BARUN_B, 50)
        ql = _wrap(d, card.body, f_q, W - m * 2)
        y += 50
        for ln in ql:
            d.text((m, y), ln, font=f_q, fill=(150, 120, 40)); y += 70
    else:
        f_t = _font(FONT_MYEONGJO_B, 74)
        lines = _wrap(d, card.title, f_t, W - m * 2)
        y = 360
        for ln in lines:
            d.text((m, y), ln, font=f_t, fill=INK); y += 100
        if card.body:
            f_b = _font(FONT_SQR, 44)
            bl = _wrap(d, card.body, f_b, W - m * 2)
            y += 40
            for ln in bl:
                d.text((m, y), ln, font=f_b, fill=(90, 84, 74)); y += 62
    _footer(d, deck, card, light=False)
    return img


# ── 템플릿 C: 다크 볼드(먹색 배경 + 큰 흰 글씨 + 노랑 키워드) ──
def render_dark(card: CardSpec, deck: Deck, frame_path=None) -> Image.Image:
    img = Image.new("RGB", (W, H), NEAR_BLACK)
    d = ImageDraw.Draw(img)
    m = 100
    if card.kicker:
        f_k = _font(FONT_SQB, 32)
        d.text((m, 120), card.kicker, font=f_k, fill=YELLOW)
    size = 96 if card.kind == "cover" else 78
    f_t = _font(FONT_SQB, size)

    def draw_hl_line(ln, y):
        # highlight 단어만 노랑
        x = m
        hl = card.highlight
        if hl and hl in ln:
            pre, post = ln.split(hl, 1)
            for seg, col in ((pre, (245, 245, 245)), (hl, YELLOW), (post, (245, 245, 245))):
                if seg:
                    d.text((x, y), seg, font=f_t, fill=col)
                    x += d.textlength(seg, font=f_t)
        else:
            d.text((x, y), ln, font=f_t, fill=(245, 245, 245))

    lines = _wrap(d, card.title, f_t, W - m * 2)
    lh = size + 22
    total = len(lines) * lh
    y = (H - total) / 2 - (40 if card.kind != "cover" else 0)
    if card.kind == "cover":
        y = 260
    for ln in lines:
        draw_hl_line(ln, y); y += lh
    if card.body and card.kind != "body":
        f_b = _font(FONT_SQR, 44)
        bl = _wrap(d, card.body, f_b, W - m * 2)
        y += 40
        for ln in bl:
            d.text((m, y), ln, font=f_b, fill=(160, 160, 165)); y += 62
    if card.kind == "cover":
        d.line([m, 200, m + 120, 200], fill=YELLOW, width=8)
    _footer(d, deck, card, light=True)
    return img


def _footer(d, deck, card, light):
    col = (235, 235, 235) if light else (120, 112, 100)
    f = _font(FONT_SQB, 34)
    d.text((100, H - 120), deck.handle, font=f, fill=YELLOW if light else (150, 120, 40))
    f2 = _font(FONT_SQR, 30)
    d.text((100, H - 78), deck.brand, font=f2, fill=col)
    if card.page:
        w = d.textlength(card.page, font=f2)
        d.text((W - 100 - w, H - 100), card.page, font=f2, fill=col)


TEMPLATES = {"brand": render_brand, "editorial": render_editorial, "dark": render_dark}


def render_deck(deck: Deck, template: str, out_dir: str, frame_path=None, prefix="card"):
    os.makedirs(out_dir, exist_ok=True)
    fn = TEMPLATES[template]
    paths = []
    for i, card in enumerate(deck.cards, 1):
        card.page = f"{i} / {len(deck.cards)}"
        img = fn(card, deck, frame_path)
        p = os.path.join(out_dir, f"{prefix}_{template}_{i}.png")
        img.save(p)
        paths.append(p)
    return paths


def montage(paths, out_path, cols=5, scale=0.42, pad=24, bg=(30, 30, 32)):
    imgs = [Image.open(p) for p in paths]
    cw, ch = int(W * scale), int(H * scale)
    imgs = [im.resize((cw, ch)) for im in imgs]
    rows = (len(imgs) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * cw + (cols + 1) * pad, rows * ch + (rows + 1) * pad), bg)
    for idx, im in enumerate(imgs):
        r, c = divmod(idx, cols)
        canvas.paste(im, (pad + c * (cw + pad), pad + r * (ch + pad)))
    canvas.save(out_path)
    return out_path


# ── 데모 콘텐츠: 쇼츠 13 「이런 디자이너로 들어가세요」 ──
def demo_deck() -> Deck:
    return Deck(
        brand="AT NOWN · 이찬호",
        handle="@차노쌤",
        cards=[
            CardSpec("cover", kicker="HAIR DESIGNER",
                     title="이런 디자이너로 들어가세요",
                     body="미용실에 사진, 들고 가시죠?", highlight="디자이너"),
            CardSpec("body", kicker="01",
                     title="층 위치, 길이, 가벼움.",
                     body="기능만 맞추는 사람 말고요.", highlight="기능만"),
            CardSpec("body", kicker="02",
                     title="당신이 그 사진을 고른 건 무드·분위기·조도 때문이거든요.",
                     body="", highlight="무드"),
            CardSpec("body", kicker="03",
                     title="층만 똑같이 맞추면 원하던 그림은, 안 나와요.",
                     body="그런 디자이너는 모질도 못 볼 확률이 커요.", highlight="안 나와요"),
            CardSpec("outro", kicker="POINT",
                     title="이 사진의 무드가 뭔지, 뭘 느끼고 골랐는지 확인하고 들어가는 사람.",
                     body="당신의 디자이너는, 무드를 읽나요?", highlight="무드"),
        ],
    )


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/cardnews"
    frame = sys.argv[2] if len(sys.argv) > 2 else None
    deck = demo_deck()
    previews = []
    for t in ("brand", "editorial", "dark"):
        paths = render_deck(deck, t, out, frame_path=frame, prefix="demo")
        mp = os.path.join(out, f"_프리뷰_{t}.png")
        montage(paths, mp)
        previews.append(mp)
        print(f"{t}: {len(paths)}장 → {mp}")
    print("PREVIEWS:", " ".join(previews))
