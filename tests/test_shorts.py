"""쇼츠 파이프라인 단위 테스트 (ffmpeg/네트워크 없이 검증 가능한 부분)."""

import tempfile
import unittest
from pathlib import Path

from shorts.__main__ import find_jobs, load_config
from shorts.subtitles import Line, assign_timings, parse_script, to_ass

SCRIPT_SAMPLE = """# 제목: 정착 미용실 찾는 법
# 설명: 미용실 고르는 기준
# 태그: 미용실, 헤어, 쇼츠

00:00-00:03 첫 대사입니다
00:03-00:07 둘째 대사입니다
타이밍 없는 대사
"""


class TestParseScript(unittest.TestCase):
    def test_meta_and_lines(self):
        script = parse_script(SCRIPT_SAMPLE)
        self.assertEqual(script.title, "정착 미용실 찾는 법")
        self.assertEqual(script.tags, ["미용실", "헤어", "쇼츠"])
        self.assertEqual(len(script.lines), 3)
        self.assertEqual(script.lines[0].start, 0.0)
        self.assertEqual(script.lines[1].end, 7.0)
        self.assertIsNone(script.lines[2].start)


class TestTimings(unittest.TestCase):
    def test_assign_untimed_evenly(self):
        lines = [Line("a"), Line("b"), Line("c")]
        assign_timings(lines, duration=30.0)
        self.assertEqual((lines[0].start, lines[0].end), (0.0, 10.0))
        self.assertEqual((lines[2].start, lines[2].end), (20.0, 30.0))

    def test_keep_existing_timings(self):
        lines = [Line("a", 0.0, 5.0), Line("b")]
        assign_timings(lines, duration=20.0)
        self.assertEqual((lines[0].start, lines[0].end), (0.0, 5.0))
        self.assertEqual(lines[1].start, 5.0)


class TestAss(unittest.TestCase):
    def test_render_ass(self):
        lines = [Line("안녕하세요", 0.0, 3.5)]
        ass = to_ass(lines)
        self.assertIn("PlayResX: 1080", ass)
        self.assertIn("Dialogue: 0,0:00:00.00,0:00:03.50,Default,안녕하세요", ass)

    def test_untimed_raises(self):
        with self.assertRaises(ValueError):
            to_ass([Line("무타이밍")])


class TestRunner(unittest.TestCase):
    def test_find_jobs_pairs_video_and_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "a.mp4").write_bytes(b"")
            (p / "a.txt").write_text("대사", encoding="utf-8")
            (p / "b.mp4").write_bytes(b"")  # 스크립트 없음 → 건너뜀
            jobs = find_jobs(p)
            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0][0].name, "a.mp4")

    def test_load_config_merges_nested(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "cfg.json"
            p.write_text('{"youtube": {"privacy": "public"}}', encoding="utf-8")
            config = load_config(p)
            self.assertEqual(config["youtube"]["privacy"], "public")
            self.assertTrue(config["youtube"]["enabled"])  # 기본값 유지
            self.assertEqual(config["bgm_volume"], 0.15)


if __name__ == "__main__":
    unittest.main()
