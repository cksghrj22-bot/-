#!/usr/bin/env python3
"""
결이 이야기 만화 파이프라인 — Gemini 나노바나나 + Codex 연동

사용법:
    python3 scripts/manga_pipeline.py "대본 텍스트" --title "매직편"
    python3 scripts/manga_pipeline.py --from-file content/manga/대본.txt --title "착한곱슬편"

출력:
    _tmp/manga/{title}/ 폴더에 6장 이미지 생성
    코워크 만화연재방 inbox에 업로드 (--upload 옵션)
"""
import json
import sys
import time
from pathlib import Path

from gemini_image import generate_image

ROOT = Path(__file__).parent.parent
SECRETS = ROOT / "secrets"

# 결이 캐릭터 시트 (검수_결이이야기_01_매듭_2026-08-13.md 기반)
GYEORI_SHEET = """
Character: "Gyeori" (결이)
- Round cream-colored face
- Orange/mustard colored hair strands that form the body
- Small legs
- Expressive face with simple features
- Warm, friendly appearance
- NOT a knot or rope (the villain is the knot, Gyeori is the victim)

Visual Style:
- Hand-drawn ink line art feel
- Cream paper texture background
- Color palette: Cream background, Brown accents, Orange point color
- Simple webtoon/manga style
- NOT photorealistic, NOT glossy advertisement style
"""

BORI_SHEET = """
Character: "Bori" (보리) - The customer
- Human customer receiving hair service
- Consistent appearance across all panels
- Same angle and lighting in before/after shots
- No heavy retouching or beautification
"""

STYLE_RULES = """
Style Rules:
1. Only TWO characters have faces: Gyeori and Bori
2. Problems (knots, tangles, machines) are drawn as faceless objects
3. Maximum 2 lines of text per panel, max 18 characters per line
4. No glossy advertisement look
5. Consistent character appearance across all panels
"""


def parse_script_to_panels(text: str, num_panels: int = 6) -> list:
    """대본을 패널별 프롬프트로 분해"""
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]

    # 기본 6장 구조
    panels = []

    # 1. 표지
    panels.append({
        "type": "cover",
        "prompt": f"Cover page. Title card style with badge design. Shows Gyeori character prominently. Hook question in customer language. {GYEORI_SHEET} {STYLE_RULES}"
    })

    # 2. 문제 제시 (손님 등장)
    panels.append({
        "type": "problem",
        "prompt": f"Panel showing the problem. Customer Bori looking concerned/confused. Hair problem visualized (but NOT as a face). {BORI_SHEET} {GYEORI_SHEET} {STYLE_RULES}"
    })

    # 3. 오해/통념
    panels.append({
        "type": "misconception",
        "prompt": f"Panel showing common misconception. Gyeori explaining, Bori listening. Visual metaphor for wrong understanding. {GYEORI_SHEET} {BORI_SHEET} {STYLE_RULES}"
    })

    # 4. 재정의/진실
    panels.append({
        "type": "truth",
        "prompt": f"Panel showing the truth/insight. 'Aha moment' for Bori. Gyeori revealing the correct understanding. Bright, positive mood. {GYEORI_SHEET} {BORI_SHEET} {STYLE_RULES}"
    })

    # 5. 해결/변화
    panels.append({
        "type": "solution",
        "prompt": f"Panel showing the solution applied. Before/after comparison if applicable. Bori looking happy with the result. {GYEORI_SHEET} {BORI_SHEET} {STYLE_RULES}"
    })

    # 6. 결론/재정의 한 줄
    panels.append({
        "type": "conclusion",
        "prompt": f"Closing panel. One-line redefinition in CHANO style. Gyeori with confident expression. Warm, satisfying mood. {GYEORI_SHEET} {STYLE_RULES}"
    })

    return panels


def generate_manga(script_text: str, title: str, output_dir: str = None) -> dict:
    """
    6장 만화 생성

    Returns: {
        "title": str,
        "output_dir": str,
        "panels": [{"name": str, "path": str, "status": str}, ...]
    }
    """
    out = Path(output_dir or ROOT / "_tmp" / "manga" / title)
    out.mkdir(parents=True, exist_ok=True)

    panels = parse_script_to_panels(script_text)
    results = []

    for i, panel in enumerate(panels):
        panel_name = f"{i+1:02d}_{panel['type']}"
        output_path = out / f"{panel_name}.png"

        print(f"🎨 {i+1}/6 생성 중: {panel_name}...")

        try:
            result = generate_image(panel["prompt"], str(output_path))
            if result:
                print(f"  ✅ 완료")
                results.append({"name": panel_name, "path": str(output_path), "status": "success"})
            else:
                print(f"  ❌ 실패")
                results.append({"name": panel_name, "path": None, "status": "failed"})
        except Exception as e:
            print(f"  ❌ 에러: {e}")
            results.append({"name": panel_name, "path": None, "status": f"error: {e}"})

        # API 레이트 리밋 방지
        if i < len(panels) - 1:
            time.sleep(3)

    success_count = len([r for r in results if r["status"] == "success"])
    print(f"\n📁 저장 위치: {out}")
    print(f"✅ 성공: {success_count}/6")

    return {
        "title": title,
        "output_dir": str(out),
        "panels": results
    }


def upload_to_cowork(output_dir: str) -> bool:
    """코워크 만화연재방 inbox에 업로드"""
    try:
        rooms = json.loads((SECRETS / "cowork_rooms.json").read_text())
        manga_room_id = rooms.get("만화연재방")
        if not manga_room_id:
            print("❌ 만화연재방 폴더 ID 없음")
            return False

        # gdrive.py로 업로드
        import subprocess
        out = Path(output_dir)
        for png in sorted(out.glob("*.png")):
            result = subprocess.run(
                ["python3", str(ROOT / "shorts" / "gdrive.py"), "upload", str(png), "--folder-id", manga_room_id],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"  ✅ 업로드: {png.name}")
            else:
                print(f"  ❌ 업로드 실패: {png.name}")

        return True
    except Exception as e:
        print(f"❌ 업로드 에러: {e}")
        return False


def main():
    import argparse
    ap = argparse.ArgumentParser(description="결이 이야기 만화 파이프라인")
    ap.add_argument("script", nargs="?", help="대본 텍스트")
    ap.add_argument("--from-file", help="대본 파일 경로")
    ap.add_argument("--title", default="untitled", help="만화 제목 (폴더명)")
    ap.add_argument("--output", help="출력 폴더 (기본: _tmp/manga/{title})")
    ap.add_argument("--upload", action="store_true", help="코워크 만화연재방에 업로드")
    args = ap.parse_args()

    if args.from_file:
        script_text = Path(args.from_file).read_text(encoding="utf-8")
    elif args.script:
        script_text = args.script
    else:
        print("대본 텍스트 또는 --from-file 필요")
        sys.exit(1)

    result = generate_manga(script_text, args.title, args.output)

    if args.upload and all(r["status"] == "success" for r in result["panels"]):
        print("\n📤 코워크 업로드 중...")
        upload_to_cowork(result["output_dir"])

    success = len([r for r in result["panels"] if r["status"] == "success"])
    return 0 if success == 6 else 1


if __name__ == "__main__":
    sys.exit(main())
