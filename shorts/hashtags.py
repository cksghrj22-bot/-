"""줄기별 해시태그 자동첨부 (2026-07-24 이찬호 "영상에 해시태그 붙여서 나가게").

발행 캡션/설명란 끝에 [브랜드 공통 + 줄기 전용 + 영어] 해시태그 블록을 붙인다.
- 정본 줄기(prompts/07 §10, prompts/08): 흑백(마인드)·컬러(감성)·만화카드·교육(커트의정석)·미용(시술)
- 유튜브: 설명 맨 위 3개가 제목 위에 뜸 → 브랜드 3개를 앞에도 노출.
- 인스타/스레드: 캡션 끝 블록.
- 영어 무조건(형 지시): 각 세트에 영문 태그 포함.

사용:
    from shorts.hashtags import caption_with_tags, youtube_tags
    desc = caption_with_tags(본문, "교육")          # 설명/캡션 + 해시태그 블록
    tags = youtube_tags("교육")                      # 유튜브 tags 리스트(최대 30)
    python3 -m shorts.hashtags 교육                   # 미리보기
"""
from __future__ import annotations

# 항상 붙는 브랜드 공통(한글+영문). 맨 앞 3개는 유튜브 제목 위 노출용.
BRAND = ["앳나운", "청담미용실", "청담헤어", "ATNOWN", "cheongdam", "koreahair"]

# 줄기 전용 (한글 + 영문 섞음)
STEMS: dict[str, list[str]] = {
    "교육": ["커트의정석", "헤어교육", "커트강의", "미용교육", "디자이너지원",
             "haircut", "haireducation", "cuttingtechnique"],
    "컬러": ["브이로그", "헤어일기", "감성에세이", "미용실일상",
             "vlog", "hairvlog", "dailylife"],
    "흑백": ["마인드", "동기부여", "일에대하여", "브랜딩",
             "mindset", "creatoros", "workphilosophy"],
    "만화카드": ["카드뉴스", "헤어팁", "미용상식", "hairtips", "cardnews"],
    "미용": ["헤어스타일", "여자헤어", "단발", "레이어드컷", "펌", "염색",
             "hairstyle", "bobcut", "layeredcut", "koreahairstyle"],
}

# 별칭 (자유 표기 → 정본 줄기)
ALIAS = {
    "흑백": "흑백", "마인드": "흑백", "철학": "흑백",
    "컬러": "컬러", "감성": "컬러", "일기": "컬러", "반보": "컬러", "재아": "컬러",
    "만화": "만화카드", "만화카드": "만화카드", "카드": "만화카드", "카드뉴스": "만화카드",
    "교육": "교육", "커트의정석": "교육", "창엽": "교육",
    "미용": "미용", "시술": "미용", "스타일": "미용",
}


def resolve(stem: str) -> str:
    """자유 표기 줄기명을 정본 키로 정규화. 모르면 '미용'(가장 범용)."""
    return ALIAS.get((stem or "").strip(), "미용")


def tag_list(stem: str, limit: int = 30) -> list[str]:
    """줄기별 해시태그 단어 리스트(# 없이). 브랜드 우선, 중복 제거."""
    key = resolve(stem)
    seen: dict[str, None] = {}
    for t in BRAND + STEMS.get(key, []):
        seen.setdefault(t, None)
    return list(seen)[:limit]


def hashtag_block(stem: str, limit: int = 30) -> str:
    """'#앳나운 #청담미용실 ...' 한 줄."""
    return " ".join("#" + t for t in tag_list(stem, limit))


def caption_with_tags(body: str, stem: str, limit: int = 30) -> str:
    """본문 + 빈 줄 + 해시태그 블록. 이미 해시태그가 있으면 본문만 반환(중복 방지)."""
    body = (body or "").rstrip()
    if "#" in body:  # 이미 태그가 들어있으면 손대지 않음
        return body
    return f"{body}\n\n{hashtag_block(stem, limit)}".strip()


def youtube_tags(stem: str) -> list[str]:
    """유튜브 snippet.tags용(최대 30). # 없이."""
    return tag_list(stem, 30)


def main(argv: list[str] | None = None) -> int:
    import sys
    args = argv if argv is not None else sys.argv[1:]
    stem = args[0] if args else "교육"
    print(f"[줄기: {stem} → {resolve(stem)}]")
    print("해시태그:", hashtag_block(stem))
    print("유튜브 tags:", youtube_tags(stem))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
