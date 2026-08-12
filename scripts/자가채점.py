#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자가채점.py — 형 사고 문법으로 내 대본을 스스로 채점한다 (2026-08-12 신설)
이찬호: "매주 이런 피드백을 스스로 하라."
  python3 ~/atnown-trunk/scripts/자가채점.py <대본.txt>   한 편
  python3 ~/atnown-trunk/scripts/자가채점.py --주간          이번 주 전부
근거: 옵시디언 차노_사고_문법 · 차노_생각의흐름_기준점 · 차노_흐름차이_본질
"""
import os, sys, re, glob, json, datetime

PIPE = os.path.expanduser("~/atnown-content-pipeline")
OUT  = os.path.join(PIPE, "_reports"); os.makedirs(OUT, exist_ok=True)

# 형 재정의 은행 (차노_사고_문법 4번) — 여기서 꺼내 쓴다
BANK = ["숱치기는 공간 만들기", "볼륨은 모근의 각도", "레이어드는 움직임",
        "색은 스며듦", "어울림은 무드 밸런스", "펌은 순서", "커트는 생각",
        "교육은 파이프라인", "가치가 가격보다"]
# 이질결합 — 미용 밖 사물
OUTSIDE = ["옷장", "커피", "비행기", "삼각김밥", "얼음", "사진 보정", "노래", "가사",
           "제습기", "서점", "식당", "운동", "요리", "청소", "정리", "지도", "악기"]
# 금지어 (AI 말투)
BAN = ["이롭다", "유의미한", "본질적으로", "극대화", "최적화", "퀄리티", "솔루션",
       "다양한", "여러가지", "를 통해", "함으로써", "라고 할 수 있습니다", "인 것 같습니다"]

def score(txt, name=""):
    L = [l.strip() for l in re.split(r"(?<=[.?!])\s+", txt) if l.strip()]
    r = []
    def add(k, ok, note): r.append((k, ok, note))

    head = " ".join(L[:2])
    add("① 주인공 (누구 이야기인가)",
        bool(re.search(r"(분들?|사람|남자|여자|얼굴|머리|정수리|곱슬|시니어|손님)", head)),
        "첫 두 줄에 「누구 얘긴지」가 있어야 한다 (기준점 2번 · 키워드 1층)")
    add("② 공감 훅 / 통념",
        bool(re.search(r"(있으세요|있죠|하시죠|생각합니다|알고 계|다들|보세요)", " ".join(L[:4]))),
        "결론부터 말하지 않는다. 통념을 먼저 세운다")
    add("③ 재정의 「A가 아니라 B다」",
        bool(re.search(r"(아니라|말고|가 아니|는 아닙)", txt)),
        "형 콘텐츠의 심장. 없으면 그냥 설명이다")
    add("④ 이질결합 (미용 밖 사물)",
        any(w in txt for w in OUTSIDE),
        "카멜커피·비행기 각도·옷장처럼 밖에서 끌어와야 시야가 넓어진다")
    # ⑤ 철학화는 **매 편 강제하지 않는다** (2026-08-12 이찬호 정정)
    # 근거: 차노_흐름차이_본질 — "억지로 철학으로 꺾고 / 메시지 전하려고 이야기를 엮는다"
    # 숫자 근거: 상위편(볼륨리플펌 7,918 · 픽시컷 4,543)에 철학화 없음. 「당신의 100년」은 99회.
    # 대신 **억지 철학을 감점**한다 — 앞에서 안 한 얘기가 끝에 갑자기 튀어나오면 걸린다.
    tail = " ".join(L[-2:]); body = " ".join(L[:-2])
    BIG = ["인생", "삶", "결국 사람", "세상", "본질은", "철학"]
    급조 = [w for w in BIG if w in tail and w not in body]
    add("⑤ 억지 철학 없음",
        not 급조,
        "끝에 %s 이(가) 갑자기 나온다. 앞에서 안 한 얘기면 빼라 — 흐름이 먼저다" % ", ".join(급조))
    add("⑥ 판정형 되묻기로 닫기",
        L[-1].endswith("?") if L else False,
        "시청자가 자기 답을 내게 한다. 단정으로 닫으면 댓글이 없다")
    add("⑦ AI 말투 없음",
        not any(w in txt for w in BAN),
        "말은 되는데 뜻이 없는 단어들")
    add("⑧ 같은 문형 3회 미만",
        len(re.findall(r"아니라", txt)) < 4,
        "「~가 아니라 ~다」를 네 번 쓰면 기계가 쓴 것처럼 읽힌다")
    # 편의 종류를 먼저 정한다 — 시술편은 시술로 닫는 게 맞다
    시술 = any(w in txt for w in ["펌", "커트", "염색", "매직", "볼륨", "층", "숱", "드라이"])
    add("⑤-b 편의 종류",
        True,
        ("시술편 — 시술로 닫는 게 맞다. 철학화 안 봐도 된다" if 시술
         else "생각편 — 이때만 한 층 위로 올라간다"))
    n = len(re.sub(r"\s", "", txt))
    add("⑨ 길이 240~320자",
        240 <= n <= 320,
        "본문 %d자 · 예상 %.1f초 (÷7.4+4.2)" % (n, n / 7.4 + 4.2))
    used = [b for b in BANK if b.split()[0] in txt]
    add("⑩ 재정의 은행 사용",
        True, "쓴 것: %s" % (", ".join(used) if used else "없음 — 새로 만들었다면 ★ 표시해 형 확인"))
    return r

def show(name, txt):
    r = score(txt, name)
    bad = [x for x in r if not x[1]]
    print("\n■ %s — %d/%d 통과" % (name, len(r) - len(bad), len(r)))
    for k, ok, note in r:
        print("  %s %-22s %s" % ("O" if ok else "X", k, note if not ok else ""))
    return len(bad)

def main():
    if "--주간" in sys.argv:
        files = sorted(glob.glob(os.path.join(PIPE, "_jobs", "*낭독용.txt")))
        tot = 0
        print("═" * 58); print("자가채점 — 형 사고 문법 기준"); print("═" * 58)
        for f in files:
            tot += show(os.path.basename(f)[:-8], open(f, encoding="utf-8").read())
        print("\n합계 미달 %d개" % tot)
        p = os.path.join(OUT, "자가채점_%s.md" % datetime.date.today().isoformat())
        print("\n> 미달 항목은 고치고 다시 돌린다. 고칠 수 없으면 왜인지 적는다.")
    elif len(sys.argv) > 1:
        f = sys.argv[1]
        show(os.path.basename(f), open(f, encoding="utf-8").read())
    else:
        raise SystemExit("쓰는 법: 자가채점.py <대본.txt>  또는  --주간")

if __name__ == "__main__":
    main()
