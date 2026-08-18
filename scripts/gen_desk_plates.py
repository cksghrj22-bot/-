#!/usr/bin/env python3
"""무드북용 실사 책상 배경 생성 — 나노바나나(gemini-2.5-flash-image)"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from gemini_image import generate_image

OUT = Path(__file__).parent.parent / "_out" / "무드보드_보이드태그" / "plates"
OUT.mkdir(parents=True, exist_ok=True)

BASE = ("Photorealistic photograph, wide horizontal 3:2 landscape composition. "
        "A worn dark wooden desk at 3am in a small studio room, shot slightly from above. "
        "Dim warm tungsten lamp light from the upper left, deep shadows, thick cigarette smoke "
        "hanging in the air making the room hazy and slightly out of focus in the background. "
        "Grainy, high ISO, unretouched, amateur snapshot feel, not glossy, not luxury, "
        "no people, no text, no letters. Muted desaturated colors. "
        "The centre of the desk is EMPTY so that photo prints can be placed there later. ")

PLATES = {
 "plate_01_open.jpg": BASE + "On the desk: a single unopened cold beer can with condensation, a full ashtray with two cigarette butts, faint amber beer ring stains on the wood.",
 "plate_02_mid.jpg":  BASE + "On the desk: a half-empty beer can, a glass ashtray overflowing with ash and four crushed cigarette butts, scattered grey ash on the wood, several overlapping wet beer ring stains.",
 "plate_03_crush.jpg":BASE + "On the desk: a badly CRUSHED and flattened aluminium beer can lying on its side, dented and twisted, spilled beer puddle, an ashtray knocked over with ash spilling out, many overlapping ring stains, crumpled paper.",
 "plate_04_dawn.jpg": BASE + "Cold pale blue dawn light replacing the tungsten lamp, smoke thinner and settling. On the desk: a crushed beer can, a mountain of ash and cigarette butts in the ashtray, dried beer stains.",
}

for name, prompt in PLATES.items():
    p = OUT / name
    try:
        generate_image(prompt, str(p))
        print(f"✅ {name}  {p.stat().st_size//1024}KB")
    except Exception as e:
        print(f"⛔ {name}  {e}")
print("→", OUT)
