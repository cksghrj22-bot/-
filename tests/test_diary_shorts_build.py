import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "diary_shorts_build.py"
SPEC = importlib.util.spec_from_file_location("diary_shorts_build", MODULE_PATH)
diary = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = diary
SPEC.loader.exec_module(diary)


class DiaryShortsBuildTest(unittest.TestCase):
    def test_parse_silences_and_speech_complement(self):
        stderr = """
        [silencedetect] silence_start: 0
        [silencedetect] silence_end: 1.25 | silence_duration: 1.25
        [silencedetect] silence_start: 2.50
        [silencedetect] silence_end: 4.00 | silence_duration: 1.50
        """
        silences = diary.parse_silences(stderr)
        self.assertEqual(silences, [diary.Span(0.0, 1.25), diary.Span(2.5, 4.0)])
        self.assertEqual(
            diary.speech_from_silences(silences, 5.0),
            [diary.Span(1.25, 2.5), diary.Span(4.0, 5.0)],
        )

    def test_filler_is_removed_and_duplicate_keeps_latter(self):
        spans = [diary.Span(0, 1.3), diary.Span(2, 3.3), diary.Span(4, 5.4)]
        words = [
            diary.Word(0.05, 0.30, "어"), diary.Word(0.45, 1.10, "시작합니다"),
            diary.Word(2.05, 2.60, "같은"), diary.Word(2.62, 3.15, "말입니다"),
            diary.Word(4.05, 4.60, "같은"), diary.Word(4.62, 5.15, "말입니다"),
        ]
        kept = diary.clean_speech_spans(spans, words, 6.0)
        self.assertGreaterEqual(kept[0].start, 0.30)
        self.assertFalse(any(item.start < 3.5 and item.start > 1.5 for item in kept))

    def test_source_time_mapping(self):
        kept = [diary.Span(2, 4), diary.Span(6, 9)]
        self.assertEqual(diary.map_source_time(3, kept), 1)
        self.assertEqual(diary.map_source_time(7, kept), 3)
        self.assertEqual(diary.map_source_time(10, kept), 5)

    def test_ass_contains_split_caption_and_handle(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "captions.ass"
            diary.write_ass(target, [diary.Caption(0.1, 1.2, "첫 줄\\N둘째 줄")], 2.0)
            text = target.read_text(encoding="utf-8")
            self.assertIn("첫 줄\\N둘째 줄", text)
            self.assertIn("@Atnownchano", text)

    def test_caption_groups_split_on_phrase_gap(self):
        kept = [diary.Span(0, 3)]
        words = [
            diary.Word(0.1, 0.8, "첫 문장입니다"),
            diary.Word(1.1, 1.8, "둘째 문장입니다"),
        ]
        captions = diary.captions_for_spans(kept, words)
        self.assertEqual([item.text for item in captions], ["첫 문장입니다", "둘째 문장입니다"])

    def test_screen_sections_are_keyword_anchored(self):
        captions = [
            diary.Caption(0, 3, "AI한테 일 시키고"),
            diary.Caption(5, 8, "지켜야 할 게 몇 개 있어요"),
            diary.Caption(12, 15, "문서에 적어놨어요"),
            diary.Caption(18, 20, "검사하는 걸 만들었어요"),
            diary.Caption(23, 25, "길이가 넘으면 걸리고"),
            diary.Caption(28, 30, "걸리면 아예 안 나와요"),
            diary.Caption(33, 36, "제 눈으로 못 봤던 거예요"),
        ]
        sections = diary.screen_sections(captions, 40)
        self.assertEqual([name for name, _ in sections], list(diary.SCREEN_PRESETS))
        self.assertAlmostEqual(sum(length for _, length in sections), 40)


if __name__ == "__main__":
    unittest.main()
