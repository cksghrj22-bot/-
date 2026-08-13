#!/usr/bin/env python3
"""
만화 연재 자동 생성기 — Gemini 나노바나나 (gemini-2.5-flash-image)

사용법:
    python3 scripts/manga_generator.py "대본 텍스트" --output _tmp/manga_output
    python3 scripts/manga_generator.py --from-file content/manga/대본.txt --output _tmp/manga_output
"""
import json
import sys
import time
from pathlib import Path

from gemini_image import generate_image

ROOT = Path(__file__).parent.parent
DEFAULT_OUTPUT = ROOT / "_tmp" / "manga_output"

# 만화 스타일 프롬프트 (고정)
STYLE_PROMPT = """
Style: Clean Korean webtoon style, simple cartoon illustration, warm and friendly colors.
Character: Korean hairdresser/salon professional, expressive face, clear emotions.
Background: Simple, not distracting, focus on character.
Text: No text in image (text will be added separately).
"""

def parse_script(text: str) -> dict:
    """
    대본 텍스트를 분석해서 6장 구성 추출
    """
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]

    # 핵심 메시지 추출
    keywords = []
    for line in lines:
        if len(line) > 10:
            keywords.append(line[:50])

    return {
        "full_text": text,
        "keywords": keywords[:6],
        "line_count": len(lines)
    }


def generate_manga_6panels(script_text: str, output_dir: str = None, title: str = "만화") -> list:
    """
    대본으로 6장 만화 생성 (표지 포함)

    1. 표지
    2-5. 본문 4장
    6. 결론/CTA
    """
    out = Path(output_dir or DEFAULT_OUTPUT)
    out.mkdir(parents=True, exist_ok=True)

    parsed = parse_script(script_text)

    # 6장 프롬프트 정의
    panels = [
        {
            "name": "01_표지",
            "prompt": f"Cover page illustration. A confident Korean hairdresser character holding scissors, looking at camera with a knowing smile. Title card style. {STYLE_PROMPT}"
        },
        {
            "name": "02_착한곱슬",
            "prompt": f"Illustration showing: A happy woman with natural curly hair that gives good volume. The curls look healthy and bouncy. Show 'good curls' concept. {STYLE_PROMPT}"
        },
        {
            "name": "03_다펴면",
            "prompt": f"Illustration showing: A sad woman with flat, lifeless hair after over-straightening. Hair sticks to head, no volume. Show the negative result. {STYLE_PROMPT}"
        },
        {
            "name": "04_매직도펌",
            "prompt": f"Illustration showing: A hairdresser explaining something with a questioning gesture. Show the concept 'magic straightening is also a perm'. {STYLE_PROMPT}"
        },
        {
            "name": "05_종류다양",
            "prompt": f"Illustration showing: Multiple hair styling options displayed - 10%, 30%, 50% straightening, surface magic. Show variety of choices. {STYLE_PROMPT}"
        },
        {
            "name": "06_맞는주문",
            "prompt": f"Closing illustration. A hairdresser and happy customer having a consultation. The customer is pointing at their hair, asking for advice. Warm, positive mood. {STYLE_PROMPT}"
        }
    ]

    results = []
    for i, panel in enumerate(panels):
        output_path = out / f"{panel['name']}.png"
        print(f"🎨 {i+1}/6 생성 중: {panel['name']}...")

        try:
            result = generate_image(panel["prompt"], str(output_path))
            if result:
                print(f"  ✅ 완료: {output_path.name}")
                results.append(str(output_path))
            else:
                print(f"  ❌ 실패: {panel['name']}")
                results.append(None)
        except Exception as e:
            print(f"  ❌ 에러: {e}")
            results.append(None)

        # API 레이트 리밋 방지
        if i < len(panels) - 1:
            time.sleep(2)

    print(f"\n📁 저장 위치: {out}")
    print(f"✅ 성공: {len([r for r in results if r])}/6")

    return results


def main():
    import argparse
    ap = argparse.ArgumentParser(description="만화 6장 자동 생성 (나노바나나)")
    ap.add_argument("script", nargs="?", help="대본 텍스트 (직접 입력)")
    ap.add_argument("--from-file", help="대본 파일 경로")
    ap.add_argument("--output", default=str(DEFAULT_OUTPUT), help="출력 폴더")
    ap.add_argument("--title", default="만화", help="만화 제목")
    args = ap.parse_args()

    if args.from_file:
        script_text = Path(args.from_file).read_text(encoding="utf-8")
    elif args.script:
        script_text = args.script
    else:
        print("대본 텍스트 또는 --from-file 필요")
        sys.exit(1)

    results = generate_manga_6panels(script_text, args.output, args.title)

    # 결과 요약
    success = len([r for r in results if r])
    if success == 6:
        print("\n🎉 만화 6장 모두 생성 완료!")
    else:
        print(f"\n⚠️ {6 - success}장 생성 실패 — 재시도 필요")

    return 0 if success == 6 else 1


if __name__ == "__main__":
    sys.exit(main())
