"""shorts.proof 시안 배치 렌더러 테스트 (네트워크·ffmpeg 없이)."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from shorts.proof import PALETTES, find_scripts, gradient_cmd, gradient_colors


class TestGradient(unittest.TestCase):
    def test_팔레트_10개_전부_고유(self):
        self.assertEqual(len(PALETTES), len(set(PALETTES)))
        self.assertGreaterEqual(len(PALETTES), 10)

    def test_팔레트_범위는_번호로_결정(self):
        self.assertEqual(gradient_colors(1, "아무거나"), PALETTES[0])
        self.assertEqual(gradient_colors(10, "아무거나"), PALETTES[9])

    def test_팔레트_밖은_슬러그_해시로_결정적(self):
        a = gradient_colors(11, "11_같은_제목")
        self.assertEqual(a, gradient_colors(11, "11_같은_제목"))
        self.assertNotEqual(a, gradient_colors(12, "12_다른_제목"))

    def test_그라디언트_명령_구성(self):
        cmd = gradient_cmd(("0x111111", "0xEEEEEE"), 32.5, "bg.mp4")
        joined = " ".join(cmd)
        self.assertIn("gradients=s=1080x1350", joined)
        self.assertIn("c0=0x111111", joined)
        self.assertIn("d=32.50", joined)
        self.assertEqual(cmd[-1], "bg.mp4")


class TestFindScripts(unittest.TestCase):
    def test_번호붙은_대본만_순서대로(self):
        with TemporaryDirectory() as d:
            for name in ("02_둘째.txt", "01_첫째.txt", "README.md", "메모.txt"):
                Path(d, name).write_text("x", encoding="utf-8")
            found = [p.name for p in find_scripts(d)]
            self.assertEqual(found, ["01_첫째.txt", "02_둘째.txt"])


if __name__ == "__main__":
    unittest.main()
