"""한 장 손그림 인포그래픽 포스터 생성기 — 스틱피겨 흑백 카드(교보 손글씨).

이찬호 지시(2026-07-22): "지독하게 잘하는 법" 같은 6칸 손그림 인포그래픽 한 장을
'이런 방식으로' 계속 찍어낸다. 1회성 그림이 아니라 배관:
    데이터(제목 + 6칸: 번호/헤딩/본문/그림키) → HTML → PNG.
그림만 바꾸면 되도록 SVG 스틱피겨를 키로 골라 끼운다.

규격: 1080×1350 인스타 4:5 · 흰 종이 · 교보 손글씨(제목/헤딩) + 나눔펜(본문) · 순수 흑백.
왜 HTML+SVG인가: 스틱피겨는 선/원/경로라 SVG가 정확하고, 교보 폰트는 @font-face로 그대로 신는다.

사용:
    python3 -m shorts.cardposter <out.png> [--spec demo]
    from shorts.cardposter import render_poster, PosterSpec, Panel
"""
from __future__ import annotations

import base64
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

W, H = 1080, 1350

FONT_HAND = "/root/.fonts/KyoboHandwriting2019.ttf"   # 제목·헤딩(교보 손글씨)
FONT_PEN = "/root/.fonts/NanumPenScript-Regular.ttf"  # 본문(나눔펜 — 공백 정상)


def _font_face(name: str, path: str) -> str:
    b64 = base64.b64encode(Path(path).read_bytes()).decode()
    return (f"@font-face{{font-family:'{name}';"
            f"src:url(data:font/ttf;base64,{b64}) format('truetype');}}")


# ─────────────────────────── SVG 스틱피겨 라이브러리 ───────────────────────────
# viewBox 300x300, 검은 선(round cap). 그림키로 골라 끼운다.
STK = 'fill="none" stroke="#141416" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"'
STK_T = 'fill="none" stroke="#141416" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"'


def _wall() -> str:
    # 벽에 부딪히는 사람 + 충격 별
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <!-- 벽 -->
  <line x1="238" y1="30" x2="238" y2="270" {STK}/>
  <g {STK_T}>
    <line x1="238" y1="60" x2="272" y2="44"/><line x1="238" y1="110" x2="272" y2="94"/>
    <line x1="238" y1="160" x2="272" y2="144"/><line x1="238" y1="210" x2="272" y2="194"/>
  </g>
  <!-- 충격 별 -->
  <g {STK_T}>
    <path d="M212 118 l14 -10 M212 128 l18 -2 M212 140 l14 10 M206 108 l6 -14 M204 150 l4 16"/>
  </g>
  <!-- 사람(달려와 머리 박음) -->
  <circle cx="150" cy="128" r="26" {STK}/>
  <path d="M150 154 L150 210" {STK}/>
  <path d="M150 168 L120 150 M150 168 L188 176" {STK}/>
  <path d="M150 210 L124 258 M150 210 L182 250" {STK}/>
  <!-- 땅 -->
  <line x1="70" y1="272" x2="210" y2="272" {STK_T}/>
</svg>'''


def _jeer() -> str:
    # 당당한 큰 사람 + 주변 작은 야유 무리(말풍선)
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <!-- 큰 사람(허리에 손, 웃음) -->
  <circle cx="150" cy="120" r="28" {STK}/>
  <path d="M138 116 q4 5 10 0 M162 116 q-4 5 -10 0" {STK_T}/>
  <path d="M132 130 q18 16 36 0" {STK_T}/>
  <path d="M150 148 L150 208" {STK}/>
  <path d="M150 166 L120 178 L128 150 M150 166 L180 178 L172 150" {STK}/>
  <path d="M150 208 L128 254 M150 208 L172 254" {STK}/>
  <!-- 작은 야유꾼 좌 -->
  <g transform="translate(34,150) scale(0.5)">
    <circle cx="40" cy="40" r="20" {STK}/><path d="M40 60 L40 110" {STK}/>
    <path d="M40 74 L70 66 M40 74 L14 88" {STK}/><path d="M40 110 L24 150 M40 110 L58 150" {STK}/>
  </g>
  <!-- 작은 야유꾼 우 -->
  <g transform="translate(228,150) scale(0.5)">
    <circle cx="40" cy="40" r="20" {STK}/><path d="M40 60 L40 110" {STK}/>
    <path d="M40 74 L10 66 M40 74 L66 88" {STK}/><path d="M40 110 L24 150 M40 110 L58 150" {STK}/>
  </g>
  <!-- 말풍선 -->
  <g {STK_T}><ellipse cx="52" cy="66" rx="34" ry="20"/><path d="M60 84 l-8 14 l18 -10"/></g>
  <g {STK_T}><ellipse cx="248" cy="66" rx="34" ry="20"/><path d="M240 84 l8 14 l-18 -10"/></g>
</svg>'''


def _tally() -> str:
    # 정(正)자 세며 버티는 사람 + 100
    marks = ""
    x0, y0 = 190, 70
    for r in range(4):
        for c in range(4):
            gx = x0 + c * 26
            gy = y0 + r * 40
            marks += f'<path d="M{gx} {gy} l0 24 M{gx+6} {gy} l0 24 M{gx+12} {gy} l0 24 M{gx+18} {gy} l0 24 M{gx-2} {gy+12} l24 -8" {STK_T}/>'
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <circle cx="90" cy="120" r="26" {STK}/>
  <path d="M90 146 q-6 40 6 62" {STK}/>
  <path d="M92 168 L150 176 M92 172 L64 150" {STK}/>
  <path d="M96 208 L74 254 M96 208 L120 250" {STK}/>
  <!-- 땀 -->
  <path d="M118 96 q6 8 0 14" {STK_T}/>
  {marks}
  <text x="196" y="256" font-family="KyoboPoster" font-size="42" fill="#141416">100</text>
  <line x1="196" y1="262" x2="252" y2="262" {STK_T}/>
  <line x1="40" y1="272" x2="150" y2="272" {STK_T}/>
</svg>'''


def _shame_run() -> str:
    # 쪽팔려도 앞으로 달리는 사람 + 뒤 웃는 무리
    crowd = ""
    for i, cx in enumerate((214, 244, 262, 232)):
        cy = 150 + (i % 2) * 22
        s = 0.42
        crowd += f'''<g transform="translate({cx},{cy}) scale({s})">
          <circle cx="0" cy="0" r="20" {STK}/><path d="M18 -6 q6 8 0 12" {STK_T}/>
          <path d="M0 20 L0 70" {STK}/><path d="M0 34 L28 26 M0 34 L-26 40" {STK}/>
          <path d="M0 70 L-16 110 M0 70 L18 110" {STK}/></g>'''
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <!-- 주인공(달림, 볼 홍조) -->
  <circle cx="110" cy="118" r="27" {STK}/>
  <path d="M96 126 q3 4 8 0 M116 126 q3 4 8 0" {STK_T}/>
  <circle cx="92" cy="126" r="4" fill="#141416"/><circle cx="132" cy="126" r="4" fill="#141416"/>
  <path d="M100 140 q10 6 20 0" {STK_T}/>
  <path d="M110 145 q-8 34 4 60" {STK}/>
  <path d="M112 166 L150 150 M112 166 L78 178" {STK}/>
  <path d="M114 205 L92 252 M114 205 L142 246" {STK}/>
  {crowd}
  <line x1="60" y1="270" x2="190" y2="270" {STK_T}/>
</svg>'''


def _mix() -> str:
    # A/B/C 기술 → 그릇에 섞기 → 새 사람(나만의 무기)
    def mini(x, y):
        return f'''<g transform="translate({x},{y}) scale(0.34)">
          <circle cx="0" cy="0" r="20" {STK}/><path d="M0 20 L0 66" {STK}/>
          <path d="M0 32 L24 40 M0 32 L-24 40" {STK}/><path d="M0 66 L-16 104 M0 66 L16 104" {STK}/></g>'''
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <!-- A B C 라벨 -->
  <text x="14" y="70" font-family="NanumPenPoster" font-size="30" fill="#141416">A</text>
  <text x="14" y="150" font-family="NanumPenPoster" font-size="30" fill="#141416">B</text>
  <text x="14" y="230" font-family="NanumPenPoster" font-size="30" fill="#141416">C</text>
  {mini(58,54)}{mini(58,134)}{mini(58,214)}
  <path d="M92 60 q40 84 40 84 q0 0 -40 84" {STK_T}/>
  <!-- 섞는 사람 + 그릇 -->
  <circle cx="168" cy="96" r="22" {STK}/>
  <path d="M168 118 L168 160" {STK}/>
  <path d="M168 132 L150 176 M168 132 L200 150" {STK}/>
  <path d="M150 190 q34 34 68 0" {STK}/>
  <path d="M150 190 L218 190" {STK_T}/>
  <path d="M200 150 l6 34" {STK_T}/>
  <!-- 화살표 -->
  <path d="M232 150 l30 0 M254 140 l10 10 l-10 10" {STK_T}/>
  <!-- 새 사람(무기 든 느낌) -->
  <g transform="translate(276,150) scale(0.7)">
    <circle cx="0" cy="-30" r="18" {STK}/><path d="M0 -12 L0 26" {STK}/>
    <path d="M0 -2 L26 -14 M0 -2 L-22 8" {STK}/><path d="M0 26 L-18 60 M0 26 L18 60" {STK}/></g>
</svg>'''


def _blank() -> str:
    # 자존심 내려놓고 백지에서 다시 + 깃발 든 작은 사람
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <!-- 화이트보드 -->
  <rect x="40" y="40" width="150" height="110" rx="6" {STK}/>
  <!-- 지우는 사람 -->
  <circle cx="150" cy="188" r="24" {STK}/>
  <path d="M150 212 L150 262" {STK}/>
  <path d="M150 226 L118 120 M150 226 L182 250" {STK}/>
  <rect x="104" y="104" width="26" height="18" rx="4" {STK_T}/>
  <!-- 깃발 든 작은 사람(정상) -->
  <g transform="translate(226,196) scale(0.6)">
    <circle cx="0" cy="0" r="18" {STK}/><path d="M0 18 L0 62" {STK}/>
    <path d="M0 30 L-24 10 M0 30 L26 22" {STK}/><path d="M0 62 L-16 100 M0 62 L16 100" {STK}/>
    <line x1="26" y1="22" x2="30" y2="-40" {STK}/><path d="M30 -40 l40 12 l-40 12" {STK_T}/></g>
  <line x1="70" y1="276" x2="260" y2="276" {STK_T}/>
</svg>'''


# ─────────────── 미용(단발) 손그림 라이브러리 — 장면↔주제 매칭 ───────────────
def _face(cx, cy, smile=True):
    eyes = f'<circle cx="{cx-13}" cy="{cy}" r="3.5" fill="#141416"/><circle cx="{cx+13}" cy="{cy}" r="3.5" fill="#141416"/>'
    mouth = (f'<path d="M{cx-9} {cy+18} q9 7 18 0" {STK_T}/>' if smile
             else f'<path d="M{cx-8} {cy+20} l16 0" {STK_T}/>')
    return eyes + mouth


def _hair_triangle() -> str:
    # 부한 삼각형 단발 + 삼각김밥 아이콘
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <path d="M150 58 L92 214 M150 58 L208 214" {STK}/>
  <path d="M92 214 q58 26 116 0" {STK}/>
  <path d="M150 58 q-34 2 -40 46 M150 58 q34 2 40 46" {STK_T}/>
  <path d="M124 150 q0 44 26 58 q26 -14 26 -58" {STK_T}/>
  {_face(150,150)}
  <g transform="translate(224,52)"><path d="M0 44 L24 2 L48 44 Z" {STK_T}/>
    <rect x="13" y="30" width="22" height="14" rx="2" {STK_T}/></g>
  <text x="150" y="250" text-anchor="middle" font-family="NanumPenPoster" font-size="26" fill="#22242a">삼각형 ≠ 면</text>
</svg>'''


def _hair_slim() -> str:
    # 부한 두상(점선 둥근 가이드) → 화살표 → 슬림
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <!-- 왼쪽: 퍼진 머리 + 둥근 두상 가이드 -->
  <circle cx="72" cy="120" r="46" stroke-dasharray="5 9" {STK_T}/>
  <path d="M30 128 q-4 -66 42 -70 q46 4 42 70" {STK}/>
  <path d="M30 128 q8 34 20 50 M114 128 q-8 34 -20 50" {STK_T}/>
  <path d="M54 138 q0 34 18 46 q18 -12 18 -46" {STK_T}/>{_face(72,138,False)}
  <!-- 화살표 -->
  <path d="M126 150 l40 0 M158 140 l10 10 l-10 10" {STK}/>
  <!-- 오른쪽: 슬림 -->
  <path d="M196 126 q-2 -64 40 -66 q42 2 40 66 q-6 40 -40 52 q-34 -12 -40 -52" {STK}/>
  {_face(236,140)}
  <text x="150" y="250" text-anchor="middle" font-family="NanumPenPoster" font-size="26" fill="#22242a">면 정리 = 슬림</text>
</svg>'''


def _hair_air() -> str:
    # 공기감 — 가위 + 머리카락 '사이' 공간
    strands = ""
    for i, x in enumerate((150, 178, 206, 234)):
        strands += f'<path d="M{x} 60 q-8 70 4 150" {STK_T}/>'
    airs = ""
    for x, y in ((166, 110), (194, 150), (222, 120), (180, 200), (210, 190)):
        airs += f'<path d="M{x} {y} q10 -8 8 6" {STK_T}/>'
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <!-- 가위 -->
  <g transform="translate(40,120) rotate(-18)">
    <circle cx="0" cy="-16" r="15" {STK}/><circle cx="0" cy="20" r="15" {STK}/>
    <path d="M12 -6 L74 34 M12 10 L74 -30" {STK}/></g>
  {strands}{airs}
  <text x="150" y="250" text-anchor="middle" font-family="NanumPenPoster" font-size="26" fill="#22242a">'사이'를 자른다</text>
</svg>'''


def _hair_mood() -> str:
    # 무드 — 직선(차가움) vs 곡선(부드러움) 두 얼굴
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <!-- 왼: 직선 단발 -->
  <path d="M40 78 L40 176 L112 176 L112 78" {STK}/>
  <path d="M40 78 L112 78" {STK}/>
  <path d="M58 120 q0 44 18 52 q18 -8 18 -52" {STK_T}/>{_face(76,120,False)}
  <text x="76" y="204" text-anchor="middle" font-family="NanumPenPoster" font-size="24" fill="#22242a">직선=차갑게</text>
  <!-- 우: 곡선 단발 -->
  <path d="M188 76 q-24 4 -24 54 q0 44 24 56 M260 76 q24 4 24 54 q0 44 -24 56" {STK}/>
  <path d="M188 76 q36 -14 72 0" {STK}/>
  <path d="M206 120 q0 44 18 52 q18 -8 18 -52" {STK_T}/>{_face(224,120)}
  <text x="224" y="204" text-anchor="middle" font-family="NanumPenPoster" font-size="24" fill="#22242a">곡선=부드럽게</text>
</svg>'''


def _hair_texture() -> str:
    # 결 — 흐르는 웨이브 결(유행이 내 것이 되는 지점)
    waves = ""
    for i, y in enumerate((80, 116, 152, 188)):
        waves += f'<path d="M46 {y} q34 -20 68 0 q34 20 68 0 q34 -20 68 0" {STK}/>'
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  {waves}
  <path d="M228 96 l18 -6 M232 128 l18 0 M228 160 l18 6" {STK_T}/>
  <text x="150" y="244" text-anchor="middle" font-family="NanumPenPoster" font-size="26" fill="#22242a">결이 곧 유행</text>
</svg>'''


def _hair_verdict() -> str:
    # 판정 — 얼굴 + 손거울 + 말풍선 "면?"
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <path d="M96 108 q-24 4 -24 52 q0 44 24 56 q-2 30 -2 30 M204 108 q24 4 24 52 q0 44 -24 56"
        {STK}/>
  <path d="M96 108 q54 -18 108 0" {STK}/>
  <path d="M120 150 q0 46 30 60 q30 -14 30 -60" {STK_T}/>{_face(150,150)}
  <!-- 말풍선 면? -->
  <g><ellipse cx="238" cy="72" rx="42" ry="30" {STK}/>
    <path d="M214 96 l-6 20 l24 -12" {STK}/>
    <text x="238" y="84" font-family="KyoboPoster" font-size="40" fill="#141416" text-anchor="middle">면?</text></g>
</svg>'''


SCENES = {
    "wall": _wall, "jeer": _jeer, "tally": _tally,
    "shame_run": _shame_run, "mix": _mix, "blank": _blank,
    "hair_triangle": _hair_triangle, "hair_slim": _hair_slim, "hair_air": _hair_air,
    "hair_mood": _hair_mood, "hair_texture": _hair_texture, "hair_verdict": _hair_verdict,
}


@dataclass
class Panel:
    num: str
    heading: str
    body: str          # 줄바꿈은 \n
    scene: str         # SCENES 키
    side_note: str = ""  # 그림 옆 작은 보조문(선택)


@dataclass
class PosterSpec:
    title: str
    panels: list = field(default_factory=list)   # 6개 권장
    banner: str = ""     # 하단 검은 강조 띠
    closer_hand: str = ""  # 마무리 손글씨(큰)
    closer_sub: str = ""   # 마무리 보조


def _panel_html(p: Panel) -> str:
    svg = SCENES[p.scene]()
    body = p.body.replace("\n", "<br>")
    note = f'<div class="note">{p.side_note}</div>' if p.side_note else ""
    return f'''<div class="panel">
  <div class="phead"><span class="num">{p.num}</span><span class="htxt">{p.heading}</span></div>
  <div class="pbody">
    <div class="ptext">{body}</div>
    <div class="part">{svg}{note}</div>
  </div>
</div>'''


def build_html(spec: PosterSpec) -> str:
    faces = _font_face("KyoboPoster", FONT_HAND) + _font_face("NanumPenPoster", FONT_PEN)
    panels = "".join(_panel_html(p) for p in spec.panels)
    banner = f'<div class="banner">{spec.banner}</div>' if spec.banner else ""
    closer = ""
    if spec.closer_hand or spec.closer_sub:
        closer = (f'<div class="closer"><div class="chand">{spec.closer_hand}</div>'
                  f'<div class="csub">{spec.closer_sub}</div></div>')
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
{faces}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px}}
body{{background:#fbfbf9;color:#141416;position:relative;overflow:hidden}}
.wrap{{padding:56px 60px 40px}}
.title{{font-family:KyoboPoster;font-size:104px;text-align:center;line-height:1;letter-spacing:2px}}
.tunder{{width:520px;height:10px;margin:14px auto 4px;
  background:radial-gradient(closest-side,#141416 92%,transparent);border-radius:8px;opacity:.5}}
.stars{{position:absolute;top:70px;right:96px;font-family:KyoboPoster;font-size:52px;color:#141416;opacity:.55}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px 40px;margin-top:26px}}
.panel{{min-height:236px}}
.phead{{display:flex;align-items:center;gap:14px;margin-bottom:6px}}
.num{{font-family:KyoboPoster;font-size:34px;color:#fbfbf9;background:#141416;
  width:46px;height:46px;border-radius:11px;display:flex;align-items:center;justify-content:center;
  padding-top:4px}}
.htxt{{font-family:KyoboPoster;font-size:40px;line-height:1;white-space:nowrap}}
.pbody{{display:flex;gap:8px;align-items:center}}
.ptext{{font-family:NanumPenPoster;font-size:31px;line-height:1.26;flex:1;color:#22242a}}
.part{{width:196px;height:196px;flex:none;position:relative}}
.part svg{{width:196px;height:196px}}
.note{{position:absolute;bottom:-2px;left:0;right:0;text-align:center;
  font-family:NanumPenPoster;font-size:26px;color:#22242a}}
.banner{{font-family:KyoboPoster;font-size:40px;color:#fbfbf9;background:#141416;
  display:inline-block;padding:8px 22px 12px;border-radius:8px;transform:rotate(-2deg);
  margin:22px 0 0 8px;line-height:1.15}}
.closer{{text-align:center;margin-top:14px}}
.chand{{font-family:KyoboPoster;font-size:56px}}
.chand b{{background:#141416;color:#fbfbf9;padding:2px 14px 6px;border-radius:8px}}
.csub{{font-family:NanumPenPoster;font-size:34px;color:#22242a;margin-top:6px}}
</style></head><body>
<div class="stars">✦ ✧</div>
<div class="wrap">
  <div class="title">{spec.title}</div>
  <div class="tunder"></div>
  <div class="grid">{panels}</div>
  {banner}{closer}
</div>
<script>
// 헤딩이 칸 폭을 넘으면 폰트 자동 축소(잘림·줄바꿈 방지) — 긴 헤딩도 배관이 흡수.
document.querySelectorAll('.phead').forEach(function(h){{
  var t=h.querySelector('.htxt'); if(!t) return;
  var avail=h.clientWidth - h.querySelector('.num').offsetWidth - 20;
  var fs=40;
  while(t.scrollWidth>avail && fs>24){{ fs-=1; t.style.fontSize=fs+'px'; }}
}});
</script>
</body></html>'''


def render_poster(spec: PosterSpec, out_png: str) -> str:
    """HTML→PNG (playwright chromium). 산출 PNG 경로 반환."""
    html = build_html(spec)
    tmp = Path(out_png).with_suffix(".html")
    tmp.write_text(html, encoding="utf-8")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        page.goto(tmp.resolve().as_uri())
        page.wait_for_timeout(350)
        page.screenshot(path=out_png, clip={"x": 0, "y": 0, "width": W, "height": H})
        browser.close()
    return out_png


# ── 포맷 검증용 데모: 레퍼런스 "지독하게 잘하는 법" 재현(발행 아님) ──
def demo_spec() -> PosterSpec:
    return PosterSpec(
        title="지독하게 잘하는 법",
        panels=[
            Panel("1", "일단 부딪히고 해본다",
                  "생각만으로는\n아무것도\n바뀌지 않는다.\n\n행동이 모든 걸\n열어준다.", "wall"),
            Panel("2", "못한다는 소리도 즐긴다",
                  "평가에 흔들리지 않고\n오히려 동력으로.\n\n비난은 나를\n단단하게 만드는 연료.", "jeer"),
            Panel("3", "안 되더라도 백 번은 해본다",
                  "실패는 결과가 아니라\n과정이다.\n\n포기 안 한 횟수가\n결국 실력으로 남는다.", "tally"),
            Panel("4", "쪽팔려도 계속한다",
                  "창피함은\n잠시의 감정일 뿐.\n\n성공은 그 감정을\n넘어선 사람의 것.", "shame_run"),
            Panel("5", "타인의 스킬을 내 방식으로",
                  "그대로 복사하지 않는다.\n재해석해 새로 만든다.", "mix", "나만의 방식 = 무기"),
            Panel("6", "필요하면 백지에서 다시 배운다",
                  "자존심 내려놓고\n처음으로 갈 용기.\n\n성장은 과거의 나와\n결별하는 과정.", "blank"),
        ],
        banner="쪽팔림은 재능을 이기고, 습관은 결과를 만든다",
        closer_hand="오늘도, <b>지독하게</b> 해보기!",
        closer_sub="결국, 해내는 사람은 그렇게 행동한다.",
    )


# ── 단발 카드(차노 재정의) — 조회수 검증 주제(단발 170만·숏컷)를 카드로 ──
def danbal_spec() -> PosterSpec:
    return PosterSpec(
        title="단발 실패 안 하는 법",
        panels=[
            Panel("1", "끝이 아니라 '면'을 본다",
                  "단발했는데 부해 보였다면\n끝을 잘못 잘라서가\n아니에요.\n옆면이 '면'이 아니라\n'삼각형'이라서예요.", "hair_triangle"),
            Panel("2", "면이 정리되면 슬림해진다",
                  "두상은 둥근데\n머리가 퍼지면 각이 생겨요.\n같은 길이도 면을 다듬으면\n한 톤 슬림해집니다.", "hair_slim"),
            Panel("3", "가벼움 = 공기를 자른 것",
                  "숱을 덜어내는 게 아니라\n머리카락 '사이'를\n디자인해요.\n공간이 생기면\n같은 숱도 가벼워집니다.", "hair_air"),
            Panel("4", "얼굴형이 아니라 '무드'",
                  "안 어울리는 얼굴은 없어요.\n무드가 안 맞는 단발이\n있을 뿐.\n직선이 강하면 차갑고\n곡선이 남으면 부드러워요.", "hair_mood"),
            Panel("5", "유행 단발은 '결'로 산다",
                  "웬디컷·허쉬컷이\n어울리려면\n레이어가 아니라 '결'이에요.\n결이 살면 유행이\n내 것이 됩니다.", "hair_texture"),
            Panel("6", "상담 때 이걸 물어보세요",
                  "\"끝을 다듬을까요,\n면을 다듬을까요?\"\n이 한마디가\n단발의 성패를 가릅니다.", "hair_verdict"),
        ],
        banner="단발 실패, 끝이 아니라 면에 있습니다",
        closer_hand="당신의 단발, <b>면</b>을 봤나요?",
        closer_sub="저장했다가, 상담 때 무드부터 물어보세요.",
    )


SPECS = {"demo": demo_spec, "danbal": danbal_spec}

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/cardposter.png"
    which = "demo"
    if "--spec" in sys.argv:
        which = sys.argv[sys.argv.index("--spec") + 1]
    render_poster(SPECS[which](), out)
    print("OK →", out)
