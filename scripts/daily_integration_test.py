#!/usr/bin/env python3
"""매일 통합 테스트 — 문제 발생 전 감지"""
import subprocess
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def test_dependencies():
    """의존성 테스트"""
    deps = [
        ("python3", "python3 --version"),
        ("node", "/opt/homebrew/bin/node --version"),
        ("ffmpeg", "/Users/chanho/.local/bin/ffmpeg -version"),
        ("faster-whisper", "python3 -c 'from faster_whisper import WhisperModel; print(\"OK\")'"),
    ]
    
    results = []
    for name, cmd in deps:
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
            ok = r.returncode == 0
        except:
            ok = False
        results.append((name, ok))
        log(f"{'✅' if ok else '⛔'} {name}")
    
    return all(ok for _, ok in results)

def test_connections():
    """연결 테스트"""
    try:
        r = subprocess.run(
            ["python3", "-m", "pipeline", "check"],
            capture_output=True, text=True, timeout=30, cwd=str(ROOT)
        )
        ok = "OK" in r.stdout
        log(f"{'✅' if ok else '⛔'} 연결")
        return ok
    except:
        log("⛔ 연결 테스트 실패")
        return False

def test_drive_download():
    """드라이브 다운로드 테스트"""
    try:
        r = subprocess.run(
            ["python3", "-c", "from shorts.gdrive import download_file; print('OK')"],
            capture_output=True, timeout=10, cwd=str(ROOT)
        )
        ok = r.returncode == 0
        log(f"{'✅' if ok else '⛔'} 드라이브")
        return ok
    except:
        return False

def test_tts():
    """TTS 테스트"""
    try:
        r = subprocess.run(
            ["python3", "-c", "from shorts.tts import load_credentials; load_credentials('secrets/elevenlabs.json'); print('OK')"],
            capture_output=True, timeout=10, cwd=str(ROOT)
        )
        ok = r.returncode == 0
        log(f"{'✅' if ok else '⛔'} TTS")
        return ok
    except:
        return False

def main():
    log("=" * 40)
    log("📋 매일 통합 테스트")
    
    results = []
    results.append(("의존성", test_dependencies()))
    results.append(("연결", test_connections()))
    results.append(("드라이브", test_drive_download()))
    results.append(("TTS", test_tts()))
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    log("=" * 40)
    log(f"결과: {passed}/{total} 통과")
    
    if passed < total:
        failed = [n for n, ok in results if not ok]
        log(f"⛔ 실패: {failed}")
        return 1
    
    log("✅ 전체 통과")
    return 0

if __name__ == "__main__":
    exit(main())
