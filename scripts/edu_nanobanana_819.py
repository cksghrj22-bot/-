#!/usr/bin/env python3
"""
교육디렉터방 · 8/19 L5 「일본 이미지분류체계」 — 나노바나나 이미지 생성 + PPTX 재빌드

왜 이 스크립트가 따로 있나:
  코워크(클라우드) 샌드박스는 generativelanguage.googleapis.com 이 프록시에서 막힌다.
  그래서 이미지 생성은 **네트워크가 있는 맥에서** 이걸 돌린다.

쓰는 법 (맥):
    cd ~/atnown-content-pipeline
    python3 scripts/edu_nanobanana_819.py            # 이미지 4장 생성 + 덱 재빌드
    python3 scripts/edu_nanobanana_819.py --only-img # 이미지만
    python3 scripts/edu_nanobanana_819.py --only-deck# 덱만 (이미지 이미 있을 때)

화풍: 따뜻한 크림 종이 · 연필/옅은 잉크 · 정면 · 세 도판의 얼굴을 동일하게(비교용) · 이미지 안 글자 금지
"""
import argparse, base64, json, subprocess, sys, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECRETS = ROOT / "secrets"
DECK_DIR = ROOT / "content/교육/2026-08-19_일본_이미지분류체계"
IMG_DIR = DECK_DIR / "img"
MODEL = "gemini-2.5-flash-image"        # = 나노바나나

# 모든 프롬프트에 공통으로 붙는 화풍 잠금줄 (매번 지어내지 말 것 — 정본이다)
STYLE = (
    "Soft editorial illustration in graphite pencil and light ink wash on warm cream paper. "
    "Gentle linework, quiet shading, muted monochrome with a faint warm beige tone. "
    "A single Korean woman seen from the front, calm neutral expression, head and shoulders, "
    "the same face and proportions across the whole set so the images can be compared side by side. "
    "Plain warm cream background, generous empty space, no props, no accessories. "
    "ABSOLUTELY NO text, letters, words, numbers, watermark or signature anywhere in the image. "
    "No color other than cream paper and soft grey-black pencil."
)

PROMPTS = {
    # 표지: 인물 없이, 좌표 개념을 나타내는 조용한 추상 도판
    "nb_cover.png": (
        "A quiet abstract illustration of a two-axis coordinate plane: one horizontal line and one "
        "vertical line crossing at the centre, two faint concentric circles around the crossing point, "
        "and a few small dots scattered in the quadrants. Graphite pencil on warm cream paper, "
        "very minimal, lots of empty space, vertical 3:4 composition. "
        "ABSOLUTELY NO text, letters, words or numbers anywhere in the image."
    ),
    # 도판 1 — 세미롱 / 매끈 / 끝 안말음 / 시스루 앞머리
    "nb_case1.png": (
        "Hairstyle reference drawing: semi-long hair reaching just below the shoulders, smooth glossy "
        "texture, the ends curving gently inward toward the neck, light wispy see-through fringe across "
        "the forehead. Square composition, head and shoulders, front view. " + STYLE
    ),
    # 도판 2 — 세미~롱 / 매끈 / 스트레이트 / 앞머리 없음
    "nb_case2.png": (
        "Hairstyle reference drawing: long straight hair falling well past the shoulders, very smooth and "
        "sleek, blunt even ends, centre parting with no fringe, hair tucked behind so the forehead is fully "
        "visible. Square composition, head and shoulders, front view. " + STYLE
    ),
    # 도판 3 — 단발 / 결 살아있는 질감 / 끝 바깥 방향 / 일자 앞머리
    "nb_case3.png": (
        "Hairstyle reference drawing: short bob ending at the jawline, visibly textured and slightly choppy, "
        "the ends flicking outward away from the face, heavy straight-across blunt fringe covering the "
        "eyebrows. Square composition, head and shoulders, front view. " + STYLE
    ),
}


def api_key() -> str:
    return json.loads((SECRETS / "gemini.json").read_text())["api_key"]


def generate(prompt: str, out: Path) -> bool:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={api_key()}"
    req = urllib.request.Request(
        url,
        data=json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=240).read())
    except urllib.error.HTTPError as e:
        print(f"   ❌ HTTP {e.code}: {e.read()[:400].decode(errors='replace')}")
        return False
    except Exception as e:
        print(f"   ❌ {type(e).__name__}: {e}")
        return False

    for cand in resp.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            if "inlineData" in part:
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(base64.b64decode(part["inlineData"]["data"]))
                return True
    print(f"   ❌ 이미지 없음: {json.dumps(resp)[:300]}")
    return False


def make_images() -> int:
    ok = 0
    for name, prompt in PROMPTS.items():
        out = IMG_DIR / name
        print(f"🎨 {name} …")
        if generate(prompt, out):
            print(f"   ✅ {out.relative_to(ROOT)}  ({out.stat().st_size // 1024} KB)")
            ok += 1
    return ok


def ensure_pptxgenjs() -> bool:
    """맥 리포에는 pptxgenjs 가 없다(플레이라이트만 있음). 없으면 깔고 간다."""
    if (ROOT / "node_modules/pptxgenjs").exists():
        return True
    print("📦 pptxgenjs 없음 → npm i pptxgenjs …")
    r = subprocess.run(["npm", "i", "pptxgenjs"], cwd=str(ROOT), capture_output=True, text=True)
    if r.returncode != 0:
        print("   ❌ npm 실패:", (r.stderr or r.stdout)[-400:])
        return False
    print("   ✅ 설치 완료")
    return True


def build_deck() -> bool:
    js = DECK_DIR / "build_pptx.js"
    if not js.exists():
        print(f"❌ 빌드 스크립트 없음: {js}")
        return False
    if not ensure_pptxgenjs():
        return False
    env_cwd = str(DECK_DIR)
    r = subprocess.run(["node", str(js)], cwd=env_cwd, capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    return r.returncode == 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-img", action="store_true")
    ap.add_argument("--only-deck", action="store_true")
    a = ap.parse_args()

    made = 0
    if not a.only_deck:
        made = make_images()
        print(f"\n🎨 이미지 {made}/{len(PROMPTS)} 생성")
        if made < len(PROMPTS):
            print("⚠️  일부 실패 — 덱은 있는 이미지만 얹어서 빌드된다(4장 다 있어야 케이스 슬라이드가 붙는다)")

    if not a.only_img:
        print("\n📊 덱 재빌드 …")
        if not build_deck():
            sys.exit(1)
        print(f"✅ {DECK_DIR / 'L5_일본_이미지분류체계.pptx'}")
        print("   확인: 표지 우측 도판 / 「참고 도판」 슬라이드가 붙어 15장이 되었는지")
