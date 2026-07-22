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
  <text x="150" y="250" text-anchor="middle" font-family="NanumPenPoster" font-size="30" fill="#22242a">삼각형 ≠ 면</text>
</svg>'''


def _hair_slim() -> str:
    # 퍼져서 각진 두상(둥근 가이드) → 면 정리 → 슬림. 두 머리 비교.
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <!-- 왼쪽: 퍼진 각진 단발 + 둥근 두상 점선 -->
  <circle cx="74" cy="118" r="42" stroke-dasharray="5 9" {STK_T}/>
  <path d="M32 108 q0 -52 42 -52 q42 0 42 52 q4 40 -12 58 l-60 0 q-16 -18 -12 -58 z" {STK}/>
  {_face(74,120,False)}
  <text x="74" y="204" text-anchor="middle" font-family="NanumPenPoster" font-size="26" fill="#22242a">퍼짐·각</text>
  <!-- 화살표 -->
  <path d="M128 150 l38 0 M158 140 l10 10 l-10 10" {STK}/>
  <!-- 오른쪽: 면 정리된 슬림 단발 -->
  <path d="M200 104 q0 -50 38 -50 q38 0 38 50 q0 40 -10 58 l-56 0 q-10 -18 -10 -58 z" {STK}/>
  <line x1="200" y1="104" x2="198" y2="162" {STK_T}/><line x1="276" y1="104" x2="278" y2="162" {STK_T}/>
  {_face(238,120)}
  <text x="238" y="204" text-anchor="middle" font-family="NanumPenPoster" font-size="26" fill="#22242a">면 정리=슬림</text>
</svg>'''


def _hair_air() -> str:
    # 가벼움=공기 — 머리에 '공기'가 든 가벼운 결(사이 공간)
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <!-- 얼굴 -->
  <ellipse cx="150" cy="168" rx="52" ry="60" {STK}/>{_face(150,158)}
  <!-- 가벼운 머리(위로 뜨고 사이 벌어진 결) -->
  <path d="M104 128 q-6 -46 18 -62" {STK}/>
  <path d="M132 112 q-2 -50 14 -66" {STK}/>
  <path d="M168 112 q2 -50 -14 -66" {STK}/>
  <path d="M196 128 q6 -46 -18 -62" {STK}/>
  <!-- 사이 공기 표시(작은 소용돌이) -->
  <path d="M124 96 q10 -6 8 6" {STK_T}/><path d="M150 84 q10 -6 8 6" {STK_T}/>
  <path d="M176 96 q10 -6 8 6" {STK_T}/>
  <text x="150" y="256" text-anchor="middle" font-family="NanumPenPoster" font-size="30" fill="#22242a">사이에 공기가 든다</text>
</svg>'''


def _hair_mood() -> str:
    # 무드 — 직선(차가움) vs 곡선(부드러움) 두 얼굴
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <!-- 왼: 직선 단발 -->
  <path d="M40 78 L40 176 L112 176 L112 78" {STK}/>
  <path d="M40 78 L112 78" {STK}/>
  <path d="M58 120 q0 44 18 52 q18 -8 18 -52" {STK_T}/>{_face(76,120,False)}
  <text x="76" y="204" text-anchor="middle" font-family="NanumPenPoster" font-size="27" fill="#22242a">직선=차갑게</text>
  <!-- 우: 곡선 단발 -->
  <path d="M188 76 q-24 4 -24 54 q0 44 24 56 M260 76 q24 4 24 54 q0 44 -24 56" {STK}/>
  <path d="M188 76 q36 -14 72 0" {STK}/>
  <path d="M206 120 q0 44 18 52 q18 -8 18 -52" {STK_T}/>{_face(224,120)}
  <text x="224" y="204" text-anchor="middle" font-family="NanumPenPoster" font-size="27" fill="#22242a">곡선=부드럽게</text>
</svg>'''


def _hair_texture() -> str:
    # 결 — 웨이브 결이 살아 흐르는 단발(머리+결)
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <!-- 얼굴 -->
  <ellipse cx="150" cy="150" rx="50" ry="58" {STK}/>{_face(150,142)}
  <!-- 윗머리 -->
  <path d="M104 118 q46 -40 92 0" {STK}/>
  <!-- 양옆 흐르는 웨이브 결 -->
  <path d="M100 120 q-20 22 -8 44 q-16 20 -4 42 q-14 18 0 38" {STK}/>
  <path d="M120 138 q-14 18 -4 36 q-12 16 -2 34" {STK_T}/>
  <path d="M200 120 q20 22 8 44 q16 20 4 42 q14 18 0 38" {STK}/>
  <path d="M180 138 q14 18 4 36 q12 16 2 34" {STK_T}/>
  <text x="150" y="266" text-anchor="middle" font-family="NanumPenPoster" font-size="30" fill="#22242a">결이 살면 내 것</text>
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


# ── 긴 얼굴형 단발 공식 손그림 6종 ──
def _lf_vertical() -> str:
    # 긴 얼굴 + 세로 강조(일자단발) = 길어보임
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <ellipse cx="150" cy="150" rx="58" ry="90" {STK}/>{_face(150,138,False)}
  <line x1="150" y1="52" x2="150" y2="252" {STK_T} stroke-dasharray="5 9"/>
  <path d="M94 116 q-10 74 6 120" {STK}/><path d="M206 116 q10 74 -6 120" {STK}/>
  <path d="M150 256 l0 20 M143 270 l7 9 l7 -9" {STK_T}/>
  <text x="150" y="292" text-anchor="middle" font-family="NanumPenPoster" font-size="27" fill="#22242a">세로 = 길어보임</text>
</svg>'''


def _lf_cut() -> str:
    # 밸런스 도식 — 세로선을 코끝 아래 가로선이 끊음(O). 너무 위서 끊으면 아래 세로 남음(주의).
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <!-- 왼: 코끝 아래서 끊음 = 시선 끊김(좋음) -->
  <ellipse cx="80" cy="140" rx="32" ry="66" {STK}/>
  <line x1="80" y1="80" x2="80" y2="180" {STK_T} stroke-dasharray="5 7"/>
  <line x1="48" y1="182" x2="112" y2="182" {STK}/>
  <path d="M96 168 l7 7 l12 -13" {STK_T}/>
  <text x="80" y="224" text-anchor="middle" font-family="NanumPenPoster" font-size="22" fill="#22242a">코끝 아래=끊김 O</text>
  <!-- 우: 너무 위서 끊음 = 아래 세로 남음(주의) -->
  <ellipse cx="220" cy="140" rx="32" ry="66" {STK}/>
  <line x1="188" y1="128" x2="252" y2="128" {STK_T}/>
  <line x1="220" y1="130" x2="220" y2="204" {STK}/>
  <path d="M234 146 l16 16 M250 146 l-16 16" {STK_T}/>
  <text x="220" y="224" text-anchor="middle" font-family="NanumPenPoster" font-size="22" fill="#22242a">너무 위=세로 남음</text>
  <text x="150" y="252" text-anchor="middle" font-family="NanumPenPoster" font-size="24" fill="#22242a">끊는 위치가 밸런스</text>
</svg>'''


def _lf_jaw() -> str:
    # 턱선 기준 — 위=가로선, 아래=세로선
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <ellipse cx="150" cy="140" rx="56" ry="80" {STK}/>{_face(150,128)}
  <line x1="88" y1="192" x2="212" y2="192" {STK}/>
  <text x="232" y="198" font-family="NanumPenPoster" font-size="27" fill="#22242a">턱선</text>
  <path d="M110 168 l9 9 l18 -20" {STK_T}/>
  <text x="150" y="256" text-anchor="middle" font-family="NanumPenPoster" font-size="23" fill="#22242a">위는 넓게·아래는 길게</text>
</svg>'''


def _lf_weight() -> str:
    # 무게중심 — 옆모습 + 코끝에서 사선 아래 15도 선. 그 밑으로 웨이트(무게) 잡기 → 짧아 보임.
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <!-- 동그라미 캐릭터(옆모습) -->
  <circle cx="150" cy="120" r="56" {STK}/>
  <!-- 코끝(오른쪽 삐죽) -->
  <path d="M204 116 q14 6 4 18" {STK}/>
  <!-- 눈·입(옆) -->
  <circle cx="178" cy="110" r="4" fill="#141416"/>
  <path d="M186 138 q9 5 16 -1" {STK_T}/>
  <!-- 코끝 기준 수평 점선(각도 기준선) -->
  <line x1="150" y1="130" x2="252" y2="130" {STK_T} stroke-dasharray="4 7"/>
  <!-- 코끝에서 사선 아래 15도 실선(코끝 → 뒤아래로) -->
  <line x1="208" y1="130" x2="60" y2="170" {STK}/>
  <!-- 15도 각 표시 -->
  <path d="M234 130 q-6 8 -13 11" {STK_T}/>
  <text x="214" y="126" font-family="NanumPenPoster" font-size="19" fill="#6b6b6b">15°</text>
  <!-- 사선 '아래'가 웨이트 존: 해칭 + 아래 화살 -->
  <path d="M96 174 l-10 16 M120 176 l-10 16 M150 176 l-10 16 M180 172 l-10 16" {STK_T}/>
  <path d="M150 196 l0 26 M143 216 l7 10 l7 -10" {STK_T}/>
  <text x="150" y="250" text-anchor="middle" font-family="NanumPenPoster" font-size="25" fill="#141416">이 선 아래로 웨이트</text>
  <text x="150" y="284" text-anchor="middle" font-family="NanumPenPoster" font-size="24" fill="#6b6b6b">= 얼굴이 짧아 보임</text>
</svg>'''


def _lf_expand() -> str:
    # 컬 = 가로 물결(얼굴 위·아래에 좌우로 흐르는 웨이브). 얼굴은 가로로 통통한 둥근 얼굴.
    # (이찬호 손그림 2026-07-22: 세로 옆가닥 X → 가로 물결선 위2·아래2)
    def _vwave(x, y0, n=3, h=34, a=16):
        # 위→아래로 확실히 들어갔다 나왔다(둥근 컬). 지그재그 X, 큰 둥근 물결.
        d = f'M{x} {y0}'
        s = -1
        for _ in range(n):
            d += f' c {a*s} {h*0.28:.0f}, {a*s} {h*0.72:.0f}, 0 {h}'
            s *= -1
        return d
    # 얼굴 양 옆으로 세로 둥근 컬 2줄씩(손그림대로 — 세로)
    right = " ".join(_vwave(x, 100) for x in (212, 238))
    left = " ".join(_vwave(x, 100) for x in (88, 62))
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <ellipse cx="150" cy="150" rx="46" ry="52" {STK}/>{_face(150,143)}
  <path d="{right}" fill="none" {STK}/>
  <path d="{left}" fill="none" {STK}/>
  <text x="150" y="290" text-anchor="middle" font-family="NanumPenPoster" font-size="26" fill="#22242a">옆에 세로 물결컬 = 통통</text>
</svg>'''


def _lf_dry() -> str:
    # 말리기 — 비스듬히 앞으로
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <ellipse cx="150" cy="150" rx="54" ry="78" {STK}/>{_face(150,140)}
  <path d="M112 108 L64 60 M64 60 l4 26 M64 60 l26 4" {STK}/>
  <path d="M188 108 L236 60 M236 60 l-4 26 M236 60 l-26 4" {STK}/>
  <text x="150" y="288" text-anchor="middle" font-family="NanumPenPoster" font-size="27" fill="#22242a">비스듬히 앞으로</text>
</svg>'''


def _lf_trim() -> str:
    # 불필요한 부피 정리 — 옆으로 뜬 부피를 커트/펌으로 덜어냄
    return f'''<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
  <ellipse cx="150" cy="152" rx="48" ry="72" {STK}/>{_face(150,142)}
  <!-- 옆으로 뜬 불필요한 부피(점선=덜어낼 부분) -->
  <path d="M102 120 q-44 22 -34 74" {STK_T} stroke-dasharray="6 8"/>
  <path d="M198 120 q44 22 34 74" {STK_T} stroke-dasharray="6 8"/>
  <!-- 정리된 라인(실선) -->
  <path d="M104 120 q-20 30 -8 66" {STK}/><path d="M196 120 q20 30 8 66" {STK}/>
  <!-- 가위(덜어냄) -->
  <g transform="translate(232,150) rotate(20)">
    <circle cx="0" cy="-13" r="12" {STK}/><circle cx="0" cy="13" r="12" {STK}/>
    <path d="M10 -4 L54 20 M10 4 L54 -20" {STK}/></g>
  <text x="150" y="256" text-anchor="middle" font-family="NanumPenPoster" font-size="27" fill="#22242a">튀어나온 곳 다듬기</text>
</svg>'''


SCENES = {
    "wall": _wall, "jeer": _jeer, "tally": _tally,
    "shame_run": _shame_run, "mix": _mix, "blank": _blank,
    "hair_triangle": _hair_triangle, "hair_slim": _hair_slim, "hair_air": _hair_air,
    "hair_mood": _hair_mood, "hair_texture": _hair_texture, "hair_verdict": _hair_verdict,
    "lf_vertical": _lf_vertical, "lf_cut": _lf_cut, "lf_jaw": _lf_jaw,
    "lf_weight": _lf_weight, "lf_expand": _lf_expand, "lf_dry": _lf_dry, "lf_trim": _lf_trim,
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
.wu{{position:relative;display:inline-block}}
.wu::after{{content:"";position:absolute;left:-4px;right:-4px;bottom:-20px;height:14px;
  background:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='14'><path d='M0 9 q11 -9 22 0 t22 0' fill='none' stroke='%23141416' stroke-width='3'/></svg>") repeat-x;
  background-size:auto 14px}}
.stars{{position:absolute;top:70px;right:96px;font-family:KyoboPoster;font-size:52px;color:#141416;opacity:.55}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px 40px;margin-top:26px}}
.panel{{min-height:236px}}
.phead{{display:flex;align-items:center;gap:14px;margin-bottom:6px}}
.num{{font-family:KyoboPoster;font-size:34px;color:#fbfbf9;background:#141416;
  width:46px;height:46px;border-radius:11px;display:flex;align-items:center;justify-content:center;
  padding-top:4px}}
.htxt{{font-family:KyoboPoster;font-size:40px;line-height:1;white-space:nowrap}}
.pbody{{display:flex;gap:8px;align-items:center}}
.ptext{{font-family:NanumPenPoster;font-size:32px;line-height:1.25;flex:1;color:#22242a}}
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
  {'' if 'class="wu"' in spec.title else '<div class="tunder"></div>'}
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


def _shoot(html: str, out_png: str) -> str:
    """HTML 문자열 → PNG (playwright chromium). 산출 PNG 경로 반환."""
    tmp = Path(out_png).with_suffix(".html")
    tmp.write_text(html, encoding="utf-8")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        page.goto(tmp.resolve().as_uri())
        try:
            page.evaluate("document.fonts && document.fonts.ready")
        except Exception:
            pass
        page.wait_for_timeout(650)
        page.screenshot(path=out_png, clip={"x": 0, "y": 0, "width": W, "height": H})
        browser.close()
    return out_png


def render_poster(spec: PosterSpec, out_png: str) -> str:
    """격자형 6칸 포스터."""
    return _shoot(build_html(spec), out_png)


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


# ═══════════════════════ 만화/변칙배열(zine) 모드 ═══════════════════════
# 이찬호 2026-07-22: "배열이 변칙적이면 / 만화스럽게 손글씨 같게 / 내 주제를 섞어".
# 반듯한 격자 대신 기울어진 말풍선 블록을 흩뿌리고, 선을 울렁이게(sketch) 만든다.

def _rough(inner: str, seed: int, scale: int = 4) -> str:
    """규격 유지 — 예전엔 feTurbulence로 울렁였지만 '찌그러짐' 지적(이찬호 2026-07-22)으로
    왜곡 제거. 깔끔한 손그림(교보/나눔펜 + 균일 선)으로 규격화."""
    return f'<g>{inner}</g>'


def _d_scissors(seed) -> str:
    inner = (f'<g transform="rotate(-16 65 65)"><circle cx="40" cy="46" r="13" {STK}/>'
             f'<circle cx="40" cy="86" r="13" {STK}/><path d="M52 54 L108 76 M52 78 L108 56" {STK}/></g>'
             f'<circle cx="92" cy="30" r="2.5" fill="#141416"/><circle cx="104" cy="44" r="2.5" fill="#141416"/>'
             f'<circle cx="86" cy="52" r="2.5" fill="#141416"/>')
    return f'<svg viewBox="0 0 130 130" xmlns="http://www.w3.org/2000/svg">{_rough(inner, seed)}</svg>'


def _d_angle(seed) -> str:
    inner = (f'<line x1="16" y1="104" x2="114" y2="104" {STK}/>'
             f'<path d="M46 104 L88 30" {STK}/><path d="M70 104 L104 44" {STK_T}/>'
             f'<path d="M46 104 q20 -4 26 -18" {STK_T}/>')
    return f'<svg viewBox="0 0 130 130" xmlns="http://www.w3.org/2000/svg">{_rough(inner, seed)}</svg>'


def _d_wave(seed) -> str:
    inner = (f'<path d="M14 48 q22 -16 44 0 q22 16 44 0" {STK}/>'
             f'<path d="M14 74 q22 -16 44 0 q22 16 44 0" {STK}/>'
             f'<path d="M14 100 q22 -16 44 0 q22 16 44 0" {STK}/>'
             f'<path d="M104 60 l12 -4 M104 86 l12 4" {STK_T}/>')
    return f'<svg viewBox="0 0 130 130" xmlns="http://www.w3.org/2000/svg">{_rough(inner, seed)}</svg>'


def _d_triface(seed) -> str:
    inner = (f'<path d="M65 22 L34 102 M65 22 L96 102" {STK}/><path d="M34 102 q31 12 62 0" {STK}/>'
             f'<circle cx="56" cy="74" r="2.6" fill="#141416"/><circle cx="74" cy="74" r="2.6" fill="#141416"/>'
             f'<path d="M58 84 q7 5 14 0" {STK_T}/>')
    return f'<svg viewBox="0 0 130 130" xmlns="http://www.w3.org/2000/svg">{_rough(inner, seed)}</svg>'


def _d_drop(seed) -> str:
    inner = (f'<path d="M65 26 q22 30 22 46 a22 22 0 1 1 -44 0 q0 -16 22 -46 z" {STK}/>'
             f'<path d="M34 108 q31 10 62 0" {STK_T} stroke-dasharray="4 7"/>')
    return f'<svg viewBox="0 0 130 130" xmlns="http://www.w3.org/2000/svg">{_rough(inner, seed)}</svg>'


def _d_moods(seed) -> str:
    inner = (f'<rect x="16" y="34" width="42" height="60" rx="3" {STK}/>'
             f'<circle cx="30" cy="60" r="2.4" fill="#141416"/><circle cx="44" cy="60" r="2.4" fill="#141416"/>'
             f'<path d="M30 74 l14 0" {STK_T}/>'
             f'<path d="M74 40 q-12 2 -12 28 q0 24 24 30 q24 -6 24 -30 q0 -26 -12 -28 q-12 -6 -24 0 z" {STK}/>'
             f'<circle cx="80" cy="66" r="2.4" fill="#141416"/><circle cx="96" cy="66" r="2.4" fill="#141416"/>'
             f'<path d="M80 78 q8 6 16 0" {STK_T}/>')
    return f'<svg viewBox="0 0 130 130" xmlns="http://www.w3.org/2000/svg">{_rough(inner, seed)}</svg>'


def _d_steps(seed) -> str:
    # 순서 1·2·3
    inner = (f'<circle cx="26" cy="40" r="15" {STK}/><text x="26" y="49" text-anchor="middle" font-family="KyoboPoster" font-size="22" fill="#141416">1</text>'
             f'<circle cx="65" cy="66" r="15" {STK}/><text x="65" y="75" text-anchor="middle" font-family="KyoboPoster" font-size="22" fill="#141416">2</text>'
             f'<circle cx="104" cy="92" r="15" {STK}/><text x="104" y="101" text-anchor="middle" font-family="KyoboPoster" font-size="22" fill="#141416">3</text>'
             f'<path d="M40 49 l12 8 M79 75 l12 8" {STK_T}/>')
    return f'<svg viewBox="0 0 130 130" xmlns="http://www.w3.org/2000/svg">{_rough(inner, seed)}</svg>'


def _d_dir(seed) -> str:
    # 방향 — 휘는 화살표
    inner = f'<path d="M16 96 q10 -66 84 -60" {STK}/><path d="M100 36 l4 22 l-22 -6" {STK}/>'
    return f'<svg viewBox="0 0 130 130" xmlns="http://www.w3.org/2000/svg">{_rough(inner, seed)}</svg>'


def _d_think(seed) -> str:
    # 생각 — 전구
    inner = (f'<path d="M65 20 a30 30 0 0 1 20 52 q-6 6 -6 16 l-28 0 q0 -10 -6 -16 a30 30 0 0 1 20 -52 z" {STK}/>'
             f'<path d="M52 96 l26 0 M56 108 l18 0" {STK_T}/>'
             f'<path d="M65 34 q-12 6 -12 22" {STK_T}/>')
    return f'<svg viewBox="0 0 130 130" xmlns="http://www.w3.org/2000/svg">{_rough(inner, seed)}</svg>'


# ── 머리 '특징'을 직접 그린 손그림(이찬호: 추상아이콘 말고 그 머리 모양) ──
def _hd_face(cx, cy, smile=True):
    eyes = f'<circle cx="{cx-11}" cy="{cy}" r="3" fill="#141416"/><circle cx="{cx+11}" cy="{cy}" r="3" fill="#141416"/>'
    mouth = (f'<path d="M{cx-7} {cy+15} q7 6 14 0" {STK_T}/>' if smile
             else f'<path d="M{cx-6} {cy+16} l12 0" {STK_T}/>')
    return eyes + mouth


# 규격 손그림 — 균일한 깔끔 선(왜곡 없음). viewBox 140.
DCS = 'fill="none" stroke="#141416" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"'
DCS_T = 'fill="none" stroke="#141416" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"'


def _dface(cx, cy, smile=True):
    eyes = f'<circle cx="{cx-10}" cy="{cy}" r="2.8" fill="#141416"/><circle cx="{cx+10}" cy="{cy}" r="2.8" fill="#141416"/>'
    mouth = (f'<path d="M{cx-6} {cy+14} q6 5 12 0" {DCS_T}/>' if smile
             else f'<path d="M{cx-5} {cy+15} l10 0" {DCS_T}/>')
    return eyes + mouth


def _hd_space(seed) -> str:
    # 숱치기=공간 — 머리카락 사이 '공간'(정돈된 갈라짐)
    inner = (f'<circle cx="70" cy="76" r="30" {DCS}/>{_dface(70,74)}'
             f'<path d="M46 54 q24 -20 48 0" {DCS}/>'
             f'<path d="M58 52 l0 -14 M70 50 l0 -16 M82 52 l0 -14" {DCS_T}/>'
             f'<circle cx="64" cy="42" r="1.8" fill="#141416"/><circle cx="76" cy="42" r="1.8" fill="#141416"/>')
    return f'<svg viewBox="0 0 140 140" xmlns="http://www.w3.org/2000/svg">{inner}</svg>'


def _hd_rootangle(seed) -> str:
    # 볼륨=모근 각도 — 정수리 뿌리가 '각도로 서있다'
    inner = (f'<circle cx="70" cy="80" r="30" {DCS}/>{_dface(70,80)}'
             f'<path d="M56 51 l8 -18 M70 49 l6 -19 M84 51 l10 -17" {DCS}/>'
             f'<path d="M64 33 q6 -3 12 0" {DCS_T}/>'
             f'<path d="M64 33 a10 10 0 0 1 12 0" {DCS_T}/>')
    return f'<svg viewBox="0 0 140 140" xmlns="http://www.w3.org/2000/svg">{inner}</svg>'


def _hd_layers(seed) -> str:
    # 레이어드=움직임 — 층진 머리 + 흐름선
    inner = (f'<circle cx="66" cy="80" r="29" {DCS}/>{_dface(66,80)}'
             f'<path d="M40 70 q6 -30 26 -30 q20 0 26 26" {DCS}/>'
             f'<path d="M42 82 q10 12 24 8" {DCS_T}/><path d="M46 96 q10 10 22 6" {DCS_T}/>'
             f'<path d="M100 70 q16 4 22 -4 M100 84 q16 6 22 0" {DCS_T}/>')
    return f'<svg viewBox="0 0 140 140" xmlns="http://www.w3.org/2000/svg">{inner}</svg>'


def _hd_bob(seed) -> str:
    # 단발=길이 밸런스 — 가지런한 단발 + 튀어나온 곳 '조각'(가위질)
    inner = (f'<path d="M42 56 q28 -22 56 0" {DCS}/>'
             f'<line x1="42" y1="56" x2="40" y2="104" {DCS}/><line x1="98" y1="56" x2="100" y2="104" {DCS}/>'
             f'<path d="M40 104 q30 8 60 0" {DCS}/>{_dface(70,80)}'
             # 튀어나온 한 올 + 조각(가위)
             f'<path d="M100 92 q16 -2 22 -12" {DCS_T}/>'
             f'<circle cx="124" cy="72" r="5" {DCS_T}/><circle cx="124" cy="86" r="5" {DCS_T}/>'
             f'<path d="M120 76 l-14 6 M120 82 l-14 -6" {DCS_T}/>')
    return f'<svg viewBox="0 0 140 140" xmlns="http://www.w3.org/2000/svg">{inner}</svg>'


def _d_soak(seed) -> str:
    # 디자이너의 색=스며듦 — 잉크 한 방울이 '번져 배어든다'(헤어컬러 아님)
    inner = (f'<path d="M70 22 q14 20 14 30 a14 14 0 1 1 -28 0 q0 -10 14 -30 z" {DCS}/>'
             f'<path d="M44 78 a26 9 0 0 0 52 0" {DCS_T}/>'
             f'<path d="M34 94 a36 12 0 0 0 72 0" {DCS_T}/>'
             f'<path d="M26 110 a44 14 0 0 0 88 0" {DCS_T}/>'
             f'<circle cx="70" cy="52" r="2.6" fill="#141416"/>')
    return f'<svg viewBox="0 0 140 140" xmlns="http://www.w3.org/2000/svg">{inner}</svg>'


def _hd_moods(seed) -> str:
    # 어울림=무드 밸런스 — 직선(차갑게) vs 곡선(부드럽게)
    inner = (f'<rect x="20" y="46" width="42" height="56" rx="4" {DCS}/>'
             f'<circle cx="34" cy="70" r="2.6" fill="#141416"/><circle cx="48" cy="70" r="2.6" fill="#141416"/>'
             f'<path d="M34 84 l14 0" {DCS_T}/>'
             f'<circle cx="100" cy="74" r="28" {DCS}/>'
             f'<circle cx="92" cy="70" r="2.6" fill="#141416"/><circle cx="108" cy="70" r="2.6" fill="#141416"/>'
             f'<path d="M92 82 q8 6 16 0" {DCS_T}/>')
    return f'<svg viewBox="0 0 140 140" xmlns="http://www.w3.org/2000/svg">{inner}</svg>'


DOODLES = {"scissors": _d_scissors, "angle": _d_angle, "wave": _d_wave,
           "triface": _d_triface, "drop": _d_drop, "moods": _d_moods,
           "steps": _d_steps, "dir": _d_dir, "think": _d_think,
           "hd_space": _hd_space, "hd_rootangle": _hd_rootangle, "hd_layers": _hd_layers,
           "hd_bob": _hd_bob, "soak": _d_soak, "hd_moods": _hd_moods}


def _arrow(seed) -> str:
    inner = f'<path d="M8 20 q34 18 74 -6 M74 14 l10 0 l-4 12" {STK_T}/>'
    return f'<svg viewBox="0 0 96 48" xmlns="http://www.w3.org/2000/svg">{_rough(inner, seed, 3)}</svg>'


@dataclass
class ZineBlock:
    old: str      # 통념(취소선)
    new: str      # 재정의(강조)
    sub: str      # 짧은 부연
    doodle: str   # DOODLES 키
    x: int        # left(px)
    y: int        # top(px)
    w: int        # width(px)
    rot: float    # 기울기(deg)


@dataclass
class ZineSpec:
    title: str
    blocks: list = field(default_factory=list)
    arrows: list = field(default_factory=list)   # (x,y,rot) 흩뿌릴 화살표
    banner: str = ""
    closer_sub: str = ""
    tag: str = "@차노쌤"


def _zblock_html(b: ZineBlock, i: int) -> str:
    dood = DOODLES[b.doodle](seed=i + 3)
    return f'''<div class="zblock" style="left:{b.x}px;top:{b.y}px;width:{b.w}px;transform:rotate({b.rot}deg)">
  <div class="ztext">
    <div class="zold">{b.old}</div>
    <div class="znew">{b.new}</div>
    <div class="zsub">{b.sub}</div>
  </div>
  <div class="zdood">{dood}</div>
</div>'''


def build_zine(spec: ZineSpec) -> str:
    faces = _font_face("KyoboPoster", FONT_HAND) + _font_face("NanumPenPoster", FONT_PEN)
    blocks = "".join(_zblock_html(b, i) for i, b in enumerate(spec.blocks))
    arrows = "".join(
        f'<div class="zarrow" style="left:{x}px;top:{y}px;transform:rotate({r}deg)">{_arrow(90 + i)}</div>'
        for i, (x, y, r) in enumerate(spec.arrows))
    banner = f'<div class="zbanner">{spec.banner}</div>' if spec.banner else ""
    closer = f'<div class="zcloser">{spec.closer_sub}</div>' if spec.closer_sub else ""
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
{faces}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px}}
body{{background:#faf8f2;color:#141416;position:relative;overflow:hidden}}
/* 종이 결 느낌 */
body::before{{content:"";position:absolute;inset:0;opacity:.05;
  background:repeating-linear-gradient(0deg,#000 0 1px,transparent 1px 6px)}}
.title{{position:absolute;left:0;right:0;top:44px;text-align:center;
  font-family:KyoboPoster;font-size:96px;transform:rotate(-1.5deg);z-index:5}}
.tunder{{position:absolute;top:172px;left:50%;width:560px;height:12px;margin-left:-280px;
  border-bottom:7px solid #141416;border-radius:60%;transform:rotate(-1deg);opacity:.85}}
.tag{{position:absolute;top:60px;right:70px;font-family:NanumPenPoster;font-size:34px;
  transform:rotate(4deg);border:3px solid #141416;border-radius:40% 50% 45% 55%;padding:2px 16px}}
.zblock{{position:absolute;min-height:184px;border:4px solid #141416;border-radius:20px 26px 16px 24px;
  background:#fffef8;padding:16px 22px 18px;box-shadow:5px 6px 0 rgba(20,20,22,.13);
  display:flex;align-items:center}}
.ztext{{flex:1;min-width:0;padding-right:112px}}
.zold{{font-family:NanumPenPoster;font-size:31px;color:#8f8c82;text-decoration:line-through;
  text-decoration-thickness:2px}}
.znew{{font-family:KyoboPoster;font-size:41px;line-height:1.02;margin-top:2px;white-space:nowrap}}
.zsub{{font-family:NanumPenPoster;font-size:29px;color:#2a2b30;margin-top:8px;white-space:nowrap}}
.zdood{{position:absolute;right:16px;top:50%;transform:translateY(-50%);width:100px;height:100px}}
.zdood svg{{width:100px;height:100px}}
.zarrow{{position:absolute;width:96px;height:48px;opacity:.9}}
.zarrow svg{{width:96px;height:48px}}
.zbanner{{position:absolute;left:60px;bottom:118px;font-family:KyoboPoster;font-size:44px;
  color:#faf8f2;background:#141416;padding:10px 24px 14px;border-radius:10px;
  transform:rotate(-2deg);line-height:1.12}}
.zcloser{{position:absolute;left:0;right:0;bottom:56px;text-align:center;
  font-family:NanumPenPoster;font-size:36px;color:#22242a}}
</style></head><body>
<div class="title">{spec.title}</div>
<div class="tunder"></div>
<div class="tag">{spec.tag}</div>
{arrows}{blocks}
{banner}{closer}
<script>
// znew(재정의) 가 블록 폭을 넘으면 폰트 축소 — 변칙 폭에도 안 잘림.
function _fitZ(){{
  document.querySelectorAll('.zblock').forEach(function(bl){{
    var tx=bl.querySelector('.ztext'); var t=bl.querySelector('.znew'); if(!tx||!t) return;
    var avail=tx.clientWidth - 112;   // 도형칸(패딩) 확보
    var fs=41; t.style.fontSize=fs+'px';
    while(t.scrollWidth>avail && fs>22){{ fs-=1; t.style.fontSize=fs+'px'; }}
  }});
}}
if(document.fonts && document.fonts.ready){{ document.fonts.ready.then(function(){{ _fitZ(); setTimeout(_fitZ,50); }}); }}
else {{ _fitZ(); }}
</script>
</body></html>'''


def render_zine(spec: ZineSpec, out_png: str) -> str:
    """만화/변칙배열 카드."""
    return _shoot(build_zine(spec), out_png)


# ── 형님 주제 총서(재정의 믹스) — 단발·레이어드·볼륨·숱치기·색·무드 한 장 ──
def mix_spec() -> ZineSpec:
    return ZineSpec(
        title="미용실 상식 뒤집기",
        blocks=[
            # 벽돌 엇갈림(왼 232/524/812 · 오 330/622/905) + 폭·기울기 변칙
            ZineBlock("숱치기 = 양 덜기", "숱치기 = 공간 만들기",
                      "숨 쉴 자리를 준다", "hd_space", 40, 232, 356, -3.5),
            ZineBlock("볼륨 = 숱", "볼륨 = 모근의 각도",
                      "모근이 서서 산다", "hd_rootangle", 676, 330, 344, 3),
            ZineBlock("레이어드 = 층", "레이어드 = 움직임",
                      "결에 움직임을 넣기", "hd_layers", 96, 524, 340, 4.5),
            ZineBlock("단발 = 길이 자르기", "단발 = 길이 밸런스",
                      "튀어나온 곳을 조각해요", "hd_bob", 648, 622, 372, -5),
            # 색=스며듦 제외(이찬호: 커트 흐름에 쌩뚱맞음) → '디자이너 정체성' 카드로 별도. 재정의는 대장 보존.
            ZineBlock("어울림 = 얼굴형", "어울림 = 무드 밸런스",
                      "무드가 안 맞을 뿐", "hd_moods", 40, 820, 392, -2.5),
        ],
        arrows=[(410, 372, 20), (438, 636, 24)],
        banner="머리는 자르는 게 아니라, '그리는' 거예요",
        closer_sub="투박하게 그려도 그 사람에게 잘 어울리면, 좋은 그림이에요.",
    )


# ═══════════════ 디자인 맵(7 슬라이더) — 만화·손그림 버전 ═══════════════
# 이찬호 2026-07-22: 앳나운 워크시트 1/4 '디자인 맵'을 만화 톤으로.
# 7개 헤어 언어(쉐입·질감·컬·볼륨·채도·색온도·투명도)를 손그림 슬라이더로.

@dataclass
class SliderRow:
    ko: str        # 쉐입
    en: str        # SHAPE
    left: str      # 왼쪽 극(안정)
    right: str     # 오른쪽 극(역동)
    pos: float     # 0(왼)~1(오) 마커 위치


@dataclass
class DesignMapSpec:
    tag: str               # 우상단 "DESIGN MAP · 1/4"
    title1: str            # 쿨 시크 단발
    title2: str            # 이 디자인의 맵
    subtitle: str
    body: str
    rows: list = field(default_factory=list)
    footer: str = ""
    brand: str = "AT NOWN 앳나운"


def _slider_svg(pos: float, seed: int) -> str:
    x = 14 + pos * 372            # 트랙 14..386
    ticks = "".join(f'<circle cx="{14 + i*93}" cy="34" r="3.2" fill="#c9c3b6"/>' for i in range(5))
    inner = (f'<path d="M14 34 q93 -7 186 0 q93 7 186 0" {STK_T}/>{ticks}'
             f'<circle cx="{x:.0f}" cy="34" r="15" fill="none" stroke="#141416" stroke-width="3"/>'
             f'<circle cx="{x:.0f}" cy="34" r="8" fill="#141416"/>')
    return (f'<svg viewBox="0 0 400 68" xmlns="http://www.w3.org/2000/svg" '
            f'preserveAspectRatio="none">{_rough(inner, seed, 3)}</svg>')


def _srow_html(r: SliderRow, i: int) -> str:
    return f'''<div class="srow">
  <div class="slabel"><span class="sko">{r.ko}</span><span class="sen">{r.en}</span></div>
  <div class="spoleL">{r.left}</div>
  <div class="strack">{_slider_svg(r.pos, 30 + i)}</div>
  <div class="spoleR">{r.right}</div>
</div>'''


def build_designmap(spec: DesignMapSpec) -> str:
    faces = _font_face("KyoboPoster", FONT_HAND) + _font_face("NanumPenPoster", FONT_PEN)
    rows = "".join(_srow_html(r, i) for i, r in enumerate(spec.rows))
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
{faces}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px}}
body{{background:#faf7f0;color:#141416;position:relative;overflow:hidden;padding:60px 66px 44px}}
body::before{{content:"";position:absolute;inset:0;opacity:.045;
  background:repeating-linear-gradient(0deg,#000 0 1px,transparent 1px 7px)}}
.top{{display:flex;justify-content:space-between;align-items:baseline;
  border-bottom:4px solid #141416;padding-bottom:12px}}
.brand{{font-family:KyoboPoster;font-size:40px;letter-spacing:1px}}
.tag{{font-family:NanumPenPoster;font-size:30px;color:#6b6459}}
.title{{font-family:KyoboPoster;font-size:74px;line-height:1.03;margin-top:20px}}
.subtitle{{font-family:NanumPenPoster;font-size:33px;color:#4a4438;margin-top:10px}}
.body{{font-family:NanumPenPoster;font-size:30px;color:#33302a;line-height:1.3;margin-top:8px;
  max-width:900px}}
.card{{border:4px solid #141416;border-radius:24px 30px 22px 28px;background:#fffdf6;
  box-shadow:6px 7px 0 rgba(20,20,22,.12);margin-top:16px;padding:12px 30px 4px}}
.srow{{display:flex;align-items:center;gap:10px;height:96px;
  border-bottom:2px dashed #ddd6c7}}
.srow:last-child{{border-bottom:none}}
.slabel{{width:132px;flex:none;display:flex;flex-direction:column}}
.sko{{font-family:KyoboPoster;font-size:38px;line-height:1}}
.sen{{font-family:NanumPenPoster;font-size:22px;color:#8a8375;letter-spacing:1px}}
.spoleL,.spoleR{{width:104px;flex:none;font-family:NanumPenPoster;font-size:26px;color:#33302a}}
.spoleL{{text-align:right}}.spoleR{{text-align:left}}
.strack{{flex:1;height:68px}}
.strack svg{{width:100%;height:68px}}
.footer{{text-align:center;font-family:NanumPenPoster;font-size:30px;color:#4a4438;margin-top:14px}}
.footer b{{background:#141416;color:#faf7f0;padding:1px 10px 4px;border-radius:6px}}
</style></head><body>
<div class="top"><span class="brand">{spec.brand}</span><span class="tag">{spec.tag}</span></div>
<div class="title">{spec.title1}<br>{spec.title2}</div>
<div class="subtitle">{spec.subtitle}</div>
<div class="body">{spec.body}</div>
<div class="card">{rows}</div>
<div class="footer">{spec.footer}</div>
</body></html>'''


def render_designmap(spec: DesignMapSpec, out_png: str) -> str:
    return _shoot(build_designmap(spec), out_png)


def coolchic_designmap() -> DesignMapSpec:
    return DesignMapSpec(
        tag="DESIGN MAP · 1/4",
        title1="쿨 시크 단발",
        title2="이 디자인의 맵",
        subtitle="이 디자인을 일곱 가지 헤어 언어로 도식화했어요.",
        body="무게감을 살짝 낮춰 차분하고 단정하게. 30대에 잘 어울리는 단발이에요. "
             "오늘은 염색 없이 오일만으로 윤기 있고 깊이감 있게 마무리했어요.",
        rows=[
            SliderRow("쉐입", "SHAPE", "안정", "역동", 0.30),
            SliderRow("질감", "TEXTURE", "부드러움", "경쾌함", 0.28),
            SliderRow("컬", "CURL", "스트레이트", "웨이브", 0.24),
            SliderRow("볼륨", "VOLUME", "슬릭", "풍성", 0.20),
            SliderRow("채도", "SATURATION", "차분", "선명", 0.60),
            SliderRow("색온도", "TEMP", "웜", "쿨", 0.46),
            SliderRow("투명도", "TONE", "딥", "투명", 0.18),
        ],
        footer="기준은 출발점일 뿐이에요. 눈앞의 머릿결을 보고 — <b>직관</b>으로 디자인합니다.",
    )


def longface_spec() -> PosterSpec:
    # 인스타 11p '긴 얼굴형 단발 공식' — 실제 5가지 방법(4·6·7·8·9p)으로 구성 + 정리
    return PosterSpec(
        title='<span class="wu">긴 얼굴형</span> 단발 공식',
        panels=[
            Panel("1", "길이 — 어디서 자르나",
                  "턱보다 위에서 끝나면\n얼굴이 넓어 보이고,\n아래로 길면\n더 길어 보여요.", "lf_jaw"),
            Panel("2", "무게 — 아래로 내리기",
                  "'코끝선'(코끝~뒤통수)\n그 아래로 머리 무게를\n내리면\n얼굴이 짧아 보여요.", "lf_weight"),
            Panel("3", "컬 — 옆에 넣기",
                  "펌으로 옆머리에\n구불구불 컬을 주면\n옆이 통통해져\n얼굴이 짧아 보여요.", "lf_expand"),
            Panel("4", "모양 — 머리 조각하기",
                  "튀어나온 곳은 덜고\n모양을 동그랗게\n다듬어요.", "lf_trim"),
            Panel("5", "말리기 — 뿌리 세워서",
                  "머리 뿌리를 비벼 세우고\n비스듬히 앞으로\n말리면\n옆 볼륨이 살아요.", "lf_dry"),
            Panel("6", "가로선이 시선을 끊어요",
                  "세로로 긴 선을\n코끝 아래 가로선이\n끊어줘요.\n너무 위서 끊으면\n아래 세로가 또 생겨요.", "lf_cut"),
        ],
        banner="긴 얼굴 = 옆으로 퍼뜨리면 짧아 보여요",
        closer_hand="단발은 길이가 아니라 <b>인상</b>을 그리는 일.",
        closer_sub="저장했다가, 상담 때 보여주세요.",
    )


def mix2_spec() -> ZineSpec:
    # 미용실 상식 뒤집기 ② — 관리·재현 편(형님 실제 재정의만)
    return ZineSpec(
        title="머리 관리 상식 뒤집기",
        blocks=[
            ZineBlock("펌 = 약 세기", "펌 = 순서",
                      "약이 아니라\n순서에 타요.", "steps", 40, 232, 356, -3.5),
            ZineBlock("앞머리 = 길이", "앞머리 = 각도",
                      "5cm도 각도로\n인상이 달라져요.", "angle", 676, 330, 344, 3),
            ZineBlock("두피 = 감는 법", "두피 = 말리는 법",
                      "고민 절반은\n말리기예요.", "drop", 96, 524, 340, 4.5),
            ZineBlock("재현 = 미용실 손", "재현 = 방향",
                      "집에선 방향이\n답이에요.", "dir", 648, 622, 360, -5),
            ZineBlock("유행컷 = 따라하기", "유행컷 = 내 결",
                      "내 결에\n얹는 거예요.", "wave", 34, 812, 344, -2.5),
            ZineBlock("커트 = 기술", "커트 = 생각",
                      "같은 가위질도\n생각으로 갈려요.", "think", 660, 905, 352, 3.5),
        ],
        arrows=[(410, 372, 20), (438, 636, 24), (404, 920, 16)],
        banner="잘 자른 머리도, 집에서 못 살리면 반이에요",
        closer_sub="당신의 머리 — 미용실 날만 예쁜가요, 매일 예쁜가요?",
    )


# ═══════════════ 상세 캐러셀(장마다 항목 1개 깊게) — 이찬호 2026-07-22 ═══════════════
# "미용실 상식 뒤집기 + 긴 얼굴형은 6장으로, 장마다 1~6을 구체화(한번 더 설명)."
@dataclass
class DetailCard:
    myth: str          # 통념(작게·취소선)
    redef: str         # 재정의(크게)
    essence: str       # 한 줄
    doodle: str        # DOODLES/SCENES 키
    explain: str       # 한 번 더 설명(\n 줄바꿈, 2~4줄)


@dataclass
class DetailSpec:
    series: str        # 시리즈명(상단)
    foot: str          # 하단 고정 문구
    cards: list = field(default_factory=list)
    cover: object = None   # 1번(표지)=원본 요약 카드(ZineSpec). 부가설명은 2번부터.


def _doodle_svg(key: str) -> str:
    fn = DOODLES.get(key) or SCENES.get(key)
    return fn(7) if fn in DOODLES.values() else (fn() if key in SCENES else "")


def build_detail(spec: DetailSpec, card: DetailCard, idx: int, total: int) -> str:
    faces = _font_face("KyoboPoster", FONT_HAND) + _font_face("NanumPenPoster", FONT_PEN)
    svg = DOODLES[card.doodle](7) if card.doodle in DOODLES else SCENES[card.doodle]()
    explain = card.explain.replace("\n", "<br>")
    redef = card.redef.replace("\n", "<br>")   # 의도한 줄바꿈만 — '요'만 흘러내리는 것 방지
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
{faces}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px}}
body{{background:#fbfbf9;color:#141416;position:relative;overflow:hidden}}
.dwrap{{padding:70px 78px 56px;height:100%;display:flex;flex-direction:column}}
.dtop{{display:flex;justify-content:space-between;align-items:center;
  font-family:KyoboPoster;font-size:40px;color:#141416}}
.dtop .series{{opacity:.9}}
.dtop .pg{{font-size:34px;opacity:.55}}
.dhandle{{position:absolute;top:70px;right:78px}}
.dmyth{{font-family:NanumPenPoster;font-size:46px;color:#9a9a9a;margin-top:64px;
  text-decoration:line-through;text-decoration-thickness:3px}}
.dredef{{font-family:KyoboPoster;font-size:112px;line-height:1.04;margin-top:10px;letter-spacing:1px}}
.dess{{font-family:NanumPenPoster;font-size:52px;color:#22242a;margin-top:20px}}
.dbody{{flex:1;display:flex;align-items:center;justify-content:center;margin:6px 0}}
.dbody svg{{width:400px;height:400px}}
.dexp{{border:3px solid #141416;border-radius:22px;padding:30px 34px;position:relative;margin-top:6px}}
.dexp .tag{{position:absolute;top:-26px;left:28px;background:#141416;color:#fbfbf9;
  font-family:KyoboPoster;font-size:34px;padding:2px 18px 6px;border-radius:8px}}
.dexp .txt{{font-family:NanumPenPoster;font-size:46px;line-height:1.34;color:#141416}}
.dfoot{{text-align:center;font-family:NanumPenPoster;font-size:34px;color:#6b6b6b;margin-top:22px}}
</style></head><body>
<div class="dwrap">
  <div class="dtop"><span class="series">{spec.series}</span><span class="pg">{idx} / {total}</span></div>
  <div class="dmyth">✗ {card.myth}</div>
  <div class="dredef">{redef}</div>
  <div class="dess">{card.essence}</div>
  <div class="dbody">{svg}</div>
  <div class="dexp"><span class="tag">한 번 더</span><div class="txt">{explain}</div></div>
  <div class="dfoot">{spec.foot}</div>
</div>
<script>
// 재정의가 한 줄 폭을 넘으면 자동 축소
(function(){{ var el=document.querySelector('.dredef'); var fs=112;
  while(el.scrollWidth>{W}-156 && fs>60){{ fs-=2; el.style.fontSize=fs+'px'; }} }})();
</script>
</body></html>'''


def render_detail_series(spec: DetailSpec, out_prefix: str) -> list:
    """1번=원본 요약 만화카드(그 시작을 잃지 않음) + 2번부터 부가설명."""
    outs = []
    total = len(spec.cards) + (1 if spec.cover else 0)
    start = 1
    if spec.cover:
        out = f"{out_prefix}_1.png"
        cover_html = build_zine(spec.cover) if isinstance(spec.cover, ZineSpec) else build_html(spec.cover)
        _shoot(cover_html, out)   # 처음 그 카드 그대로(구조 안 바꿈)
        outs.append(out)
        start = 2
    for off, c in enumerate(spec.cards):
        i = start + off
        out = f"{out_prefix}_{i}.png"
        _shoot(build_detail(spec, c, i, total), out)
        outs.append(out)
    return outs


def mix_detail_spec() -> DetailSpec:
    return DetailSpec(
        series="미용실 상식 뒤집기",
        foot="@차노쌤 · 머리는 자르는 게 아니라 '그리는' 거예요",
        cover=mix_spec(),   # 1번=처음 그 6칸 만화카드(서사) 그대로
        cards=[
            DetailCard("숱치기 = 양 덜기", "숱치기는\n공간이에요", "숨 쉴 자리를 준다", "hd_space",
                       "숱을 친다는 건 양을 더는 게 아니에요.\n머리카락 사이에 숨 쉴 자리를 만드는 일.\n공간이 생겨야 결이 살고,\n무겁던 머리가 가벼워 보여요."),
            DetailCard("볼륨 = 숱", "볼륨은\n모근 각도예요", "모근이 서야 산다", "hd_rootangle",
                       "볼륨은 숱이 많아서 생기는 게 아니에요.\n모근이 서 있느냐 누웠느냐,\n그 각도가 볼륨을 정해요.\n말릴 때 뿌리를 세우면 살아나죠."),
            DetailCard("레이어드 = 층", "레이어드는\n움직임이에요", "결에 움직임을 넣는다", "hd_layers",
                       "레이어드는 층을 내는 기술이 아니에요.\n결에 움직임을 넣는 일이에요.\n층이 목적이 아니라,\n흔들릴 때 자연스러운 그 느낌이 목적이죠."),
            DetailCard("단발 = 길이 자르기", "단발은\n밸런스예요", "튀어나온 곳을 조각한다", "hd_bob",
                       "단발은 길이를 자르는 게 아니에요.\n튀어나온 곳을 조각해\n전체 밸런스를 맞추는 일.\n같은 길이도 밸런스가 다르면 인상이 달라져요."),
            # 색=스며듦: 커트 흐름에 쌩뚱맞아 제외(이찬호 2026-07-22). 재정의는 대장에 보존→'디자이너 정체성' 카드로 별도.
            DetailCard("어울림 = 얼굴형", "어울림은\n무드예요", "무드가 안 맞을 뿐", "hd_moods",
                       "안 어울리는 얼굴형은 없어요.\n얼굴형이 문제가 아니라\n무드가 안 맞았을 뿐이에요.\n무드만 맞추면 누구나 소화해요."),
        ],
    )


def longface_detail_spec() -> DetailSpec:
    return DetailSpec(
        series="긴 얼굴형 단발 공식",
        foot="@차노쌤 · 단발은 길이가 아니라 인상을 그리는 일",
        cover=longface_spec(),   # 1번=처음 그 긴얼굴 카드(공식 6칸) 그대로
        cards=[
            DetailCard("단발 = 짧게 자르기", "길이는\n어디서 끊나요", "기준은 턱 언저리", "lf_jaw",
                       "어디서 자르느냐가 반이에요.\n턱보다 위에서 끝나면 얼굴이 넓어 보이고,\n아래로 길게 두면 더 길어 보여요.\n긴 얼굴은 '턱 언저리'가 기준이에요."),
            DetailCard("무게 = 숱 많이", "무게는\n아래로 내려요", "코끝 15° 사선 아래로", "lf_weight",
                       "코끝에서 사선으로 15도 내린 선을 그어요.\n그 선 아래로 머리 무게(웨이트)를 잡으면\n시선이 아래로 모여\n얼굴이 짧아 보여요."),
            DetailCard("긴 얼굴 = 층 많이", "컬은\n옆에 넣어요", "옆이 통통해져요", "lf_expand",
                       "펌으로 옆머리에 구불구불 컬을 주면\n납작하던 옆이 통통해져요.\n옆으로 퍼지면\n긴 세로가 짧아 보여요."),
            DetailCard("다듬기 = 끝만 정리", "모양은\n조각이에요", "동그랗게 다듬기", "lf_trim",
                       "튀어나온 곳은 덜어내고\n전체를 동그란 모양으로 다듬어요.\n각지면 더 길어 보이고,\n둥글면 부드럽고 짧아 보여요."),
            DetailCard("볼륨 = 미용실에서만", "말리기는\n뿌리부터예요", "뿌리 세워 앞으로", "lf_dry",
                       "머리 뿌리를 비벼 세우고\n비스듬히 앞으로 말려요.\n집에서 이 방향만 지켜도\n옆 볼륨이 살아나요."),
            DetailCard("짧게만 = 정답", "밸런스는\n가로선이에요", "코끝 아래서 끊기", "lf_cut",
                       "세로로 긴 선을\n코끝 아래 가로선이 끊어줘요.\n너무 위에서 끊으면 아래 세로가 또 생겨요.\n끊는 위치가 밸런스예요."),
        ],
    )


def mix2_detail_spec() -> DetailSpec:
    # 관리편 부가설명 — 전부 차노 실제 대본 출처(막 만든 것 아님)
    return DetailSpec(
        series="머리 관리 상식 뒤집기",
        foot="@차노쌤 · 잘 자른 머리도 집에서 못 살리면 반이에요",
        cover=mix2_spec(),   # 1번=처음 그 관리편 6칸 카드 그대로
        cards=[
            DetailCard("펌 = 약 세기", "펌은\n순서예요", "약이 아니라 순서에 타요", "steps",
                       "펌이 상하는 건 약이 세서가 아니에요.\n약을 올리고 푸는 '순서'에 타요.\n같은 약도 순서가 맞으면\n덜 상하고 결이 살아요."),
            DetailCard("앞머리 = 길이", "앞머리는\n각도예요", "5cm도 각도로 갈려요", "angle",
                       "앞머리는 길이 문제가 아니에요.\n5cm를 어느 각도로 두느냐로\n인상이 확 달라져요.\n길이보다 각도를 먼저 봐요."),
            DetailCard("두피 = 감는 법", "두피는\n말리는 법이에요", "고민 절반은 말리기", "drop",
                       "두피 고민의 절반은 감는 게 아니라\n'말리는 법'에서 갈려요.\n뿌리를 세워 말리면\n볼륨도 두피도 편해져요."),
            DetailCard("재현 = 미용실 손", "재현은\n방향이에요", "집에선 방향이 답", "dir",
                       "미용실 날만 예쁜 건 손이 아니라\n'방향'을 몰라서예요.\n드라이 방향만 맞추면\n집에서도 그 모양이 나와요."),
            DetailCard("유행컷 = 따라하기", "유행컷은\n내 결이에요", "내 결에 얹는 것", "wave",
                       "유행컷은 그대로 따라하는 게 아니에요.\n내 결 위에 얹는 거예요.\n웬디컷·허쉬컷도\n내 결에 맞아야 어울려요."),
            DetailCard("커트 = 기술", "커트는\n생각이에요", "생각으로 갈려요", "think",
                       "같은 가위질도 생각이 달라요.\n어디를 왜 덜지 먼저 그리고 잘라요.\n기술이 아니라 생각이\n결과를 가릅니다."),
        ],
    )


SPECS = {"demo": demo_spec, "danbal": danbal_spec, "longface": longface_spec}
ZINE_SPECS = {"mix": mix_spec, "mix2": mix2_spec}
MAP_SPECS = {"coolchic": coolchic_designmap}
DETAIL_SPECS = {"mixdetail": mix_detail_spec, "longfacedetail": longface_detail_spec,
                "mix2detail": mix2_detail_spec}

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/cardposter.png"
    which = "demo"
    if "--spec" in sys.argv:
        which = sys.argv[sys.argv.index("--spec") + 1]
    if which in DETAIL_SPECS:
        prefix = out[:-4] if out.endswith(".png") else out
        outs = render_detail_series(DETAIL_SPECS[which](), prefix)
        print("OK →", *outs, sep="\n")
    elif which in MAP_SPECS:
        render_designmap(MAP_SPECS[which](), out)
    elif which in ZINE_SPECS:
        render_zine(ZINE_SPECS[which](), out)
    else:
        render_poster(SPECS[which](), out)
        print("OK →", out)
