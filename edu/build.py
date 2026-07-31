# -*- coding: utf-8 -*-
"""python3 -m edu.build  →  스케줄 생성 + 검증 + HTML 갱신.

검증 실패 시 HTML을 쓰지 않고 종료코드 1 (버그가 산출물로 새는 걸 코드가 막음).
결과물:
  content/교육/2026-07-23_교육시스템_정본/교육일정_캘린더_2026.html
  content/교육/2026-07-23_교육시스템_정본/과목별_준비물_과제_주의사항.html
"""
import os, sys
from . import spec, schedule, render
from .prep_data import TEACHERS

OUT_DIR = os.path.join(os.path.dirname(__file__), '..',
                       'content', '교육', '2026-07-23_교육시스템_정본')
CAL = '교육일정_캘린더_2026.html'
PREP = '과목별_준비물_과제_주의사항.html'
ALL = '교육_전체안내_배포용.html'


def prep_consistency():
    """준비물 문서의 과목명이 spec 트랙과 일치하는지 대조(불일치 = 문제)."""
    problems = []
    prep_by_teacher = {name: [g for g, *_ in rows] for name, _, _, rows in TEACHERS}
    for teacher, subs in spec.TRACKS.items():
        if teacher == '와이':
            continue   # 맨즈 STAGE는 별도 줄기 — 시즈 준비물 문서 대상 아님
        want = [lab for lab, _ in subs]
        got = prep_by_teacher.get(teacher)
        if got is None:
            problems.append(f"준비물 문서에 '{teacher}' 없음"); continue
        if sorted(want) != sorted(got):
            miss = set(want) - set(got); extra = set(got) - set(want)
            if miss:  problems.append(f"준비물 누락 [{teacher}]: {sorted(miss)}")
            if extra: problems.append(f"준비물 잉여 [{teacher}]: {sorted(extra)}")
    return problems


def main(write=True):
    DATA = schedule.build()
    problems = schedule.validate(DATA) + prep_consistency()
    if problems:
        print("❌ 검증 실패 — HTML 미갱신:")
        for p in problems:
            print("  -", p)
        return 1
    print(f"✅ 검증 통과 — 과목 {spec.TOTAL_SUBJECTS} · 선생님 {len(spec.TEACHERS)}")
    if write:
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(os.path.join(OUT_DIR, CAL), 'w', encoding='utf-8') as f:
            f.write(render.render_calendar(DATA))
        with open(os.path.join(OUT_DIR, PREP), 'w', encoding='utf-8') as f:
            f.write(render.render_prep())
        with open(os.path.join(OUT_DIR, ALL), 'w', encoding='utf-8') as f:
            f.write(render.render_all(DATA))
        print("   →", CAL); print("   →", PREP); print("   →", ALL)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--check' not in sys.argv))
