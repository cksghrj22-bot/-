"""한국어 숫자 리더 잠금 — '9억 9,900만' 말깨짐 재발 방지(2026-07-28 박제)."""
import unittest

from shorts.tts import koreanize_numbers as k, read_sino, apply_synth_fixes


class TestKoreanize(unittest.TestCase):
    def test_read_sino_기본(self):
        self.assertEqual(read_sino(0), "영")
        self.assertEqual(read_sino(1000000), "백만")
        self.assertEqual(read_sino(999000000), "구억구천구백만")
        self.assertEqual(read_sino(18210000), "천팔백이십일만")
        self.assertEqual(read_sino(37), "삼십칠")

    def test_단위복합_쉼표(self):
        # 핵심: 쉼표 있는 억/만 복합에서 안 끊기게 한글로
        self.assertEqual(k("가치 차이는 9억 9,900만 원이에요."), "가치 차이는 구억구천구백만 원이에요.")
        self.assertEqual(k("여기 100만 원이 있어요."), "여기 백만 원이 있어요.")

    def test_순수숫자(self):
        self.assertEqual(k("37년 경력"), "삼십칠년 경력")
        self.assertEqual(k("1,821만 원"), "천팔백이십일만 원")

    def test_숫자없으면_그대로(self):
        self.assertEqual(k("같은 백만 원은 어디로"), "같은 백만 원은 어디로")

    def test_apply_synth_fixes에_포함(self):
        # apply_synth_fixes가 숫자 리더까지 자동 적용
        self.assertIn("구억구천구백만", apply_synth_fixes("9억 9,900만 원"))


if __name__ == "__main__":
    unittest.main()
