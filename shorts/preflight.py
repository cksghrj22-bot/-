"""제작 전 강제 게이트 — "예전에 한 거 까먹고 또 만드는" 버그를 코드로 막는다(2026-07-28 이찬호 지시).

배경(형 정곡): 규칙을 markdown에 '박제'해도 매 세션 내가 *읽어야* 발동한다 → 안 읽으면 중복 생성
(오늘 주파수 재탕이 실증). 코드로 박은 규칙(교보폰트·타임스탬프싱크)은 한 번도 안 틀렸다.
그래서 '착수 전 중복검색'을 **prose가 아니라 실행 게이트**로 만든다. 만들기 전에 무조건 통과해야 한다.

무엇을 검사하나:
  1) 지식 인덱스(data/index.json) 의미검색 — 같은 논지의 기존 대본이 있나(TF-IDF).
  2) knowledge/유튜브_예약현황.md — 이미 발행/예약된 제목과 키워드 겹침.
결과:
  OK   = 새 주제. 진행.
  WARN = 비슷한 게 있음. 차별점 확인하고 진행.
  BLOCK= 사실상 같은 게 이미 발행/예약됨. 만들지 마라(형 승인 없이는).

쓰는 법:
    python3 -m shorts.preflight "상담 주파수 커트 10분"
    from shorts.preflight import check ; v = check("메타안경 콘텐츠 자산")  # v["verdict"], v["matches"]
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "data" / "index.json"
SCHEDULE_MD = ROOT / "knowledge" / "유튜브_예약현황.md"

# 논지가 겹치는지 볼 때 무시할 흔한 토큰(조사/일반어).
_STOP = {"이", "그", "저", "수", "것", "때", "더", "왜", "안", "못", "다", "좀", "은", "는", "이런",
         "미용실", "미용사", "머리", "헤어", "영상", "편", "이유", "진짜", "후기", "하는", "하기",
         "이게", "그거", "저거", "당신", "우리", "요즘", "그냥"}


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[가-힣A-Za-z0-9]+", text)
    return {w for w in words if len(w) >= 2 and w not in _STOP}


def _published_titles() -> list[str]:
    """예약현황.md 표에서 발행/예약된 제목만 뽑는다(videoId가 붙은 행)."""
    if not SCHEDULE_MD.exists():
        return []
    titles = []
    for line in SCHEDULE_MD.read_text(encoding="utf-8").splitlines():
        # | 제목 | **videoId** | ... 형태의 행에서 제목 셀
        if "**" not in line or line.count("|") < 3:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        # videoId(** **)를 가진 행의 첫 셀을 제목으로
        if any(re.fullmatch(r"\*\*[A-Za-z0-9_-]{6,}\*\*", c) for c in cells):
            title = cells[0]
            if title and not title.startswith("-") and "편" != title:
                titles.append(title)
    return titles


def _overlap(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def check(topic: str, index_path: str | Path = INDEX_PATH,
          block_at: float = 0.5, warn_at: float = 0.3) -> dict:
    """topic(제목/핵심키워드)이 기존 발행물과 중복인지 판정."""
    matches: list[dict] = []

    # 1) 발행/예약 제목과 키워드 겹침(가장 강한 신호 — 이미 세상에 나간 것)
    best_pub = 0.0
    for t in _published_titles():
        ov = _overlap(topic, t)
        if ov >= warn_at:
            matches.append({"kind": "발행/예약", "ref": t, "score": round(ov, 2)})
            best_pub = max(best_pub, ov)

    # 2) 지식 인덱스 의미검색(기존 대본 유사도)
    idx_hit = 0.0
    try:
        from pipeline.index import Index
        p = Path(index_path)
        if p.exists():
            for chunk, score in Index.load(p).search(topic, top_k=5):
                src = getattr(chunk, "source", "")
                if ("대본" in src or "shorts" in src) and score >= 4.0:
                    matches.append({"kind": "기존대본", "ref": src, "score": round(score, 2)})
                    idx_hit = max(idx_hit, score)
    except Exception as e:  # 인덱스 깨졌으면 게이트는 발행목록만으로 판정(막지 않고 알림)
        matches.append({"kind": "인덱스오류", "ref": str(e)[:80], "score": 0})

    matches.sort(key=lambda m: -m["score"])
    if best_pub >= block_at:
        verdict = "BLOCK"
    elif best_pub >= warn_at or idx_hit >= 6.0:
        verdict = "WARN"
    else:
        verdict = "OK"
    return {"verdict": verdict, "topic": topic, "matches": matches[:6]}


def format_report(res: dict) -> str:
    icon = {"OK": "✅", "WARN": "⚠️", "BLOCK": "⛔"}[res["verdict"]]
    lines = [f"{icon} 중복게이트 [{res['verdict']}] — 주제: {res['topic']}"]
    if res["verdict"] == "BLOCK":
        lines.append("   → 이미 발행/예약된 것과 사실상 동일. 형 승인 없이 만들지 마라.")
    elif res["verdict"] == "WARN":
        lines.append("   → 비슷한 게 있다. 차별점을 명확히 하고 진행(같은 결론이면 중단).")
    else:
        lines.append("   → 새 주제. 진행 가능.")
    for m in res["matches"]:
        lines.append(f"     · [{m['kind']} {m['score']}] {m['ref']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="제작 전 중복 게이트")
    ap.add_argument("topic", help="제목 또는 핵심 키워드(따옴표로 묶어서)")
    ap.add_argument("--index", default=str(INDEX_PATH))
    a = ap.parse_args(argv)
    res = check(a.topic, index_path=a.index)
    print(format_report(res))
    return 2 if res["verdict"] == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
