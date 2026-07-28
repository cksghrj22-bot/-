"""쇼츠 자막·BGM 정본 스타일 — 영구 박제(커밋됨). 세션마다 재구현 금지.

배경(2026-07-27 이찬호): 정본 값이 제작규격_정본.md(문서)에만 있고 코드에 없어서,
새 세션마다 STYLE을 손으로 다시 짜다 버그 재발(폰트 폴백·EN 멀어짐·BGM 무음).
→ 여기 한 곳에 고정. 렌더 스크립트는 반드시 이 모듈을 import 해서 쓴다.

정확값은 `pipeline/완성_체크표.md`와 1:1.
"""
from __future__ import annotations
import subprocess
from pathlib import Path


def kyobo_family() -> str:
    """이 환경의 교보손글씨 실제 패밀리명을 반환(폴백 버그 방지).

    문서엔 'Kyobo Handwriting 2019'(맥 이름)로 적혀 있으나 리눅스 설치본은
    'KyoboHandwriting2019'(공백 없음). libass는 정확 매칭이라 공백 버전이면 폴백된다.
    설치 폰트에서 실제 패밀리명을 읽어 그대로 쓴다.
    """
    for p in ("/root/.fonts/KyoboHandwriting2019.ttf",
              "/home/user/-/assets/fonts/KyoboHandwriting2019.ttf"):
        if Path(p).exists():
            try:
                out = subprocess.run(["fc-scan", "--format", "%{family}", p],
                                     capture_output=True, text=True).stdout.strip()
                if out:
                    return out.split(",")[0]
            except Exception:
                pass
    return "KyoboHandwriting2019"


KYOBO = kyobo_family()

# 한글 자막(하단·검정박스·70) — 정본. EN은 같은 블록 아래줄(54)로 합쳐 '멀어짐/충돌' 원천차단.
# (한글\N{\fs54}영어 = 한 Dialogue → libass 충돌 재정렬 없음, 간격 바짝.)
SUB = {
    "font": KYOBO, "size": 70,
    "primary_color": "&H00FFFFFF", "outline_color": "&H00000000",
    "box_color": "000000", "box_opacity": 100, "border_style": 4,
    "outline": 2, "alignment": 2, "margin_v": 410,   # 블록 하단 y≈1510 = 채널명 UI(하단 380) 위
}
EN_INLINE = r"{\fs54\c&HF0F0F0&}"   # 한글 아래 붙는 영어 인라인 태그(바짝)
EMPHASIS_INLINE = r"{\fs104}"        # 강조 1회 글자확대

# 검은화면 질문 카드(중간 굵은 질문·시작 훅) — 교보 중앙 대형.
QCARD = {
    "font": KYOBO, "size": 92,
    "primary_color": "&H00FFFFFF", "outline_color": "&H00000000",
    "box_color": "000000", "box_opacity": 0, "border_style": 1,
    "outline": 0, "alignment": 5, "margin_v": 40,
}

# BGM: loudnorm(-34) 뒤 volume. 0.15면 ≈-50dB(무음 버그). 0.32 = 꼬리 ≈-33dB(들림·나레 아래).
BGM_VOLUME = 1.0   # loudnorm(-34 LUFS)이 이미 레벨 결정 → 추가 감쇠 금지(0.15는 이중감쇠 무음 버그)

# 채널명/브랜딩: 영상에 채널명 안 넣음(유튜브가 표시). SNS 아웃트로는 제작규격 유지(채널명 아님).
CHANNEL_WATERMARK = False

# 아웃트로 "SNS에 일기를 쓰고 있어요" — 정본=정가운데 카드+검은박스(런북·verify_render "아웃트로중앙").
# 하단 작은 반투명(46/alpha80)은 옛버전 = 틀림. 중앙·박스·또렷·페이드.
OUTRO_CARD = {
    "font": KYOBO, "size": 64,
    "primary_color": "&H00FFFFFF", "outline_color": "&H00000000",
    "box_color": "000000", "box_opacity": 100, "border_style": 4,
    "outline": 2, "alignment": 5, "margin_v": 40,
    "alpha": "00", "fade": [500, 400], "dur": 2.6,
}


def ko_en(ko: str, en: str | None) -> str:
    """한글+영어를 한 블록으로. 영어는 바로 아래 작은 글씨(멀어짐 방지)."""
    if not en:
        return ko
    return f"{ko}\\N{EN_INLINE}{en}"


# ─────────────────────────────────────────────────────────────────────────────
# 🎬 POP 스타일 — 예능/유튜브 훅 자막(두꺼운 볼드고딕 + 굵은 검은테두리 + 2톤 노랑/흰)
# (2026-07-28 이찬호 "이런 글씨체 이런 느낌도 하나 넣어놔" — IMG_2125 레퍼런스)
# 교보손글씨(감성)와 별개의 '강한 정보전달' 옵션. 골라 쓰는 두 번째 스템.
# ─────────────────────────────────────────────────────────────────────────────
def bold_gothic_family() -> str:
    """이 환경의 두꺼운 고딕 실제 패밀리명(레퍼런스=두꺼운 볼드고딕). 폴백 방지."""
    for p in ("/root/.fonts/nsqr_eb.ttf",
              "/home/user/-/assets/fonts/nsqr_eb.ttf"):
        if Path(p).exists():
            try:
                full = subprocess.run(["fc-scan", "--format", "%{fullname}", p],
                                      capture_output=True, text=True).stdout.strip()
                if full:
                    return full.split(",")[0]   # 'NanumSquareRound ExtraBold'
            except Exception:
                pass
    return "NanumSquareRound ExtraBold"


POP_FONT = bold_gothic_family()

# POP 하단 자막 — 흰 볼드 + 굵은 검은 테두리(박스 없음, 아웃라인만). 레퍼런스 "그래서 저는 늘".
POP_SUB = {
    "font": POP_FONT, "size": 82,
    "primary_color": "&H00FFFFFF", "outline_color": "&H00000000",
    "box_color": "000000", "box_opacity": 0, "border_style": 1,
    "outline": 6, "shadow": 0, "alignment": 2, "margin_v": 430,
}
# POP 영어 = 한글 아래 작은 노랑 이탤릭(레퍼런스 "so I I always wanna live in").
POP_EN_INLINE = r"{\fs46\i1\c&H00D4FF&}"

# POP 제목/훅 2톤 카드 — 노랑 1줄 + 흰 1줄, 초굵은 검은테두리, 상단 밴드. 레퍼런스 "가장 온전한 나로 / 살아가는 방법".
POP_TITLE = {
    "font": POP_FONT, "size": 108,
    "primary_color": "&H00FFFFFF", "outline_color": "&H00000000",
    "box_color": "000000", "box_opacity": 0, "border_style": 1,
    "outline": 9, "shadow": 0, "alignment": 8, "margin_v": 120,
}
POP_YELLOW = r"{\c&H00D4FF&}"   # 노랑(ASS는 BGR: 00 D4 FF = #FFD400)
POP_WHITE = r"{\c&H00FFFFFF&}"


def pop_title(line_yellow: str, line_white: str) -> str:
    """2톤 훅 제목: 윗줄 노랑 + 아랫줄 흰. POP_TITLE 스타일과 함께 쓴다."""
    return f"{POP_YELLOW}{line_yellow}\\N{POP_WHITE}{line_white}"


def pop_ko_en(ko: str, en: str | None) -> str:
    """POP 하단: 흰 볼드 한글 + 아래 작은 노랑 이탤릭 영어."""
    if not en:
        return ko
    return f"{ko}\\N{POP_EN_INLINE}{en}"
