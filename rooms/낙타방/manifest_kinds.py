#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""매니페스트 스탬 구분기 — 이 방 안에서도 줄기끼리 절대 섞이지 않게 (2026-08-15 차노 확정)

> "에이엠톤 매니페스트랑 낙타식 매니페스트는 전혀 달라 구분해"
> "방안에서도 다른 매니페스트 스탬끼리는 정확히 구분해서 섞이지 않도록하기"

모든 렌더러는 파일을 직접 json.load 하지 않는다. **반드시 load(path, expect=...) 를 통과시킨다.**
`kind` 가 없거나 다르면 렌더 자체를 막는다. `kind` 가 맞아도 **그 스탬의 필수/금지 키**를 검사해
다른 스탬의 파일을 이름만 바꿔 넣은 경우까지 잡는다.
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

KINDS = {
    "nakta_subtitle_bar_v1": {
        "이름": "① 낙타형 자막바",
        "폴더": "content/nakta/",
        "렌더러": "rooms/낙타방/nakta_from_manifest.py",
        "규격": "knowledge/규격_낙타형자막바_컨텐츠_정본.md",
        "캔버스": (1080, 1350),
        "필수": ["kind", "out", "slides"],
        "금지": ["cards", "segments", "phrases"],       # 에이엠톤/쇼츠 파일이면 여기서 걸린다
        "항목키": "slides",
        "항목필수": ["src", "lines"],
        "항목금지": ["line1", "line2", "accent", "accent2"],
    },
    "amton_bottomleft_v1": {
        "이름": "③ 에이엠톤 좌하단 두 줄",
        "폴더": "content/amton/",
        "렌더러": "rooms/낙타방/amton_post.py",
        "규격": "knowledge/규격_에이엠톤식_좌하단두줄_v1.md",
        "캔버스": (1080, 1350),
        "필수": ["kind", "out", "cards", "defaults"],
        "금지": ["slides", "segments", "phrases"],
        "항목키": "cards",
        "항목필수": ["src", "line1"],
        "항목금지": ["lines", "role", "start", "duration"],
    },
}

# 이 방 것이 아닌 스탬 — 들어오면 방을 잘못 찾은 것
남의방 = {
    "segments": "방2 쇼츠(`content/manifests/`) 매니페스트로 보인다 — 유튜브쇼츠방 것이다.",
    "phrases":  "방2 쇼츠 대본 매니페스트로 보인다 — 유튜브쇼츠방 것이다.",
}


class ManifestError(SystemExit):
    pass


def _die(msg):
    raise ManifestError("⛔ 매니페스트 거부\n   " + msg.replace("\n", "\n   "))


def load(path, expect):
    """expect 스탬이 아니면 렌더를 막는다. 성공하면 dict 반환."""
    if expect not in KINDS:
        _die(f"모르는 스탬: {expect}. 등록된 것: {list(KINDS)}")
    spec = KINDS[expect]
    p = pathlib.Path(path)
    if not p.exists():
        _die(f"파일 없음: {p}")
    try:
        m = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        _die(f"JSON 아님: {p}\n{e}")

    kind = m.get("kind") or m.get("format")      # format 은 구버전 키
    if kind is None:
        for k, why in 남의방.items():
            if k in m:
                _die(f"{p.name} 에 `kind` 가 없다.\n{why}")
        _die(f"{p.name} 에 `kind` 가 없다. 맨 위에 \"kind\": \"{expect}\" 를 적는다.\n"
             f"이 방 스탬: " + " / ".join(f"{k} = {v['이름']}" for k, v in KINDS.items()))
    if kind != expect:
        other = KINDS.get(kind)
        _die(f"{p.name} 는 「{other['이름'] if other else kind}」 매니페스트다. "
             f"이 렌더러는 「{spec['이름']}」 전용.\n"
             + (f"→ {other['렌더러']} 로 돌려라. 폴더도 {other['폴더']} 다." if other else
                f"→ 등록되지 않은 스탬: {kind}"))

    # 스탬은 맞다고 적혀 있어도 내용이 다른 스탬이면 잡는다
    for k in spec["금지"]:
        if k in m:
            owner = next((v["이름"] for v in KINDS.values() if k == v["항목키"]), None)
            _die(f"{p.name} 는 kind={kind} 인데 `{k}` 키가 있다"
                 + (f" — 「{owner}」 의 키다. 스탬이 섞였다." if owner else " — 이 스탬에 없는 키다."))
    for k in spec["필수"]:
        if k not in m:
            _die(f"{p.name} 에 필수 키 `{k}` 가 없다. (kind={kind})")

    items = m.get(spec["항목키"]) or []
    if not items:
        _die(f"{p.name} 의 `{spec['항목키']}` 가 비었다.")
    for i, it in enumerate(items, 1):
        for k in spec["항목금지"]:
            if k in it:
                _die(f"{p.name} {spec['항목키']}[{i}] 에 `{k}` 가 있다 — 다른 스탬의 항목 형식이다.")
        for k in spec["항목필수"]:
            if k not in it:
                _die(f"{p.name} {spec['항목키']}[{i}] 에 필수 키 `{k}` 가 없다.")

    cw, ch = spec["캔버스"]
    cv = m.get("canvas", {"w": cw, "h": ch})
    if (cv.get("w"), cv.get("h")) != (cw, ch):
        _die(f"{p.name} 캔버스 {cv.get('w')}x{cv.get('h')} — 「{spec['이름']}」 은 {cw}x{ch} 다.")

    # 폴더 규율은 경고만 (작업 중 임시 위치 허용)
    if spec["폴더"] not in str(p).replace("\\", "/"):
        print(f"⚠ {p.name} 이 {spec['폴더']} 밖에 있다. 스탬별 폴더를 지켜라.", file=sys.stderr)
    return m


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        for k, v in KINDS.items():
            print(f"\n{v['이름']}\n  kind    {k}\n  폴더    {v['폴더']}\n  렌더러  {v['렌더러']}\n  항목키  {v['항목키']}")
        raise SystemExit(0)
    # 진단 모드: 이 파일이 무슨 스탬인지 알려준다
    m = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    k = m.get("kind") or m.get("format")
    print(f"kind={k}", KINDS.get(k, {}).get("이름", "(등록 안 됨)"))
