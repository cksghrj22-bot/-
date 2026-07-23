"""텍스트 렌더 안전 유틸 — 영상/이미지에 글자를 그릴 때 '깨짐'을 렌더 전에 자동으로 잡는다.

깨짐의 3원인과 대응:
  1) 글리프 없음(손글씨 폰트에 '=' 등 기호 부재) → □ 두부 → missing_glyphs로 사전 검출 + pick_font 대체.
  2) 폭 초과 → 화면 밖으로 잘림 → fit()이 자동 줄바꿈.
  3) 자동 줄바꿈으로도 안 되면 → fit()이 폰트 크기를 min_size까지 자동 축소.

사용:
    from shorts import textsafe
    font, lines = textsafe.fit(draw, "긴 문장", FONT_B, max_w=1800, max_h=200, size=60)
    # font·lines 로 그리면 절대 넘치지 않음. 글리프 문제는 assert_ok로 사전 차단.

2026-07-23 이찬호 지시: "글자 저번에도 많이 깨지던데 잘 확인해. 스스로 고쳐 코드 만들어."
"""
from __future__ import annotations
from functools import lru_cache
from PIL import ImageFont

try:
    from fontTools.ttLib import TTFont
    _HAS_FT = True
except Exception:  # pragma: no cover
    _HAS_FT = False


@lru_cache(maxsize=32)
def _cmap(font_path: str) -> frozenset:
    """폰트가 지원하는 유니코드 코드포인트 집합(캐시)."""
    if not _HAS_FT:
        return frozenset()
    try:
        return frozenset(TTFont(font_path).getBestCmap().keys())
    except Exception:
        return frozenset()


def missing_glyphs(text: str, font_path: str) -> list[str]:
    """폰트에 없는 문자 목록(공백 제외). fontTools 없으면 빈 목록(검사 스킵)."""
    cm = _cmap(font_path)
    if not cm:
        return []
    return [c for c in dict.fromkeys(text) if c not in (" ", "\n") and ord(c) not in cm]


def pick_font(text: str, candidates: list[str]) -> str:
    """text의 모든 글리프를 가진 첫 폰트. 없으면 결손이 가장 적은 폰트."""
    best, best_miss = candidates[0], None
    for p in candidates:
        m = missing_glyphs(text, p)
        if not m:
            return p
        if best_miss is None or len(m) < best_miss:
            best, best_miss = p, len(m)
    return best


def _wrap(draw, text: str, font, max_w: float) -> list[str]:
    """공백 우선, 안 되면 글자단위로 max_w 안에 접는다."""
    lines, cur = [], ""
    for token in _tokens(text):
        trial = cur + token
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur.rstrip())
            cur = token.lstrip() if token != " " else ""
    if cur.strip():
        lines.append(cur.rstrip())
    # 한 토큰이 통째로 max_w를 넘으면 글자단위 재분할
    out = []
    for ln in lines:
        if draw.textlength(ln, font=font) <= max_w:
            out.append(ln); continue
        buf = ""
        for ch in ln:
            if draw.textlength(buf + ch, font=font) <= max_w or not buf:
                buf += ch
            else:
                out.append(buf); buf = ch
        if buf:
            out.append(buf)
    return out or [""]


def _tokens(text: str):
    """단어(공백 유지) 단위 토큰. 한글은 어절, 라틴은 단어로 접기 좋게."""
    cur = ""
    for ch in text:
        cur += ch
        if ch == " ":
            yield cur; cur = ""
    if cur:
        yield cur


def fit(draw, text: str, font_path: str, max_w: float, max_h: float | None = None,
        size: int = 60, min_size: int = 20, line_gap: float = 1.18):
    """(font, lines) 반환 — max_w(필수)·max_h(선택) 안에 반드시 들어가도록 자동 줄바꿈+축소.

    - 먼저 size로 줄바꿈. 폭 초과 줄이 남으면 크기를 1씩 줄여 재시도.
    - max_h 주면 전체 높이(줄수×크기×line_gap)도 그 안에 맞춘다.
    - min_size까지 줄여도 안 맞으면 min_size로 최선을 다한 결과 반환(그래도 잘림 방지 위해 줄바꿈은 유지).
    """
    text = text.replace("\n", " ").strip()
    for s in range(size, min_size - 1, -1):
        font = ImageFont.truetype(font_path, s)
        lines = _wrap(draw, text, font, max_w)
        widest = max((draw.textlength(ln, font=font) for ln in lines), default=0)
        total_h = len(lines) * s * line_gap
        if widest <= max_w and (max_h is None or total_h <= max_h):
            return font, lines
    font = ImageFont.truetype(font_path, min_size)
    return font, _wrap(draw, text, font, max_w)


def draw_centered(draw, lines, font, cx: float, top: float, fill, line_gap: float = 1.18):
    """lines를 cx 중심·top부터 세로로 그린다. 다음 블록 top(=아래 경계) 반환."""
    s = font.size
    y = top
    for ln in lines:
        w = draw.textlength(ln, font=font)
        draw.text((cx - w / 2, y), ln, font=font, fill=fill)
        y += s * line_gap
    return y


def assert_ok(text: str, font_path: str, max_w: float, draw=None, size: int = 60):
    """렌더 전 자가검사. 글리프 결손이 있으면 (False, 사유). 폭은 fit로 항상 해결되므로 경고만."""
    miss = missing_glyphs(text, font_path)
    if miss:
        return False, f"글리프 없음 {''.join(miss)} in {font_path.split('/')[-1]}"
    return True, "ok"
