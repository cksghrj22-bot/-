#!/usr/bin/env python3
"""결이 이야기 만화 파이프라인 v2 — 구조(대본) 기반 + 레퍼런스 첨부 생성.

v1(`manga_pipeline.py`)의 실패 원인을 전부 고친 판.
  ① v1은 인자로 받은 대본을 **어떤 프롬프트에도 넣지 않았다** (parse_script_to_panels가 통째로 버림)
     → 제목만 '착한곱슬편'이고 내용은 매듭 만화가 나왔다.
  ② 레퍼런스 이미지를 안 붙였다 → 결이가 '주황 머리카락 소녀'로 매 컷 다르게 나왔다.
  ③ 3:4 지정·이미지 안 글자 금지가 프롬프트에 없었다 → 1024 정사각 + 영어 글자 범벅.

v2는 구조 JSON(컷별 대본·프롬프트·문구)을 읽어서 생성하고,
①편 정본 3장을 레퍼런스로 붙인다. 문구는 그림에 넣지 않고 make_card.py가 얹는다.

사용:
    python3 scripts/manga_pipeline2.py content/manga/착한곱슬편_구조.json
    python3 scripts/manga_pipeline2.py <구조.json> --only 3      # 3번 컷만 재생성
    python3 scripts/manga_pipeline2.py <구조.json> --no-assemble # 원본만
"""
import argparse, base64, io, json, subprocess, sys, time, urllib.error, urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SECRETS = ROOT / "secrets"
MODEL = "gemini-2.5-flash-image"

# ── 레퍼런스 정본 (①편 「매듭 편」) — 이게 캐릭터 일관성의 전부다
REFS = [
    ROOT / "_out/매듭이야기_final_복고텍스트/c2_매듭.png",    # 결이 생김새
    ROOT / "_out/매듭이야기_final_복고텍스트/c1_표지.png",    # 보리 얼굴·살롱
    ROOT / "_out/매듭이야기_final_복고텍스트/c6_공간.png",    # 화풍·색감
]

CHARACTER_LOCK = """\
첨부한 3장은 내가 연재 중인 한국 미용만화 '결이 이야기' 1편의 카드다.
같은 시리즈의 다음 편이다. 첨부의 캐릭터와 화풍을 그대로 유지해서 그려라.

[화풍] 정겨운 옛 한국 만화 감성, 따뜻한 크림색 종이 질감, 손맛 있는 잉크 선, 부드러운 수채 채색.
       색은 크림색 배경 · 갈색 톤 · 결이의 주황, 이 세 가지로만 간다. 플랫 벡터 스티커 톤 금지.
[결이] 결이의 몸은 밝은 주황과 머스타드색 '이어폰 줄'이 동그랗게 모인 덩어리다.
       사람 머리카락이 아니다. 사람 소녀가 아니다.
       줄 끝의 이어버드 두 개가 팔처럼 뻗어 있고, 아래에 아주 짧은 다리 두 개,
       덩어리 한가운데에 크림색 둥근 얼굴이 작게 박혀 있다. 사람 팔·사람 다리·사람 손 금지.
       크기와 비율과 얼굴 위치를 매 컷 똑같이 유지하고, 표정만 바꾼다.
       결이는 머리 밖에 떠 있는 마스코트가 아니라 머리카락의 뿌리나 결 속에 연결되어 있다.
[보리] 첨부의 손님과 같은 얼굴. 수수한 20~30대 여성, 자연스러운 긴 갈색 머리. 미인 보정 금지.
[차노] 얼굴은 그리지 않는다. 손과 소매만. 손가락 다섯 개.

[전 컷 금지]
- 이미지 안에 글자·문자·숫자·로고·말풍선 텍스트를 절대 넣지 않는다. 문구는 나중에 따로 얹는다.
- 결이와 보리 말고 다른 것에 얼굴을 붙이지 않는다. 아이롱·약통·빗은 얼굴 없는 사물이다.
- 매끈한 3D·광고 사진 톤, 과한 보정, 공포스러운 두피 묘사, 사람 머리 위에 마스코트 얹기.
- 세로 3:4 구도를 유지한다.
"""


def api_key() -> str:
    return json.loads((SECRETS / "gemini.json").read_text())["api_key"]


def ref_parts(max_side: int = 1024) -> list:
    """레퍼런스 이미지를 줄여서 inline_data 파트로."""
    parts = []
    for p in REFS:
        if not p.exists():
            print(f"  ⚠️ 레퍼런스 없음: {p}")
            continue
        im = Image.open(p).convert("RGB")
        r = max_side / max(im.size)
        if r < 1:
            im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=88)
        parts.append({"inline_data": {"mime_type": "image/jpeg",
                                      "data": base64.b64encode(buf.getvalue()).decode()}})
    if not parts:
        sys.exit("레퍼런스가 하나도 없다. 캐릭터가 깨지므로 생성하지 않는다.")
    return parts


def generate(prompt: str, out_path: Path, refs: list, tries: int = 3) -> bool:
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={api_key()}")
    payload = {
        "contents": [{"parts": refs + [{"text": prompt}]}],
        "generationConfig": {"imageConfig": {"aspectRatio": "3:4"}},
    }
    for n in range(tries):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                         headers={"Content-Type": "application/json"})
            resp = json.loads(urllib.request.urlopen(req, timeout=180).read())
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:300]
            if e.code == 400 and "imageConfig" in body:
                payload.pop("generationConfig", None)   # 구버전 API 대응
                continue
            print(f"  ❌ HTTP {e.code}: {body}")
            time.sleep(4)
            continue
        for part in resp.get("candidates", [{}])[0].get("content", {}).get("parts", []):
            data = part.get("inlineData") or part.get("inline_data")
            if data:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(base64.b64decode(data["data"]))
                return True
        print(f"  ❌ 이미지 없음 (시도 {n+1}/{tries})")
        time.sleep(4)
    return False


def assemble(panel: dict, raw: Path, out: Path):
    """make_card.py 로 1080x1350 + 문구."""
    cmd = ["python3", str(ROOT / "scripts/cards/make_card.py"),
           "--img", str(raw), "--out", str(out)]
    if panel.get("bleed"):
        cmd.append("--bleed")
    for k in ("badge", "title", "head", "body", "pin"):
        if panel.get(k):
            cmd += [f"--{k}", panel[k]]
    for label in panel.get("label", []):
        cmd += ["--label", label]
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", help="구조 JSON 경로")
    ap.add_argument("--only", type=int, help="해당 번호 컷만 생성")
    ap.add_argument("--no-assemble", action="store_true")
    ap.add_argument("--skip-existing", action="store_true", help="원본이 이미 있으면 생성 건너뛰고 조립만")
    a = ap.parse_args()

    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    raw_dir = ROOT / spec["raw_dir"]
    out_dir = ROOT / spec["out_dir"]
    refs = ref_parts()
    print(f"📎 레퍼런스 {len(refs)}장 첨부 · 「{spec['title']}」 {len(spec['panels'])}컷")

    ok = 0
    for panel in spec["panels"]:
        n = panel["n"]
        if a.only and n != a.only:
            continue
        raw = raw_dir / f"c{n}.png"
        if a.skip_existing and raw.exists():
            print(f"⏭  c{n} {panel['name']} — 원본 있음, 조립만")
            if not a.no_assemble:
                assemble(panel, raw, out_dir / f"c{n}.png")
            ok += 1
            continue
        prompt = f"{CHARACTER_LOCK}\n\n[이 컷]\n{panel['prompt']}"
        # 악성곱슬 통합편 실생성 검수에서 반복된 오류를 컷별로 잠근다.
        if "악성곱슬" in spec.get("title", ""):
            corrections = {
                3: "직파모는 위쪽 반은 곳고 아래쪽 반은 확실한 완만한 물결이어야 한다. 세 다발은 아래쪽 프레임 밖으로 계속 이어져 끝이 화면에 보이지 않게 해라. J자, C자, 고리, 고리 모양 머리끝을 절대 그리지 마라. 사람, 결이 마스코트, 얼굴, 장식은 아예 등장시키지 마라.",
                4: "옆얼굴과 뒷모습이 함께 보이는 3/4 후면으로 그려라. 축모는 반드시 두 구역이 동시에 보여야 한다. 첫째는 화면 왼쪽에 노출된 귀의 바로 앞, 관자놀이 헤어라인. 둘째는 머리카락 가장 아래쪽 목덜미 헤어라인. 손은 두 구역을 가리지 말고 사이 머리만 들어라. 뒷머리 중앙에는 축모를 그리지 마라. 결이 마스코트, 얼굴 붙은 머리 장식, 주황색 캐릭터는 아예 등장시키지 마라.",
                6: "좌우 인물 위에는 아무 라벨도 두지 마라. Before, After를 포함한 모든 글자와 숫자를 그리지 마라. 머리카락이나 몸에 얼굴 붙인 장식, 결이 마스코트, 주황색 캐릭터, 꽃, 장미를 아예 등장시키지 마라. 좌우 구분은 얇은 세로선만 사용해라.",
            }
            if n in corrections:
                prompt += f"\n\n[추가 절대 교정]\n{corrections[n]}"
        print(f"🎨 c{n} {panel['name']} …")
        if not generate(prompt, raw, refs):
            print(f"  ❌ c{n} 실패")
            continue
        print(f"  ✅ {raw}")
        if not a.no_assemble:
            assemble(panel, raw, out_dir / f"c{n}.png")
        ok += 1
        time.sleep(3)

    print(f"\n원본 {raw_dir}\n완성 {out_dir}\n성공 {ok}")


if __name__ == "__main__":
    main()
