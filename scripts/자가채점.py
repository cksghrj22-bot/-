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
    # ⑪ 폐기 문구 되살림 금지 (2026-08-12) — 수정원장.md 표에서 읽는다.
    #    형이 고쳐준 말을 부정형·조각으로 되살리는 사고를 렌더 전에 막는다.
    LEDGER = os.path.expanduser("~/atnown-trunk/prompts/수정원장.md")
    banned = []
    try:
        for ln in open(LEDGER, encoding="utf-8"):
            if ln.count("|") >= 4 and "폐기된 말" not in ln and "---" not in ln:
                cell = [c.strip() for c in ln.strip().strip("|").split("|")]
                if len(cell) >= 3 and cell[2]:
                    banned.append(cell[2])
    except FileNotFoundError:
        banned = []
    flat = re.sub(r"[^가-힣a-zA-Z0-9]", "", txt)
    hit = [b for b in banned
           if re.sub(r"[^가-힣a-zA-Z0-9]", "", b) and
              re.sub(r"[^가-힣a-zA-Z0-9]", "", b)[:12] in flat]
    add("⑪ 폐기 문구 없음", not hit,
        ("되살아났다: %s — 수정원장.md 확인" % ", ".join(hit)) if hit
        else "수정원장 %d건 대조 통과" % len(banned))
    # ── 형이 지적한 내 고질 3종 (2026-08-12) ─────────────────────────
    #   "부사를 잘못 써서 내용이 헷갈려지고 / 너무 줄이다가 급전개되고 /
    #    할루시네이션으로 말도 안 되는 내용을 확정하듯 얘기해서 별로야"
    def stems(line):
        return {w[:2] for w in re.findall(r"[가-힣]+", line) if len(w) >= 2}

    # ⑫ 접속부사가 논리와 맞는가
    #    통념 줄(다들·보통·대부분·~라고 생각합니다) 다음에는 대조가 와야 한다.
    #    인과(그래서·따라서·그러니까)를 쓰면 "다들 이런데 나는 아니다"가 무너진다.
    통념표지 = ["다들", "보통", "대부분", "라고 생각합니다", "인 줄 압니다", "흔히"]
    인과 = ["그래서", "따라서", "그러니까", "그러므로"]
    대조 = ["근데", "그런데", "하지만", "그러나", "반대로"]
    부사오용 = []
    for i in range(1, len(L)):
        prev, cur = L[i - 1], L[i]
        if any(t in prev for t in 통념표지) and any(cur.startswith(c) for c in 인과):
            부사오용.append("%d번 「%s」 — 앞이 통념이라 대조(%s)가 맞다"
                            % (i + 1, cur[:6], "·".join(대조[:3])))
        if any(cur.startswith(c) for c in 인과) and i >= 1 and not (
                any(t in prev for t in ["때문", "거든요", "니까", "습니다"])):
            pass
    add("⑫ 접속부사 논리", not 부사오용, " / ".join(부사오용) or "인과·대조 자리 맞음")

    # ⑬ 급전개 없음 — 줄과 줄 사이 말이 하나도 안 겹치면 '점프'.
    #    다만 아래는 정상 연결이라 점프로 세지 않는다:
    #      훅 2줄 / 마무리 2줄 / 접속사·지시어로 이어받은 줄 / 이질결합 줄
    이음말 = ["근데", "그런데", "하지만", "그러나", "반대로", "그래서", "따라서",
              "그러니까", "그 후에", "그다음", "그러고", "추가로", "게다가", "또",
              "이건", "그건", "이게", "그게", "이는", "그는", "이런", "그런", "이렇게"]
    점프 = []
    for i in range(1, len(L)):
        if stems(L[i - 1]) & stems(L[i]):
            continue
        if i <= 1 or i >= len(L) - 2:                      # 훅·마무리는 원래 턴이 있다
            continue
        if any(L[i].startswith(c) for c in 이음말):         # 말로 이어받았다
            continue
        if any(o in L[i] or o in L[i - 1] for o in OUTSIDE):  # 이질결합은 의도된 점프
            continue
        if L[i].rstrip(".!?").endswith(("니까요", "거든요", "때문입니다", "때문이거든요",
                                        "이니까요", "라서요", "으니까요")):
            continue                                        # 앞줄의 근거를 대는 줄 — 정상 연결
        점프.append("%d→%d번" % (i, i + 1))
    # 너무 줄임 — 15자 넘는 문장끼리 4배 이상 벌어지면 호흡이 끊긴다
    #   (10자 안팎 짧은 문장은 형 문체다. 「안 좋아하세요.」 같은 것 — 세지 않는다)
    급감 = []
    for i in range(1, len(L)):
        a, b = len(L[i - 1]), len(L[i])
        if min(a, b) >= 15 and (max(a, b) / min(a, b)) > 4.0:
            급감.append("%d→%d번 (%d자→%d자)" % (i, i + 1, a, b))
    add("⑬ 급전개 없음", not (점프 or 급감),
        ("말이 안 이어짐: %s" % ", ".join(점프) if 점프 else "")
        + (" / 길이 급감: %s" % ", ".join(급감) if 급감 else "")
        or "점프 0 · 길이 급감 0")

    # ⑭ 지어낸 수치 없음 — 대본의 모든 숫자는 수치_근거.md 에 출처가 있어야 한다
    SRC = os.path.expanduser("~/atnown-trunk/prompts/수치_근거.md")
    허용수 = set()
    try:
        for ln in open(SRC, encoding="utf-8"):
            if ln.count("|") >= 3 and "수치" not in ln and "---" not in ln:
                c = [x.strip() for x in ln.strip().strip("|").split("|")]
                if c and re.fullmatch(r"[0-9.]+", c[0]):
                    허용수.add(c[0])
    except FileNotFoundError:
        pass
    쓴수 = set(re.findall(r"\d+(?:\.\d+)?", txt))
    무근거 = sorted(쓴수 - 허용수)
    add("⑭ 지어낸 수치 없음", not 무근거,
        ("출처 없음: %s — 수치_근거.md 에 형 확인 후 적고 쓸 것" % ", ".join(무근거))
        if 무근거 else "숫자 %d개 전부 출처 있음" % len(쓴수))

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
