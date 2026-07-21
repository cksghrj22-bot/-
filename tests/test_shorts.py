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

    def test_unknown_hash_comment_is_skipped(self):
        # '# 라인:' 같은 미인식 주석은 대사가 되면 안 된다 (나레이션 오염 방지)
        script = parse_script("# 라인: 마인드\n# 메모: 아무거나\n00:00-00:03 진짜 대사\n")
        self.assertEqual(len(script.lines), 1)
        self.assertEqual(script.lines[0].text, "진짜 대사")


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

    def test_title_and_opacity(self):
        lines = [Line("본문", 0.0, 3.0)]
        ass = to_ass(lines, style={"box_opacity": 70}, title="상단 제목")
        self.assertIn("Style: Title,", ass)
        self.assertIn("Dialogue: 1,0:00:00.00,0:00:03.00,Title,상단 제목", ass)
        # 70% 불투명 = 알파 0x4D (77)
        self.assertIn("&H4D000000", ass)
        # 제목 박스는 노란색(FFD700 → BGR 00D7FF), 완전 불투명
        self.assertIn("&H0000D7FF", ass)


class TestEnglishSubtitle(unittest.TestCase):
    """영어 자막(외국인 유치용) — '한글 || English' 파싱 + 한글 아래 영어 줄."""

    def test_parse_splits_ko_en(self):
        s = parse_script("00:00-00:03 흰머리도 찰랑여요 || Gray hair can flow too\n")
        self.assertEqual(s.lines[0].text, "흰머리도 찰랑여요")
        self.assertEqual(s.lines[0].en, "Gray hair can flow too")

    def test_parse_no_separator_leaves_en_none(self):
        s = parse_script("00:00-00:03 한글만 있어요\n")
        self.assertIsNone(s.lines[0].en)

    def test_parse_untimed_line_also_splits(self):
        s = parse_script("한글 대사 || English line\n")
        self.assertEqual(s.lines[0].text, "한글 대사")
        self.assertEqual(s.lines[0].en, "English line")

    def test_ass_emits_english_style_and_event(self):
        lines = [Line("한글", 0.0, 3.0, en="Korean")]
        ass = to_ass(lines)
        self.assertIn("Style: English,", ass)
        self.assertIn("Dialogue: 0,0:00:00.00,0:00:03.00,English,Korean", ass)
        # 한글 자막(Default)도 그대로 있어야 한다
        self.assertIn("Dialogue: 0,0:00:00.00,0:00:03.00,Default,한글", ass)

    def test_no_english_style_when_absent(self):
        ass = to_ass([Line("한글만", 0.0, 3.0)])
        self.assertNotIn("Style: English,", ass)

    def test_english_below_korean(self):
        # 영어 margin_v(165)가 한글 margin_v(260)보다 작아야 한글 '아래'에 위치
        from shorts.subtitles import DEFAULT_STYLE, DEFAULT_EN_STYLE
        self.assertLess(DEFAULT_EN_STYLE["margin_v"], DEFAULT_STYLE["margin_v"])
        self.assertLess(DEFAULT_EN_STYLE["size"], DEFAULT_STYLE["size"])

    def test_long_english_wraps_two_lines(self):
        from shorts.subtitles import wrap_en
        long_en = "It starts with honoring the natural texture of your beautiful hair every day"
        wrapped = wrap_en(long_en, 44, 1080)
        self.assertIn("\\N", wrapped)
        self.assertLessEqual(wrapped.count("\\N"), 1)  # 최대 2줄


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
