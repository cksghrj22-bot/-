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
    "outline": 2, "alignment": 2, "margin_v": 300,   # 하단, UI존(바닥380) 위
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


def ko_en(ko: str, en: str | None) -> str:
    """한글+영어를 한 블록으로. 영어는 바로 아래 작은 글씨(멀어짐 방지)."""
    if not en:
        return ko
    return f"{ko}\\N{EN_INLINE}{en}"
