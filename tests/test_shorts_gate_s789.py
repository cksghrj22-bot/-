import unittest

from scripts.shorts_gate import _aligned_speech_onsets, s7_manifest, s9_match


class ShortsGateS789Test(unittest.TestCase):
    def test_s8_difflib_alignment_does_not_accumulate_after_mismatch(self):
        words = [
            {"word": "첫문장", "start": 0.10, "end": 0.50},
            {"word": "오독", "start": 0.55, "end": 0.80},
            {"word": "둘째", "start": 1.40, "end": 1.70},
            {"word": "문장", "start": 1.72, "end": 2.00},
        ]
        onsets, ratio = _aligned_speech_onsets(["첫문장", "둘째문장"], words)
        self.assertEqual(onsets, [0.10, 1.40])
        self.assertGreater(ratio, 0.7)

    def test_s7_manifest_limits(self):
        cuts = [
            {"start": 0, "end": 1.0, "clip": "a", "source": "one"},
            {"start": 1, "end": 3.0, "clip": "b", "source": "one"},
            {"start": 3, "end": 5.0, "clip": "c", "source": "one"},
            {"start": 5, "end": 7.0, "clip": "d", "source": "one"},
            {"start": 7, "end": 9.0, "clip": "e", "source": "one"},
        ]
        result = " ".join(s7_manifest(cuts))
        self.assertIn("1.00초 < 1.6초", result)
        self.assertIn("자료컷 5개", result)
        self.assertIn("출처 1종", result)

    def test_s9_is_duration_weighted(self):
        result = s9_match([
            {"start": 0, "end": 8, "match": 1},
            {"start": 8, "end": 10, "match": 0},
        ])
        self.assertAlmostEqual(result["score"], 0.8)

    def test_s9_does_not_treat_mismatch_as_match(self):
        result = s9_match([{"start": 0, "end": 2, "일치": "불일치"}])
        self.assertEqual(result["score"], 0.0)


if __name__ == "__main__":
    unittest.main()
