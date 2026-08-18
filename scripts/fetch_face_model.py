#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""얼굴검출 모델(YuNet) 내려받기 — 썸네일 프레임 고르기 의존성.

왜: OpenCV 5 에는 옛 haarcascade 데이터가 빠졌다. 썸네일은 '얼굴이 보이는 컷'이라야 하므로
    검출기가 필요하다. YuNet(약 230KB, OpenCV 공식 zoo)을 assets/models/ 에 둔다.
사용: {"cmd":"python_script","args":["fetch_face_model.py"]}
"""
import glob, os, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DST  = ROOT / "assets/models"
URLS = [
    ("face_detection_yunet_2023mar.onnx",
     "https://raw.githubusercontent.com/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"),
]

def main():
    DST.mkdir(parents=True, exist_ok=True)
    # 이미 맥 어딘가에 haarcascade 가 있으면 그걸 쓴다
    found = []
    for p in ("/opt/homebrew/**/haarcascade_frontalface*.xml",
              "/usr/local/**/haarcascade_frontalface*.xml"):
        found += glob.glob(p, recursive=True)[:2]
    if found:
        print("기존 haarcascade 발견:", *found, sep="\n  ", flush=True)

    for name, url in URLS:
        out = DST / name
        if out.exists() and out.stat().st_size > 100_000:
            print("이미 있음:", out.name, out.stat().st_size, flush=True); continue
        req = urllib.request.Request(url, headers={"User-Agent": "atnown-pipeline"})
        data = urllib.request.urlopen(req, timeout=120).read()
        out.write_bytes(data)
        print("✅ 받음:", out.name, len(data), "바이트", flush=True)

    import cv2
    m = str(DST / URLS[0][0])
    d = cv2.FaceDetectorYN.create(m, "", (320, 320))
    print("✅ YuNet 로드 OK", cv2.__version__, flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
