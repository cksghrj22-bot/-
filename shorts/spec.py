"""쇼츠 정본(定本) 락 + 자동 점검 — "이걸 하면 저걸 까먹는" 걸 코드가 막는다.

이찬호가 확정한 마인드 쇼츠 규격을 한 곳(SPEC)에 못박고, 렌더 전에 config가
그 값을 다 갖고 있는지 자동으로 확인한다. 하나라도 어긋나면 렌더가 큰 경고를 띄운다.
규격을 "의도적으로" 바꿀 때만 여기 SPEC을 같이 고친다 → 실수로 빠지는 일이 없어진다.

사용:
    python3 -m shorts.spec            # 현재 config가 정본과 맞는지 ✓/✗ 표로 출력
    (렌더 시 proof가 자동 호출 — 어긋나면 경고)
"""

from __future__ import annotations

import json
from pathlib import Path

# ── 정본 락 (이찬호 확정값 — 바꾸려면 여기부터 고친다) ──────────────────────
PRESET = "style_preset_mind"

SPEC = {
    "layout": "dim",
    "fit": "crop45",
    "video_area": [1080, 1200],
    "dim_opacity": 0.0,                       # 전체 반투명 블랙 "깔기" (2026-07-17)
    "grade": "bw",                      # 기본 컬러 필터 (2026-07-15)
    "outro_text": "SNS에 일기를 쓰고 있어요",   # 마무리 브랜딩 (2026-07-17 확정 문구)
    "subtitle": {
        "font": "KyoboHandwriting2019",
        "size": 98,
        "box_opacity": 100,                    # 자막 뒤 검정박스 100%
        "alignment": 5,                        # 화면 정가운데
    },
    "title": {
        "font": "KyoboHandwriting2019",
        "size": 128,                           # 제목 > 자막
    },
    "outro_style": {"alpha": "20", "dur": 2.6},
}

GRADE_PALETTE = {"warm_film", "clean", "cinema", "bw", "none"}  # 지우지 말 것


def check_spec(config: dict, grades: set | None = None) -> list[str]:
    """config가 정본과 맞는지 점검. 문제 목록을 돌려준다(빈 리스트 = 정상)."""
    issues: list[str] = []
    p = config.get(PRESET)
    if not p:
        return [f"'{PRESET}' 프리셋이 config에 없음"]

    def eq(label, got, want):
        if got != want:
            issues.append(f"{label}: {got!r} ≠ 정본 {want!r}")

    eq("layout", p.get("layout"), SPEC["layout"])
    eq("fit", p.get("fit"), SPEC["fit"])
    eq("video_area", list(p.get("video_area", [])), SPEC["video_area"])
    eq("dim_opacity(블랙 깔기)", p.get("dim_opacity"), SPEC["dim_opacity"])
    eq("grade(기본 필터)", p.get("grade"), SPEC["grade"])
    eq("outro_text(마무리 문구)", p.get("outro_text"), SPEC["outro_text"])

    st = p.get("subtitle_style", {})
    eq("자막 폰트", st.get("font"), SPEC["subtitle"]["font"])
    eq("자막 크기", st.get("size"), SPEC["subtitle"]["size"])
    eq("자막 박스 불투명도", st.get("box_opacity"), SPEC["subtitle"]["box_opacity"])
    eq("자막 정렬(가운데)", st.get("alignment"), SPEC["subtitle"]["alignment"])

    tt = p.get("title_style", {})
    eq("제목 폰트", tt.get("font"), SPEC["title"]["font"])
    eq("제목 크기", tt.get("size"), SPEC["title"]["size"])
    if tt.get("size", 0) <= st.get("size", 0):
        issues.append(f"제목({tt.get('size')})이 자막({st.get('size')})보다 크지 않음 — 제목>자막 규칙 위반")

    ost = p.get("outro_style", {})
    eq("아웃트로 투명도", ost.get("alpha"), SPEC["outro_style"]["alpha"])
    eq("아웃트로 노출초", ost.get("dur"), SPEC["outro_style"]["dur"])

    if "저장" in (p.get("outro_text") or ""):
        issues.append("아웃트로에 '저장' 들어감 — 저장 CTA 금지 규칙 위반")

    if grades is not None and not GRADE_PALETTE.issubset(grades):
        미싱 = GRADE_PALETTE - grades
        issues.append(f"필터 팔레트에서 빠진 grade: {sorted(미싱)} (지우지 말 것)")

    return issues


def format_report(config: dict, grades: set | None = None) -> str:
    issues = check_spec(config, grades)
    if not issues:
        return "🔒 정본 점검 ✓ — 모든 규격 이상 없음 (dim25·필터·아웃트로·박스·제목>자막)"
    lines = ["🔴 정본 점검 실패 — 아래가 정본과 어긋남 (렌더 전 고칠 것):"]
    lines += [f"   ✗ {m}" for m in issues]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="쇼츠 정본 점검")
    ap.add_argument("--config", default="shorts_config.json")
    args = ap.parse_args(argv)
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    try:
        from .proof import GRADES
        grades = set(GRADES)
    except Exception:
        grades = None
    print(format_report(config, grades))
    return 1 if check_spec(config, grades) else 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
