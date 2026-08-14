#!/usr/bin/env python3
"""
Runway 영상 생성 (이미지→영상)
사용법:
  python3 scripts/runway_video.py image.png "카메라 줌인" output.mp4
  python3 scripts/runway_video.py --text "프롬프트" output.mp4  (텍스트만)

토큰 사용량: 5초=50, 10초=100 (대략)
1000토큰 = 약 20개 5초 영상

2026-08-14 생성
"""
import sys
import json
import time
import base64
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

SECRETS = Path(__file__).parent.parent / "secrets"
DATA = Path(__file__).parent.parent / "data"
API_BASE = "https://api.dev.runwayml.com/v1"
USAGE_LOG = DATA / "runway_usage.json"

def load_api_key():
    key_file = SECRETS / "runway.json"
    if not key_file.exists():
        print("❌ secrets/runway.json 없음")
        sys.exit(1)
    return json.loads(key_file.read_text()).get("api_key", "")

def log_usage(duration: int, success: bool, prompt: str):
    """사용량 로그"""
    DATA.mkdir(exist_ok=True)

    usage = {"total_tokens": 0, "videos": []}
    if USAGE_LOG.exists():
        usage = json.loads(USAGE_LOG.read_text())

    tokens = 50 if duration == 5 else 100
    if success:
        usage["total_tokens"] += tokens

    usage["videos"].append({
        "date": datetime.now().isoformat(),
        "duration": duration,
        "tokens": tokens if success else 0,
        "success": success,
        "prompt": prompt[:50]
    })

    USAGE_LOG.write_text(json.dumps(usage, indent=2, ensure_ascii=False))

    remaining = 1000 - usage["total_tokens"]
    print(f"📊 사용량: {usage['total_tokens']}/1000 토큰 (남은: {remaining})")

    if remaining <= 0:
        print("🚨 1000토큰 소진! 형에게 보고 필요")

def image_to_base64(image_path: str) -> str:
    """이미지를 base64로 변환"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def generate_from_image(image_path: str, prompt: str, output_path: str, duration: int = 5):
    """이미지에서 영상 생성"""
    api_key = load_api_key()

    # 이미지 base64 인코딩
    img_ext = Path(image_path).suffix.lower()
    mime = {"png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(img_ext, "image/png")
    img_b64 = image_to_base64(image_path)

    url = f"{API_BASE}/image_to_video"

    payload = {
        "model": "gen4_turbo",
        "promptImage": f"data:{mime};base64,{img_b64}",
        "promptText": prompt,
        "duration": duration,
        "ratio": "720:1280",
    }

    return _send_request(url, payload, output_path, duration, prompt, api_key)

def generate_from_text(prompt: str, output_path: str, duration: int = 5):
    """텍스트에서 영상 생성 (Gen-4.5)"""
    api_key = load_api_key()

    url = f"{API_BASE}/text_to_video"

    payload = {
        "model": "gen4.5",
        "promptText": prompt,
        "duration": duration,
        "ratio": "720:1280",
    }

    return _send_request(url, payload, output_path, duration, prompt, api_key)

def _send_request(url: str, payload: dict, output_path: str, duration: int, prompt: str, api_key: str):
    """API 요청 전송"""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "X-Runway-Version": "2024-11-06",
        },
        method="POST"
    )

    try:
        print(f"🎬 Runway 영상 생성: {prompt[:50]}...")
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())

        task_id = result.get("id")
        if task_id:
            print(f"⏳ 작업 ID: {task_id}")
            success = poll_task(api_key, task_id, output_path)
            log_usage(duration, success, prompt)
            return success

        print(f"❌ 응답: {result}")
        log_usage(duration, False, prompt)
        return False

    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ HTTP {e.code}: {error_body[:200]}")
        log_usage(duration, False, prompt)
        return False
    except Exception as e:
        print(f"❌ 에러: {e}")
        log_usage(duration, False, prompt)
        return False

def poll_task(api_key: str, task_id: str, output_path: str, max_wait: int = 300):
    """작업 완료 대기"""
    url = f"{API_BASE}/tasks/{task_id}"

    start = time.time()
    while time.time() - start < max_wait:
        try:
            req = urllib.request.Request(url, headers={
                "Authorization": f"Bearer {api_key}",
                "X-Runway-Version": "2024-11-06",
            })
            resp = urllib.request.urlopen(req, timeout=30)
            result = json.loads(resp.read())

            status = result.get("status")
            progress = result.get("progress", 0)
            print(f"⏳ {status} ({progress}%)")

            if status == "SUCCEEDED":
                output_url = result.get("output", [None])[0]
                if output_url:
                    urllib.request.urlretrieve(output_url, output_path)
                    print(f"✅ 저장: {output_path}")
                    return True
                return False

            if status == "FAILED":
                print(f"❌ 실패: {result.get('failure', '?')}")
                return False

            time.sleep(5)
        except Exception as e:
            print(f"⚠️ {e}")
            time.sleep(5)

    print("❌ 타임아웃")
    return False

def show_usage():
    """사용량 확인"""
    if not USAGE_LOG.exists():
        print("📊 사용량: 0/1000 토큰")
        return

    usage = json.loads(USAGE_LOG.read_text())
    total = usage.get("total_tokens", 0)
    videos = usage.get("videos", [])

    print(f"📊 Runway 사용량: {total}/1000 토큰")
    print(f"   생성 영상: {len([v for v in videos if v.get('success')])}개")
    print(f"   남은 토큰: {1000 - total}")

def main():
    if len(sys.argv) < 2:
        print("사용법:")
        print("  이미지→영상: python3 scripts/runway_video.py image.png \"움직임\" output.mp4")
        print("  텍스트→영상: python3 scripts/runway_video.py --text \"프롬프트\" output.mp4")
        print("  사용량 확인: python3 scripts/runway_video.py --usage")
        sys.exit(1)

    if sys.argv[1] == "--usage":
        show_usage()
        return

    duration = 10 if "--10s" in sys.argv else 5

    if sys.argv[1] == "--text":
        prompt = sys.argv[2]
        output = sys.argv[3]
        success = generate_from_text(prompt, output, duration)
    else:
        image = sys.argv[1]
        prompt = sys.argv[2]
        output = sys.argv[3]
        success = generate_from_image(image, prompt, output, duration)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
