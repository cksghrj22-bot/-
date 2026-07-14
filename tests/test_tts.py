"""일레븐랩스 TTS 모듈 테스트 — 네트워크·외부 의존성 없이 통과해야 한다."""

import json
import tempfile
import unittest
from pathlib import Path

from shorts import tts


class TestCredentials(unittest.TestCase):
    def _write(self, data: dict) -> Path:
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(data, f)
        f.close()
        return Path(f.name)

    def test_valid_credentials_get_defaults(self):
        creds = tts.load_credentials(self._write({"api_key": "sk_x", "voice_id": "v1"}))
        self.assertEqual(creds["model_id"], tts.DEFAULT_MODEL)
        self.assertEqual(creds["speed"], tts.DEFAULT_SPEED)
        self.assertEqual(creds["voice_settings"], tts.DEFAULT_VOICE_SETTINGS)

    def test_voice_settings_override_merges_with_defaults(self):
        creds = tts.load_credentials(self._write(
            {"api_key": "sk_x", "voice_id": "v1", "voice_settings": {"stability": 0.6}}
        ))
        self.assertEqual(creds["voice_settings"]["stability"], 0.6)
        self.assertEqual(
            creds["voice_settings"]["similarity_boost"],
            tts.DEFAULT_VOICE_SETTINGS["similarity_boost"],
        )

    def test_missing_voice_id_raises(self):
        with self.assertRaises(ValueError):
            tts.load_credentials(self._write({"api_key": "sk_x"}))

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            tts.load_credentials("secrets/없는파일.json")


class TestBuildRequest(unittest.TestCase):
    def test_request_shape(self):
        req = tts.build_request("숱 쳤는데 더 지저분해진 적 있죠?", "sk_key", "voice123")
        self.assertIn("/text-to-speech/voice123", req.full_url)
        self.assertEqual(req.get_header("Xi-api-key"), "sk_key")
        body = json.loads(req.data.decode("utf-8"))
        self.assertEqual(body["text"], "숱 쳤는데 더 지저분해진 적 있죠?")
        self.assertEqual(body["model_id"], tts.DEFAULT_MODEL)


class TestStitchingContext(unittest.TestCase):
    """줄별 합성이어도 앞뒤 문맥으로 억양이 이어지게 하는 previous_text/next_text."""

    def test_context_included_when_given(self):
        req = tts.build_request(
            "둘째 줄.", "sk_key", "voice123",
            previous_text="첫째 줄.", next_text="셋째 줄.",
        )
        body = json.loads(req.data.decode("utf-8"))
        self.assertEqual(body["previous_text"], "첫째 줄.")
        self.assertEqual(body["next_text"], "셋째 줄.")

    def test_context_omitted_when_absent(self):
        req = tts.build_request("한 줄.", "sk_key", "voice123")
        body = json.loads(req.data.decode("utf-8"))
        self.assertNotIn("previous_text", body)
        self.assertNotIn("next_text", body)


class TestScheduleStarts(unittest.TestCase):
    """앞 줄 나레이션이 끝나기 전에 다음 줄이 겹치지 않게 시작 시각을 민다."""

    def test_no_shift_when_slots_are_wide_enough(self):
        starts = tts.schedule_starts([0.0, 5.0], durations=[2.2, 2.2], speed=1.1)
        self.assertEqual(starts, [0.0, 5.0])

    def test_shifts_when_previous_line_would_overlap(self):
        # 1.1배속 시 3.3초 클립 = 3.0초 점유 → 2.5초 시작 예정이던 둘째 줄은 3.0+0.12로 밀림
        starts = tts.schedule_starts([0.0, 2.5], durations=[3.3, 1.1], speed=1.1)
        self.assertEqual(starts[0], 0.0)
        self.assertAlmostEqual(starts[1], 3.12, places=6)

    def test_shift_cascades_to_following_lines(self):
        starts = tts.schedule_starts([0.0, 1.0, 2.0], durations=[2.2, 2.2, 1.1], speed=1.1)
        self.assertAlmostEqual(starts[1], 2.12, places=6)
        self.assertAlmostEqual(starts[2], 4.24, places=6)


class TestNarrationFilter(unittest.TestCase):
    def test_filter_places_clips_at_line_starts(self):
        f = tts.narration_filter([("a.mp3", 0.0), ("b.mp3", 2.5)], speed=1.1)
        self.assertIn("atempo=1.1", f)
        self.assertIn("adelay=0|0", f)
        self.assertIn("adelay=2500|2500", f)
        self.assertIn("amix=inputs=2:normalize=0", f)
        self.assertTrue(f.endswith("[nar]"))

    def test_filter_declicks_clip_edges(self):
        f = tts.narration_filter([("a.mp3", 0.0)], speed=1.1)
        self.assertIn("afade=t=in:st=0:d=0.02", f)
        self.assertIn("areverse", f)


if __name__ == "__main__":
    unittest.main()


class TestAlignLineSpans(unittest.TestCase):
    """전체 합성의 글자 타임스탬프 → 줄별 자막 타이밍 (배속 반영)."""

    def test_spans_follow_speech(self):
        texts = ["안녕", "잘 가"]
        chars = list("안녕\n잘 가")
        starts = [0.0, 0.4, 0.9, 1.1, 1.5, 1.7]
        ends = [0.4, 0.8, 1.0, 1.5, 1.7, 2.2]
        spans = tts.align_line_spans(texts, chars, starts, ends, speed=1.1)
        self.assertAlmostEqual(spans[0][0], 0.0)
        self.assertAlmostEqual(spans[0][1], 0.8 / 1.1)
        self.assertAlmostEqual(spans[1][0], 1.1 / 1.1)
        self.assertAlmostEqual(spans[1][1], 2.2 / 1.1)
