# -*- coding: utf-8 -*-
"""스케줄 생성 + 검증(invariant 강제).

build()    : spec의 트랙을 8월~12월초 전 구간에 고르게 펼쳐 날짜별 배치를 만든다.
validate() : 규칙 위반을 리스트로 반환. 하나라도 있으면 build 스크립트가 실패 처리한다.
             → 가짜 과목·과목 누락·같은 레벨 같은날 충돌·몰림을 '코드가' 막는다.
"""
import datetime, random
from collections import defaultdict, Counter
from . import spec


def _fridays(y, m):
    fs = []; d = datetime.date(y, m, 1)
    while d.month == m:
        if d.weekday() == 4:
            fs.append(d)
        d += datetime.timedelta(days=1)
    return fs


def event_fridays():
    """2·3·4주차 금요일 = 모델데이/특강 → 정규과목 미배정."""
    out = set()
    for m in (8, 9, 10, 11, 12):
        for idx, fd in enumerate(_fridays(2026, m), 1):
            if idx in (2, 3, 4):
                out.add(fd)
    return out


def _wkidx(d):
    return (d - spec.ANCHOR).days // 7


def build():
    """returns dict: date -> [(label, teacher, lvtext), ...]  (모델/특강/시험 포함)."""
    ev_fri = event_fridays()
    byweek = defaultdict(list)
    d = spec.WIN_START
    while d <= spec.WIN_END:
        if d.weekday() in (1, 2, 3, 4, 6) and d not in ev_fri:   # 화수목금일, 이벤트금 제외
            byweek[_wkidx(d)].append(d)
        d += datetime.timedelta(days=1)
    weeks = sorted(byweek)
    wmax = weeks[-1]

    # 주별 요일 순서를 로또식으로 섞음(재현 가능 — 고정 시드)
    wk_dates = {}
    for wi in weeks:
        ds = sorted(byweek[wi]); random.seed(700 + wi); random.shuffle(ds)
        wk_dates[wi] = ds

    # 레벨이 특정 달에 쏠리지 않고 매달 L1~L5가 골고루 열리게:
    #  ① 선생님 안에서 레벨셋별로 묶고, 라운드로빈(L1a,L2a,…,L1b,L2b,…)으로 섞은 뒤
    #  ② 그 섞인 순서를 전 구간(8~12월)에 선형으로 펼친다.
    # → 각 레벨이 한 선생님 안에서 앞·중간·뒤로 흩어지고, 하루/달 몰림도 없다.
    from itertools import zip_longest
    items = []
    for teacher, subs in spec.TRACKS.items():
        groups = {}                      # lset -> [labels] (등장 순서 유지)
        for label, lset in subs:
            groups.setdefault(lset, []).append(label)
        # 라운드로빈 순서를 '레벨 높은 쪽부터'(L5→L1)로 두어 L5도 초반(8월)에 등장.
        # 선형 배치와 합쳐지면 각 레벨이 8~11월 전 구간에 고르게 흩어진다.
        order_ls = sorted(groups, key=lambda s: -max(s))    # L5..L1
        cols = [list(zip(groups[ls], [ls] * len(groups[ls]))) for ls in order_ls]
        interleaved = [cell for tup in zip_longest(*cols)
                       for cell in tup if cell is not None]  # [(label, lset), ...]
        n = len(interleaved)
        for i, (label, lset) in enumerate(interleaved):
            ideal = round(i * wmax / (n - 1)) if n > 1 else 0
            items.append((ideal, teacher, label, lset))
    items.sort(key=lambda x: (x[0], x[1]))

    from collections import Counter
    DATA = defaultdict(list)
    day_lv = defaultdict(set)      # 그날 사용된 레벨
    day_tc = defaultdict(set)      # 그날 강의하는 선생님
    tc_wd = defaultdict(Counter)   # 선생님별 요일 사용횟수(요일 분산용)
    day_load = Counter()           # 날짜별 과목수(하루 몰림 완화)
    misplaced = []
    cap = spec.RULES['max_same_weekday']
    for ideal, teacher, label, lset in items:
        # 이상적 주 근처에서 후보를 모으되, 첫 후보가 나와도 +2주까지 더 훑어
        # '덜 쓴 요일'을 고를 여지를 준다(요일 벽 방지 + 이상적 주 근접 유지).
        cands = []          # (dt, off) — off=이상적 주와의 거리
        found_off = None
        for off in range(0, len(weeks) + 2):
            for wk in (ideal + off, ideal - off):
                if wk not in byweek:
                    continue
                for dt in wk_dates[wk]:
                    if dt.weekday() in spec.TEACHER_OFF.get(teacher, ()):  # 선생님 휴무 요일
                        continue
                    if lset & day_lv[dt]:            # 같은 레벨 이미 있음 → 불가
                        continue
                    if teacher in day_tc[dt]:        # 같은 선생님 하루 2번 방지
                        continue
                    cands.append((dt, off))
            if cands and found_off is None:
                found_off = off
            if found_off is not None and off >= found_off + 2:
                break
        if cands:
            # ① 요일 cap 넘는 후보는 뒤로(있으면 피함) ② 덜 쓴 요일 ③ 이상적 주 근접
            # ④ 그날 과목수 적은 쪽 ⑤ 재현 가능한 순서
            cands.sort(key=lambda c: (tc_wd[teacher][c[0].weekday()] >= cap,
                                      tc_wd[teacher][c[0].weekday()], c[1],
                                      day_load[c[0]], c[0].weekday(), c[0].toordinal()))
            dt = cands[0][0]
            day_lv[dt] |= lset; day_tc[dt].add(teacher)
            tc_wd[teacher][dt.weekday()] += 1; day_load[dt] += 1
            DATA[dt].append((label, teacher, spec.lvtxt(lset)))
        else:
            misplaced.append((teacher, label))

    # ── 배치 후 수동 이동(spec.MANUAL_MOVES) — 제약 지키며 월 간 재배치 ──
    def _lset_of(lvt):
        return frozenset(int(x) for x in lvt.replace('L', '').split('·') if x)
    for level, src_m, dst_m, cnt in getattr(spec, 'MANUAL_MOVES', []):
        for _ in range(cnt):
            # 출발월에서 그 레벨을 점유한 과목(재현 위해 정렬) 중 옮길 수 있는 것 선택
            srcs = sorted(
                ((d, i, lab, tc, lvt)
                 for d in list(DATA) if isinstance(d, datetime.date) and d.month == src_m
                 for i, (lab, tc, lvt) in enumerate(DATA[d])
                 if tc not in ('모델', '특강', '시험') and level in _lset_of(lvt)),
                key=lambda x: (x[3], x[0].toordinal(), x[2]))
            moved = False
            for d0, i0, lab, tc, lvt in srcs:
                lset = _lset_of(lvt)
                # 도착월에서 빈 자리(같은레벨X·같은선생님X·휴무X·이벤트금X·정원)
                dsts = sorted(d for wk in weeks for d in wk_dates[wk]
                              if d.month == dst_m
                              and d.weekday() not in spec.TEACHER_OFF.get(tc, ())
                              and not (lset & day_lv[d]) and tc not in day_tc[d]
                              and day_load[d] < spec.RULES['max_per_day'])
                if not dsts:
                    continue
                d1 = dsts[0]
                # 원위치에서 제거
                DATA[d0].pop(i0)
                day_load[d0] -= 1; tc_wd[tc][d0.weekday()] -= 1
                day_tc[d0].discard(tc)
                day_lv[d0] = set().union(*[_lset_of(x[2]) for x in DATA[d0]
                                           if x[1] not in ('모델', '특강', '시험')]) if DATA[d0] else set()
                # 새 위치에 추가
                DATA[d1].append((lab, tc, lvt))
                day_lv[d1] |= lset; day_tc[d1].add(tc)
                tc_wd[tc][d1.weekday()] += 1; day_load[d1] += 1
                moved = True
                break
            if not moved:
                misplaced.append((f'이동실패 L{level}', f'{src_m}→{dst_m}'))

    # 금 이벤트 + 시험
    for m in (8, 9, 10, 11, 12):
        for idx, fd in enumerate(_fridays(2026, m), 1):
            if idx in (2, 4) and spec.WIN_START <= fd <= spec.WIN_END:
                DATA[fd].append(('모델데이', '모델', ''))
            if idx == 3:
                DATA[fd].append((f'특강 {spec.LECT.get(m, "")}', '특강', ''))
    DATA[spec.EXAM].append(('입봉시험', '시험', ''))

    for dt in DATA:                # 표기 순서: 레벨 오름차순
        DATA[dt].sort(key=lambda x: x[2])
    DATA['_misplaced'] = misplaced  # 검증용(렌더 시 무시)
    return DATA


def _regular(DATA):
    return [(d, l, t, lvt) for d, v in DATA.items() if isinstance(d, datetime.date)
            for l, t, lvt in v if t not in ('모델', '특강', '시험')]


def validate(DATA):
    """규칙 위반 목록을 반환(빈 리스트=정상)."""
    problems = []
    reg = _regular(DATA)

    # 1) 과목 총수 = 스펙과 일치 (누락/중복 없음)
    if len(reg) != spec.TOTAL_SUBJECTS:
        problems.append(f"과목 수 불일치: {len(reg)} (스펙 {spec.TOTAL_SUBJECTS})")

    # 2) 미배치 없음
    mis = DATA.get('_misplaced', [])
    if mis:
        problems.append(f"미배치 과목 {len(mis)}: {mis}")

    # 3) 가짜 과목 금지
    for d, l, t, lvt in reg:
        for bad in spec.FORBIDDEN_LABELS:
            if bad in l:
                problems.append(f"가짜 과목 등장: '{l}' ({d})")

    # 4) 같은 레벨 같은 날 충돌 금지
    for d in DATA:
        if not isinstance(d, datetime.date):
            continue
        used = []
        for l, t, lvt in DATA[d]:
            if t in ('모델', '특강', '시험'):
                continue
            s = set(int(x) for x in lvt.replace('L', '').split('·'))
            for u in used:
                if s & u:
                    problems.append(f"같은 레벨 같은 날 충돌: {d} {lvt}")
            used.append(s)
        if len(used) > spec.RULES['max_per_day']:
            problems.append(f"하루 과목 초과({len(used)}>{spec.RULES['max_per_day']}): {d}")

    # 5) 스펙의 모든 과목이 정확히 한 번 등장
    placed = sorted(l for _, l, _, _ in reg)
    want = sorted(lab for subs in spec.TRACKS.values() for lab, _ in subs)
    if placed != want:
        miss = set(want) - set(placed)
        extra = set(placed) - set(want)
        if miss:  problems.append(f"누락된 과목: {sorted(miss)}")
        if extra: problems.append(f"스펙에 없는 과목: {sorted(extra)}")

    # 6) 몰림 방지 — 각 선생님은 최소 N개월에 걸쳐 분산
    from collections import Counter
    need = spec.RULES['teacher_span_min_months']
    for t in spec.TEACHERS:
        months = set(d.month for d, l, tt, lvt in reg if tt == t)
        if len(months) < need:
            problems.append(f"{t} 몰림: {len(months)}개월에만 분산(최소 {need})")

    # 7) 기간 경계 — window 밖 정규과목 금지
    for d, l, t, lvt in reg:
        if not (spec.WIN_START <= d <= spec.WIN_END):
            problems.append(f"기간 밖 과목: {d} {l}")

    # 8) 요일 벽 방지 — 한 선생님이 같은 요일에 과도하게 몰리면 안 됨
    wd_by_t = defaultdict(Counter)
    for d, l, t, lvt in reg:
        wd_by_t[t][d.weekday()] += 1
    cap = spec.RULES['max_same_weekday']
    wd = ['월', '화', '수', '목', '금', '토', '일']
    for t, c in wd_by_t.items():
        for w, n in c.items():
            if n > cap:
                problems.append(f"{t} 요일 몰림: {wd[w]}요일 {n}회(최대 {cap})")

    # 9) 선생님별 휴무 요일 준수 (예: 와이=화·일 배제 → 수·목·금만)
    for d, l, t, lvt in reg:
        if d.weekday() in spec.TEACHER_OFF.get(t, ()):
            problems.append(f"{t} 휴무 요일 배치: {d}({wd[d.weekday()]}) {l}")

    return problems
