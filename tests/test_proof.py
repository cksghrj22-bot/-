"""shorts.proof 시안 배치 렌더러 테스트 (네트워크·ffmpeg 없이)."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from shorts.proof import PALETTES, broll_bg_cmd, find_scripts, gradient_cmd, gradient_colors, match_broll


class TestBrollLoop(unittest.TestCase):
    """짧은 B롤이 나레이션보다 짧아도 잘리지 않게 루프 채움 (2026-07-21 잘림버그 잠금)."""

    def test_broll_bg_cmd에_stream_loop_있음(self):
        cmd = broll_bg_cmd("src.mp4", 1.0, 40.0, "bg.mp4")
        self.assertIn("-stream_loop", cmd)
        # -stream_loop 는 입력(-i) 앞에 와야 입력 루프로 동작
        self.assertLess(cmd.index("-stream_loop"), cmd.index("-i"))
        self.assertIn("-1", cmd[cmd.index("-stream_loop") + 1])

    def test_duration_t로_길이_고정(self):
        cmd = broll_bg_cmd("src.mp4", 2.0, 45.0, "bg.mp4")
        self.assertIn("-t", cmd)
        self.assertIn("45.00", cmd)


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


class TestMatchBroll(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(match_broll("01_대본", None))

    def test_single_file_used_directly(self):
        with TemporaryDirectory() as d:
            f = Path(d) / "아무영상.mp4"
            f.touch()
            self.assertEqual(match_broll("01_대본", f), f)

    def test_directory_matches_by_prefix(self):
        with TemporaryDirectory() as d:
            hit = Path(d) / "01_커트장면.MOV"
            miss = Path(d) / "02_다른편.mp4"
            hit.touch(); miss.touch()
            self.assertEqual(match_broll("01_대본", d), hit)
            self.assertIsNone(match_broll("03_없는편", d))
