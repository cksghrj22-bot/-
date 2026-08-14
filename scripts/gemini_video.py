#!/usr/bin/env python3
"""
Gemini Veo 영상 생성 스크립트
사용법: python3 scripts/gemini_video.py "프롬프트" output.mp4

2026-08-14 생성
"""
import sys
import json
import time
import base64
import urllib.request
import urllib.error
from pathlib import Path

SECRETS = Path(__file__).parent.parent / "secrets"

def load_api_key():
    key_file = SECRETS / "gemini.json"
    if not key_file.exists():
        print("❌ secrets/gemini.json 없음")
        sys.exit(1)
    return json.loads(key_file.read_text()).get("api_key", "")

def generate_video(prompt: str, output_path: str, model: str = "veo-3.1-fast-generate-preview"):
    """Veo로 영상 생성"""
    api_key = load_api_key()

    # 영상 생성 요청
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateVideo?key={api_key}"

    payload = {
        "prompt": prompt,
        "config": {
            "numberOfVideos": 1,
            "durationSeconds": 5,  # 5초 영상
            "aspectRatio": "9:16",  # 세로 영상 (쇼츠용)
        }
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        print(f"🎬 영상 생성 시작: {prompt[:50]}...")
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())

        # 작업 ID 추출 (비동기 작업)
        operation_name = result.get("name")
        if operation_name:
            print(f"⏳ 작업 ID: {operation_name}")
            return poll_operation(api_key, operation_name, output_path)

        # 즉시 결과가 있는 경우
        return handle_result(result, output_path)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ HTTP 에러 {e.code}: {error_body}")
        return False
    except Exception as e:
        print(f"❌ 에러: {e}")
        return False

def poll_operation(api_key: str, operation_name: str, output_path: str, max_wait: int = 300):
    """비동기 작업 완료 대기"""
    url = f"https://generativelanguage.googleapis.com/v1beta/{operation_name}?key={api_key}"

    start = time.time()
    while time.time() - start < max_wait:
        try:
            resp = urllib.request.urlopen(url, timeout=30)
            result = json.loads(resp.read())

            if result.get("done"):
                print("✅ 생성 완료")
                return handle_result(result.get("response", {}), output_path)

            progress = result.get("metadata", {}).get("progress", 0)
            print(f"⏳ 진행 중... {progress}%")
            time.sleep(5)

        except Exception as e:
            print(f"⚠️ 폴링 에러: {e}")
            time.sleep(5)

    print("❌ 타임아웃")
    return False

def handle_result(result: dict, output_path: str):
    """결과 처리 및 저장"""
    videos = result.get("generatedVideos", [])
    if not videos:
        print("❌ 생성된 영상 없음")
        print(f"응답: {json.dumps(result, indent=2)[:500]}")
        return False

    video_data = videos[0].get("video", {})

    # base64 데이터인 경우
    if "videoBytes" in video_data:
        video_bytes = base64.b64decode(video_data["videoBytes"])
        Path(output_path).write_bytes(video_bytes)
        print(f"✅ 저장: {output_path} ({len(video_bytes):,} bytes)")
        return True

    # URL인 경우
    if "uri" in video_data:
        video_url = video_data["uri"]
        print(f"📥 다운로드: {video_url}")
        urllib.request.urlretrieve(video_url, output_path)
        print(f"✅ 저장: {output_path}")
        return True

    print("❌ 영상 데이터 형식 알 수 없음")
    print(f"응답: {json.dumps(result, indent=2)[:500]}")
    return False

def main():
    if len(sys.argv) < 3:
        print("사용법: python3 scripts/gemini_video.py \"프롬프트\" output.mp4")
        print()
        print("옵션:")
        print("  --fast    빠른 생성 (기본)")
        print("  --full    고품질 생성")
        print("  --lite    가벼운 생성")
        print()
        print("예시:")
        print('  python3 scripts/gemini_video.py "헤어샵에서 머리 자르는 장면, 시네마틱" hair_cut.mp4')
        sys.exit(1)

    prompt = sys.argv[1]
    output = sys.argv[2]

    # 모델 선택
    model = "veo-3.1-fast-generate-preview"
    if "--full" in sys.argv:
        model = "veo-3.1-generate-preview"
    elif "--lite" in sys.argv:
        model = "veo-3.1-lite-generate-preview"

    print(f"모델: {model}")
    success = generate_video(prompt, output, model)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
