# -*- coding: utf-8 -*-
"""단발매니펌 5장 낙타 캐러셀 빌드 — 문안은 차노 8/16 구술 원문."""
import subprocess, sys, pathlib
sys.path.insert(0, "scripts/cards")
from PIL import Image
import nakta_post as NP

SRC = pathlib.Path("_clips_pool/단발매니펌")
OUT = pathlib.Path("_out/얼굴납작_조각커트__N"); OUT.mkdir(parents=True, exist_ok=True)
TMP = pathlib.Path("_tmp/_danbal_frames"); TMP.mkdir(parents=True, exist_ok=True)

# (클립, 프레임초, 크롭 세로중심 0~1, top, 문안)
PLAN = [
 ("IMG_2721.MOV", 1.35, 0.42, 0.06,
   [("설정","거울 봤을 때, 머리가 혹은 얼굴이 납작해 보이지 않나요?"),
    ("결론","커트 문제일 확률이 99%입니다.")]),
 ("IMG_2720.MOV", 7.80, 0.45, 0.62,
   [("설정","동양인의 두상은 대부분 납작하기때문에"),
    ("결론","이점에 유의하여 커트하면 충분히 보완 할 수 있습니다.")]),
 ("IMG_2724.MOV", 0.90, 0.40, 0.70,
   [("설정","그래서 두상, 헤어를 조각함으로써"),
    ("시안","얼굴의 단점은 가리고 장점은 커버합니다.")]),
 ("IMG_2725.MOV", 3.20, 0.42, 0.05,
   [("설정","똑같은 단발이라도"),
    ("결론","이부분을 고려한 단발과 아닌 단발은 움직일때 다릅니다.")]),
 ("quality_restoration_20260816133521220.mp4", 1.30, 0.45, 0.66,
   [("시안","사진으로는 안 보입니다."),
    ("결론","움직여야 보이거든요.")]),
]

def grab(clip, t, out):
    subprocess.run(["ffmpeg","-v","error","-ss",str(t),"-i",str(SRC/clip),
                    "-frames:v","1","-y",str(out)], check=True)

def crop45(p, center):
    im = Image.open(p).convert("RGB")
    w, h = im.size
    th = int(w / 0.8)                      # 4:5
    if th > h:                             # 가로가 넓으면 폭을 깎는다
        tw = int(h * 0.8); x = (w - tw)//2
        im = im.crop((x, 0, x+tw, h))
    else:
        y = int(h*center - th/2); y = max(0, min(h-th, y))
        im = im.crop((0, y, w, y+th))
    return im.resize((1080, 1350), Image.LANCZOS)

for i, (clip, t, center, top, lines) in enumerate(PLAN, 1):
    f = TMP / f"f{i}.png"
    grab(clip, t, f)
    photo = crop45(f, center)
    NP.render(photo, lines, str(OUT / f"slide_{i}.png"), top=top)
    print(f"  {i}. {clip}  t={t}s  top={top}  → slide_{i}.png")
print("완료:", OUT)
