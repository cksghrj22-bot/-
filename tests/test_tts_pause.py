"""쉼 강제(collect_pause_edits) — 시작부 강제 쉼 건너뛰기(head_grace) 검증.

이찬호 2026-07-18: 08 첫 마디가 로봇처럼 끊겨 들림 → 맨 앞 문장부호 강제 쉼을 죽인다.
"""
import unittest

from shorts.tts import collect_pause_edits

TARGETS = {",": 0.16, ".": 0.40}


def _mk(text):
    """글자별 start/end를 0.1초 간격으로 만든다 (부호도 한 글자로 취급)."""
    chars = list(text)
    starts = [i * 0.1 for i in range(len(chars))]
    ends = [(i + 1) * 0.1 for i in range(len(chars))]
    return chars, starts, ends


class TestHeadGrace(unittest.TestCase):
    def test_early_comma_skipped(self):
        # "가끔은, 옛날" — 콤마 뒤 쉼이 0.3초쯤(head_grace 1.2 이내) → 강제 쉼 안 넣음
        chars, s, e = _mk("가끔은, 옛날예요")
        edits = collect_pause_edits(chars, s, e, TARGETS, head_grace=1.2)
        self.assertEqual(edits, [], "시작부 콤마엔 강제 쉼이 없어야(첫 마디 안 끊김)")

    def test_late_punct_still_forced(self):
        # 앞에 긴 도입 뒤 마침표 → head_grace 넘어가면 강제 쉼 유지
        chars, s, e = _mk("이것은아주긴첫문장입니다. 다음문장")
        edits = collect_pause_edits(chars, s, e, TARGETS, head_grace=1.2)
        self.assertTrue(edits, "시작부 이후 문장부호는 강제 쉼이 유지돼야")

    def test_head_grace_zero_keeps_old_behavior(self):
        # head_grace=0 이면 예전처럼 첫 부호도 강제 쉼
        chars, s, e = _mk("가끔은, 옛날예요")
        edits = collect_pause_edits(chars, s, e, TARGETS, head_grace=0.0)
        self.assertTrue(edits)


if __name__ == "__main__":
    unittest.main()
