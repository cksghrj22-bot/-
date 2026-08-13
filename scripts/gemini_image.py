#!/usr/bin/env python3
"""
만화연재 이미지 생성 — Gemini (나노바나나2)
"""
import json
import urllib.request
import base64
from pathlib import Path

ROOT = Path(__file__).parent.parent
SECRETS = ROOT / "secrets"

def get_api_key():
    return json.loads((SECRETS / "gemini.json").read_text())["api_key"]

def generate_image(prompt: str, output_path: str = None) -> str:
    """
    프롬프트로 이미지 생성 (Gemini / 나노바나나 = gemini-2.5-flash-image)
    반환: 저장된 파일 경로 또는 base64 이미지
    """
    key = get_api_key()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={key}"

    payload = {
        "contents": [{
            "parts": [{
                "text": f"Create an image: {prompt}"
            }]
        }]
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )

    resp = json.loads(urllib.request.urlopen(req, timeout=120).read())

    # 이미지 추출 (Gemini 응답 형식 - candidates[0].content.parts에서 inlineData 찾기)
    candidates = resp.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        for part in parts:
            if "inlineData" in part:
                img_data = part["inlineData"]["data"]
                if output_path:
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    Path(output_path).write_bytes(base64.b64decode(img_data))
                    return output_path
                return img_data

    return None

def generate_manga_panels(story_text: str, panel_count: int = 6, output_dir: str = None) -> list:
    """
    스토리 텍스트로 만화 패널 여러 장 생성
    """
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    results = []
    for i in range(panel_count):
        prompt = f"Panel {i+1} of {panel_count}: {story_text}"
        out_path = f"{output_dir}/panel_{i+1:02d}.png" if output_dir else None
        result = generate_image(prompt, out_path)
        results.append(result)
        print(f"✅ 패널 {i+1}/{panel_count} 생성")

    return results

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("사용법: python3 gemini_image.py '프롬프트' [출력파일]")
        sys.exit(1)

    prompt = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else None

    result = generate_image(prompt, output)
    if result:
        print(f"✅ 생성 완료: {output or '(base64)'}")
    else:
        print("❌ 생성 실패")
