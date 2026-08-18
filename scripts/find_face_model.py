#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""맥에 얼굴검출 모델이 있는지 훑는다.

⛔ 홈 전체(`~/**`) 재귀 glob 금지 — 실행기를 600초 타임아웃까지 물어버렸다(2026-08-19).
   훑을 곳은 site-packages 같은 **좁은 경로**로 못 박는다."""
import glob, os, cv2
pats = ["/opt/homebrew/**/haarcascade_frontalface*.xml",
        "/usr/local/**/haarcascade_frontalface*.xml",
        "/opt/homebrew/**/face_detection_yunet*.onnx"]
hit = []
for p in pats:
    hit += glob.glob(p, recursive=True)[:3]
print("cv2", cv2.__version__)
print("data dir:", getattr(cv2, "data", None) and cv2.data.haarcascades)
print("찾은 것:", *hit, sep="\n  ") if hit else print("찾은 것: 없음")
