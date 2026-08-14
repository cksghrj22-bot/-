#!/usr/bin/env python3
"""
주간 전사 시뮬레이션 체크 — 매주 일요일 자동 실행
모든 브릿지 실제 테스트 + 예측 경고

2026-08-14 생성
"""
import json
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
SECRETS = ROOT / "secrets"
REPORT_FILE = ROOT / "_WEEKLY_REPORT.md"
LOG_FILE = ROOT / "data/weekly_check.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# === 브릿지 실제 테스트 ===

def test_instagram_api():
    """인스타 API 실제 호출 테스트"""
    try:
        token_file = SECRETS / "instagram.json"
        if not token_file.exists():
            return False, "토큰 없음", None

        data = json.loads(token_file.read_text())
        token = data.get("access_token", "")
        ig_id = data.get("instagram_account_id", "")

        # 미디어 목록 가져오기 테스트
        url = f"https://graph.facebook.com/v26.0/{ig_id}/media?fields=id&limit=1&access_token={token}"
        resp = urllib.request.urlopen(url, timeout=15)
        result = json.loads(resp.read())

        if "data" in result:
            return True, "API 정상", {"media_count": len(result.get("data", []))}
        return False, "응답 이상", result
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}", None
    except Exception as e:
        return False, str(e), None

def test_elevenlabs_api():
    """ElevenLabs API 실제 호출 테스트"""
    try:
        key_file = SECRETS / "elevenlabs.json"
        if not key_file.exists():
            return False, "키 없음", None

        key = json.loads(key_file.read_text()).get("api_key", "")
        req = urllib.request.Request(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": key}
        )
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())

        voices = data.get("voices", [])
        return True, f"{len(voices)}개 보이스", {"voice_count": len(voices)}
    except Exception as e:
        return False, str(e), None

def test_gemini_api():
    """Gemini API 실제 호출 테스트"""
    try:
        key_file = SECRETS / "gemini.json"
        if not key_file.exists():
            return False, "키 없음", None

        key = json.loads(key_file.read_text()).get("api_key", "")
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        resp = urllib.request.urlopen(url, timeout=15)
        data = json.loads(resp.read())

        models = data.get("models", [])
        return True, f"{len(models)}개 모델", {"model_count": len(models)}
    except Exception as e:
        return False, str(e), None

def test_drive_api():
    """Google Drive 연결 테스트 (MCP 통해서는 못함, 파일 존재만 확인)"""
    try:
        token_file = SECRETS / "gdrive.json"
        if not token_file.exists():
            return False, "토큰 없음", None
        return True, "토큰 있음", None
    except Exception as e:
        return False, str(e), None

def test_ffmpeg_render():
    """ffmpeg 렌더 테스트 (1초 검은 화면 생성)"""
    try:
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            out_path = f.name

        cmd = [
            "ffmpeg", "-y", "-f", "lavfi", "-i", "color=black:s=100x100:d=0.5",
            "-c:v", "libx264", "-t", "0.5", out_path
        ]
        env = {"PATH": "/Users/chanho/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin"}

        r = subprocess.run(cmd, capture_output=True, env=env, timeout=30)

        if r.returncode == 0 and Path(out_path).exists():
            size = Path(out_path).stat().st_size
            os.unlink(out_path)
            return True, f"렌더 성공 ({size}B)", {"output_size": size}
        os.unlink(out_path) if Path(out_path).exists() else None
        return False, "렌더 실패", None
    except Exception as e:
        return False, str(e), None

# === 예측 경고 ===

def predict_elevenlabs():
    """ElevenLabs 소진 예측"""
    try:
        key_file = SECRETS / "elevenlabs.json"
        key = json.loads(key_file.read_text()).get("api_key", "")
        req = urllib.request.Request(
            "https://api.elevenlabs.io/v1/user",
            headers={"xi-api-key": key}
        )
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())

        sub = data.get("subscription", {})
        used = sub.get("character_count", 0)
        limit = sub.get("character_limit", 1)
        remaining = limit - used

        # 일주일 평균 사용량 추정 (현재 사용량 기준)
        # 리셋 주기 모르니까 보수적으로
        if remaining < 10000:
            return "위험", f"남은 글자 {remaining:,}자 — 곧 소진"
        elif remaining < 50000:
            return "주의", f"남은 글자 {remaining:,}자"
        return "양호", f"남은 글자 {remaining:,}자"
    except:
        return "확인불가", ""

# === 리포트 생성 ===

def generate_report(results, predictions):
    """주간 리포트 생성"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# 주간 전사 체크 리포트",
        f"**생성:** {ts}",
        "",
        "## 브릿지 테스트 결과",
        "",
        "| 서비스 | 상태 | 결과 |",
        "|---|---|---|",
    ]

    for name, (ok, msg, _) in results.items():
        status = "✅" if ok else "❌"
        lines.append(f"| {name} | {status} | {msg} |")

    lines.extend([
        "",
        "## 예측 경고",
        "",
        "| 항목 | 상태 | 메모 |",
        "|---|---|---|",
    ])

    for name, (status, msg) in predictions.items():
        emoji = {"양호": "✅", "주의": "⚠️", "위험": "🚨", "확인불가": "❓"}.get(status, "❓")
        lines.append(f"| {name} | {emoji} {status} | {msg} |")

    lines.extend([
        "",
        "---",
        f"*자동 생성됨*",
    ])

    report = "\n".join(lines)
    with open(REPORT_FILE, "w") as f:
        f.write(report)

    return report

# === 메인 ===

def run_weekly():
    """주간 체크 실행"""
    log("=" * 60)
    log("🔬 주간 전사 시뮬레이션 체크 시작")

    # 브릿지 테스트
    results = {}

    log("  [인스타그램 API 테스트]")
    results["인스타그램"] = test_instagram_api()
    log(f"    → {'✅' if results['인스타그램'][0] else '❌'} {results['인스타그램'][1]}")

    log("  [ElevenLabs API 테스트]")
    results["ElevenLabs"] = test_elevenlabs_api()
    log(f"    → {'✅' if results['ElevenLabs'][0] else '❌'} {results['ElevenLabs'][1]}")

    log("  [Gemini API 테스트]")
    results["Gemini"] = test_gemini_api()
    log(f"    → {'✅' if results['Gemini'][0] else '❌'} {results['Gemini'][1]}")

    log("  [Google Drive 테스트]")
    results["Google Drive"] = test_drive_api()
    log(f"    → {'✅' if results['Google Drive'][0] else '❌'} {results['Google Drive'][1]}")

    log("  [ffmpeg 렌더 테스트]")
    results["ffmpeg"] = test_ffmpeg_render()
    log(f"    → {'✅' if results['ffmpeg'][0] else '❌'} {results['ffmpeg'][1]}")

    # 예측
    predictions = {}

    log("  [ElevenLabs 소진 예측]")
    predictions["ElevenLabs 잔여"] = predict_elevenlabs()
    log(f"    → {predictions['ElevenLabs 잔여'][0]}: {predictions['ElevenLabs 잔여'][1]}")

    # 리포트 생성
    report = generate_report(results, predictions)
    log(f"  리포트 생성: {REPORT_FILE}")

    # 문제 집계
    problems = [name for name, (ok, _, _) in results.items() if not ok]
    warnings = [name for name, (status, _) in predictions.items() if status in ["주의", "위험"]]

    if problems:
        log(f"❌ 실패: {', '.join(problems)}")
    if warnings:
        log(f"⚠️ 주의: {', '.join(warnings)}")
    if not problems and not warnings:
        log("✅ 전체 정상")

    log("=" * 60)
    return len(problems) == 0

if __name__ == "__main__":
    import sys
    success = run_weekly()
    sys.exit(0 if success else 1)
