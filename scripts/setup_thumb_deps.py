#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""썸네일 의존성 설치 — 맥(remote_cmd_watch)에 opencv 를 깐다.

왜: 썸네일 프레임 고르기가 cv2(선명도·인물덩어리·얼굴검출)를 쓴다.
    맥 파이썬에 cv2 가 없어서 make_thumb.py 가 죽었다.
    opencv-python 에는 얼굴 검출용 haarcascade 도 같이 들어온다.
사용: {"cmd":"python_script","args":["setup_thumb_deps.py"]}
"""
import subprocess, sys

PKGS = ["numpy", "opencv-python-headless"]


def try_install(extra):
    cmd = [sys.executable, "-m", "pip", "install", "--quiet"] + extra + PKGS
    print("$", " ".join(cmd), flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout[-1500:] or "", flush=True)
    if r.returncode:
        print("[stderr]", r.stderr[-1500:], flush=True)
    return r.returncode == 0


def main():
    ok = try_install([]) or try_install(["--user"]) or try_install(["--break-system-packages"])
    if not ok:
        print("⛔ 설치 실패"); return 1
    import importlib, os
    for m in ("numpy", "cv2"):
        importlib.invalidate_caches()
    import cv2, numpy
    casc = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    print("✅ cv2", cv2.__version__, "numpy", numpy.__version__, flush=True)
    print("✅ 얼굴모델", casc, os.path.exists(casc), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
