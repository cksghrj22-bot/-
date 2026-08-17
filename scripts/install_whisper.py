#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""faster-whisper 설치 + 모델 내려받기. 샌드박스 밖(remote_cmd_watch)에서 돌려야 한다.
없으면 shorts_gate 의 S8(실측 싱크)이 모든 렌더를 무조건 탈락시킨다."""
import subprocess, sys

def sh(argv):
    print("$", " ".join(argv), flush=True)
    r = subprocess.run(argv, capture_output=True, text=True, timeout=540)
    print((r.stdout or "")[-1500:], (r.stderr or "")[-800:], flush=True)
    return r.returncode

rc = sh([sys.executable, "-m", "pip", "install", "-q", "faster-whisper"])
if rc != 0:
    rc = sh([sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", "faster-whisper"])
if rc != 0:
    rc = sh([sys.executable, "-m", "pip", "install", "-q", "--user", "faster-whisper"])
try:
    from faster_whisper import WhisperModel
    print("import OK — 모델 내려받는 중(small)", flush=True)
    WhisperModel("small", device="cpu", compute_type="int8")
    print("✅ faster-whisper 준비 완료", flush=True)
    sys.exit(0)
except Exception as e:
    print("⛔ 실패: %s: %s" % (type(e).__name__, e), flush=True)
    sys.exit(1)
