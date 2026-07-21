"""B롤 자동 선택 엔진 — 대본 주제를 넣으면 알맞은 배경 클립을 스스로 고른다.

이찬호: "내가 계속 올려주는 게 아니라, 스캔해서 B롤 스스로 붙이는 시스템을 만들어라."

흐름:
    대본 텍스트 → 키워드 점수로 카테고리 판별 → 카탈로그에서 클립 선택
    (덜 쓴 것 우선 · 파일ID 있는 것 우선 · 1편=고유 원본) → [카테고리·파일ID·시작초] 출력

데이터 정본: knowledge/broll_catalog.json  (사람 원장: knowledge/B롤카탈로그.md)
기준표(사람용): prompts/10_B롤_선택기준.md

사용:
    python3 -m shorts.broll "네 위치는 네가 만든다. 브랜드는 성장이다"
        → aerial · DJI_152313 · start 0  (파일ID 없으면 A방이 채울 것 표시)
    python3 -m shorts.broll --script content/shorts/2026-07-18/07.txt
    python3 -m shorts.broll "..." --mark DJI_152313   # 사용 처리(uses+1) → 다음엔 다른 걸 고름
    python3 -m shorts.broll --list                     # 카탈로그 상태 표
"""

from __future__ import annotations

import json
import re
from pathlib import Path

CATALOG_PATH = Path("knowledge/broll_catalog.json")

# ── 주제 → 카테고리 키워드 사전 (prompts/10 매칭표를 코드로) ──────────────────
# 각 카테고리에 딸린 단어가 대본에 나오면 그 카테고리 점수가 오른다. 최고점 = 배경.
KEYWORDS: dict[str, list[str]] = {
    "cut": ["커트", "숱", "볼륨", "펌", "질감", "가위", "머릿결", "층", "다운펌", "자르", "손질"],
    "consult": ["상담", "단골", "진단", "신뢰", "정착", "예약", "첫방문", "재방문", "고객", "손님"],
    "workout": ["운동", "자기투자", "지속", "오래", "태도", "몸", "루틴", "땀", "훈련", "습관", "꾸준"],
    "reading": ["기록", "독서", "책", "지적자본", "배움", "공부", "메모", "수첩", "읽", "글", "일기"],
    "aerial": ["브랜드", "위치", "성장", "마인드", "위로", "사색", "우화", "길", "나아가", "방향",
               "꿈", "본질", "가치", "정체성", "철학", "삶", "인생", "여정", "노래"],
    "scalp": ["두피", "스케일링", "탈모", "모근", "각질", "두피케어"],
}

# aerial = 마인드/추상 기본값(대본이 미용 시술을 안 가리키면 대개 마인드성)
DEFAULT_CATEGORY = "aerial"


def load_catalog(path: Path = CATALOG_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def classify(text: str) -> tuple[str, dict[str, int]]:
    """대본 텍스트 → (카테고리, 카테고리별 점수). 동점/무점수면 기본값."""
    scores = {cat: 0 for cat in KEYWORDS}
    for cat, words in KEYWORDS.items():
        for w in words:
            scores[cat] += len(re.findall(re.escape(w), text))
    best = max(scores, key=lambda c: scores[c])
    if scores[best] == 0:
        return DEFAULT_CATEGORY, scores
    return best, scores


def pick(category: str, catalog: dict, *, require_file_id: bool = False) -> dict | None:
    """카테고리에서 클립 하나 선택. 덜 쓴 것 → 파일ID 있는 것 우선. 없으면 None.

    `usable: false` 클립은 제외한다 — 실내 오분류·다운로드 불가·인물리스크 등
    렌더에 부적합한 소스가 uses=0이라는 이유로 1순위 선택되는 사고를 막는다.
    """
    clips = [c for c in catalog["clips"]
             if c["category"] == category and c.get("usable", True)]
    if require_file_id:
        clips = [c for c in clips if c.get("file_id")]
    if not clips:
        return None
    # 정렬 키: 지금 렌더 가능한 것(file_id 있음) 먼저 → 그중 덜 쓴 것 우선.
    clips.sort(key=lambda c: (0 if c.get("file_id") else 1, c.get("uses", 0)))
    return clips[0]


def select_for_script(text: str, catalog: dict | None = None) -> dict:
    """대본 텍스트 하나로 카테고리 판별 + 클립 선택까지. 결과 dict."""
    catalog = catalog or load_catalog()
    category, scores = classify(text)
    clip = pick(category, catalog)
    return {
        "category": category,
        "scores": scores,
        "clip": clip,
        "ready": bool(clip and clip.get("file_id")),
    }


def mark_used(clip_id: str, catalog: dict, path: Path = CATALOG_PATH) -> bool:
    """클립 사용 처리(uses+1) 후 저장 → 다음 선택 때 덜 쓴 다른 걸 고르게."""
    for c in catalog["clips"]:
        if c["id"] == clip_id:
            c["uses"] = c.get("uses", 0) + 1
            path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
            return True
    return False


def _fmt(result: dict) -> str:
    c = result["clip"]
    cat = result["category"]
    if not c:
        return f"[{cat}] 후보 클립이 카탈로그에 없음 — knowledge/B롤_촬영요청.md에 추가 필요"
    fid = c.get("file_id") or "‼️파일ID없음(A방 스캔으로 채울 것)"
    return (f"# B롤: [{cat} · {c['id']} · start {c.get('start', 0)} · id {fid}]"
            + ("" if result["ready"] else "   ← 렌더 전 A방이 file_id 채움"))


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="B롤 자동 선택")
    ap.add_argument("text", nargs="?", default="", help="대본 텍스트(주제)")
    ap.add_argument("--script", help="대본 파일 경로(내용을 읽어 판별)")
    ap.add_argument("--mark", help="이 클립 id를 사용 처리(uses+1)")
    ap.add_argument("--list", action="store_true", help="카탈로그 상태 표")
    ap.add_argument("--catalog", default=str(CATALOG_PATH))
    args = ap.parse_args(argv)

    catalog = load_catalog(Path(args.catalog))

    if args.list:
        print(f"{'id':16} {'카테고리':10} {'uses':>4}  file_id")
        for c in catalog["clips"]:
            fid = c.get("file_id") or "— (스캔 필요)"
            print(f"{c['id']:16} {c['category']:10} {c.get('uses',0):>4}  {fid}")
        return 0

    if args.mark:
        ok = mark_used(args.mark, catalog, Path(args.catalog))
        print(f"{'✓ 사용처리' if ok else '✗ 그런 id 없음'}: {args.mark}")
        return 0 if ok else 1

    text = args.text
    if args.script:
        text = Path(args.script).read_text(encoding="utf-8")
    if not text.strip():
        ap.error("대본 텍스트나 --script 를 줘야 함")

    result = select_for_script(text, catalog)
    print(_fmt(result))
    top = sorted(result["scores"].items(), key=lambda kv: -kv[1])[:3]
    hint = ", ".join(f"{k}={v}" for k, v in top if v)
    if hint:
        print(f"  (판별 점수: {hint})")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
