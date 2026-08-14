#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""싱크 검사 (재작성 2026-08-14)

원본 소실로 _ROOMS_LOG 기록 기반 복원

검사 항목:
- 오디오 48kHz (96kHz는 FAIL)
- 스테레오 채널

사용법:
    python3 scripts/싱크검사.py <영상.mp4>
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("사용법: 싱크검사.py <영상.mp4>")
        return 1

    video = Path(sys.argv[1])
    if not video.exists():
        print(f"영상 없음: {video}")
        return 1

    # 오디오 정보 추출
    probe = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=sample_rate,channels",
        "-of", "json", str(video)
    ], text=True)

    streams = json.loads(probe).get("streams", [])
    if not streams:
        print("❌ 오디오 스트림 없음")
        return 1

    audio = streams[0]
    sample_rate = int(audio.get("sample_rate", 0))
    channels = int(audio.get("channels", 0))

    print(f"샘플레이트: {sample_rate} Hz")
    print(f"채널: {channels}")

    fails = []

    # 48kHz 검사
    if sample_rate != 48000:
        fails.append(f"샘플레이트 {sample_rate}Hz — 48kHz 필요")

    # 스테레오 검사
    if channels != 2:
        fails.append(f"채널 {channels} — 스테레오(2) 필요")

    if fails:
        print("\n❌ FAIL")
        for f in fails:
            print(f"  - {f}")
        return 1

    print("\n✅ PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
