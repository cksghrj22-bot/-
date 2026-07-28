# -*- coding: utf-8 -*-
"""교육 스케줄·준비물 문서의 불변식(invariant) 테스트.

이 테스트가 '박제된 규칙'을 강제한다 — 다음 세션에서 코드를 고쳐도
가짜 과목·과목 누락·레벨 충돌·몰림이 다시 생기면 여기서 잡힌다.
실행: python3 -m unittest tests.test_edu
"""
import datetime
import unittest

from edu import spec, schedule, build


class TestEduSchedule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.DATA = schedule.build()
        cls.problems = schedule.validate(cls.DATA)

    def test_no_rule_violations(self):
        self.assertEqual(self.problems, [], "\n".join(self.problems))

    def test_all_70_subjects_placed_once(self):
        reg = [l for d, v in self.DATA.items() if isinstance(d, datetime.date)
               for l, t, lvt in v if t not in ('모델', '특강', '시험')]
        self.assertEqual(len(reg), spec.TOTAL_SUBJECTS)
        self.assertEqual(len(set(reg)), spec.TOTAL_SUBJECTS, "중복 과목 있음")

    def test_no_forbidden_fake_subjects(self):
        reg = [l for d, v in self.DATA.items() if isinstance(d, datetime.date)
               for l, t, lvt in v if t not in ('모델', '특강', '시험')]
        for l in reg:
            for bad in spec.FORBIDDEN_LABELS:
                self.assertNotIn(bad, l, f"가짜 과목 '{bad}' 등장")

    def test_no_same_level_same_day(self):
        for d, v in self.DATA.items():
            if not isinstance(d, datetime.date):
                continue
            used = []
            for l, t, lvt in v:
                if t in ('모델', '특강', '시험'):
                    continue
                s = set(int(x) for x in lvt.replace('L', '').split('·'))
                for u in used:
                    self.assertFalse(s & u, f"{d}: 같은 레벨 같은 날 충돌")
                used.append(s)

    def test_spread_within_window(self):
        dates = [d for d in self.DATA if isinstance(d, datetime.date)
                 and any(t not in ('모델', '특강', '시험') for _, t, _ in self.DATA[d])]
        self.assertGreaterEqual(min(dates), spec.WIN_START)
        self.assertLessEqual(max(dates), spec.WIN_END)
        # 12월 첫주까지 사용
        self.assertTrue(any(d.month == 12 for d in dates), "12월에 과목 없음(몰림)")

    def test_each_teacher_spread_min_months(self):
        need = spec.RULES['teacher_span_min_months']
        for t in spec.TEACHERS:
            months = set(d.month for d in self.DATA if isinstance(d, datetime.date)
                         for _, tt, _ in self.DATA[d] if tt == t)
            self.assertGreaterEqual(len(months), need, f"{t} 몰림")

    def test_prep_matches_spec(self):
        self.assertEqual(build.prep_consistency(), [])

    def test_build_check_exits_ok(self):
        self.assertEqual(build.main(write=False), 0)


if __name__ == '__main__':
    unittest.main()
