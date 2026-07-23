"""텍스트 렌더 안전 유틸 테스트 — 글자 깨짐(글리프 부재·폭 초과) 사전차단 검증.
2026-07-23 이찬호: '글자 저번에도 많이 깨지던데 스스로 고쳐 코드 만들어.'"""
import unittest
from PIL import Image, ImageDraw

from shorts import textsafe

FB = "/usr/share/fonts/truetype/nanum/NanumSquareB.ttf"


class TestGlyph(unittest.TestCase):
    def test_정상글자는_결손없음(self):
        self.assertEqual(textsafe.missing_glyphs("러닝 = 인생", FB), [])

    def test_이모지는_결손검출(self):
        self.assertIn("😀", textsafe.missing_glyphs("좋아요😀", FB))

    def test_pick_font_전부있는폰트선택(self):
        self.assertEqual(textsafe.pick_font("가나다", [FB]), FB)

    def test_assert_ok(self):
        self.assertTrue(textsafe.assert_ok("러닝 = 인생", FB, 1800)[0])
        self.assertFalse(textsafe.assert_ok("x😀", FB, 1800)[0])


class TestRenderBased(unittest.TestCase):
    """cmap이 아니라 실제 렌더로 깨짐 검출 — 교보 손글씨 space=□ 실사고 재현."""
    HAND = "/root/.fonts/KyoboHandwriting2019.ttf"

    def test_손글씨_공백깨짐_검출(self):
        import os
        if not os.path.exists(self.HAND):
            self.skipTest("교보 폰트 없음")
        # cmap엔 space가 있다고 나오지만, 실제로는 박스로 깨짐 → broken_chars가 잡아야
        self.assertIn(" ", textsafe.broken_chars("러닝 = 인생", self.HAND))

    def test_나눔은_공백정상(self):
        self.assertEqual(textsafe.broken_chars("러닝 = 인생", FB), [])

    def test_pick_font_깨지는손글씨_피하고_나눔선택(self):
        import os
        if not os.path.exists(self.HAND):
            self.skipTest("교보 폰트 없음")
        self.assertEqual(textsafe.pick_font("러닝 = 인생", [self.HAND, FB]), FB)


class TestFit(unittest.TestCase):
    def setUp(self):
        self.d = ImageDraw.Draw(Image.new("RGB", (100, 100)))

    def test_긴문장_자동줄바꿈해_폭안에(self):
        font, lines = textsafe.fit(self.d, "그만두고 싶은 순간이 반드시 옵니다 그래도 한 걸음 더",
                                   FB, max_w=400, size=60)
        widest = max(self.d.textlength(l, font=font) for l in lines)
        self.assertLessEqual(widest, 400)
        self.assertGreater(len(lines), 1)

    def test_짧은문장_한줄유지(self):
        font, lines = textsafe.fit(self.d, "러닝", FB, max_w=1800, size=60)
        self.assertEqual(len(lines), 1)
        self.assertEqual(font.size, 60)

    def test_공백없는_긴토큰_글자단위분할(self):
        font, lines = textsafe.fit(self.d, "가나다라마바사아자차카타파하", FB, max_w=200, size=60)
        widest = max(self.d.textlength(l, font=font) for l in lines)
        self.assertLessEqual(widest, 200)

    def test_max_h제약시_축소(self):
        # 아주 낮은 높이 → 폰트 축소로 맞춤
        font, lines = textsafe.fit(self.d, "한 줄 문장", FB, max_w=1800, max_h=40, size=60, min_size=20)
        self.assertLessEqual(font.size * len(lines) * 1.18, 60)


if __name__ == "__main__":
    unittest.main()
