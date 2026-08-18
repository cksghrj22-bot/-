#!/usr/bin/env python3
"""무드북 배경 — 검은 하드보드지 질감 (나노바나나)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from gemini_image import generate_image
OUT = Path(__file__).parent.parent / "_out" / "무드보드_보이드태그" / "board"
OUT.mkdir(parents=True, exist_ok=True)

B = ("A photograph of a large black mat board lying flat on a studio table, camera directly "
     "above, the board fills the whole frame. Soft window light rakes across it from the left "
     "so the paper texture catches the light. You can see the fibre, the tooth, tiny lighter "
     "flecks and a little dust. Matte black cardstock, nothing placed on it, no writing. "
     "Shot on a 50mm lens, natural, unretouched. ")

P = {
 "board_a.jpg": B + "Fine tooth, like museum mount board.",
 "board_b.jpg": B + "Coarser fibre with visible small lighter flecks, like recycled black craft board.",
 "board_c.jpg": B + "Very fine smooth grain with faint dust and micro scratches, like a black presentation board that has been handled.",
}
for n,p in P.items():
    try:
        generate_image(p, str(OUT/n)); print("✅", n, (OUT/n).stat().st_size//1024, "KB")
    except Exception as e:
        print("⛔", n, type(e).__name__, e)
