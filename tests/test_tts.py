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


class TestNarrationFilter(unittest.TestCase):
    def test_filter_places_clips_at_line_starts(self):
        f = tts.narration_filter([("a.mp3", 0.0), ("b.mp3", 2.5)], speed=1.1)
        self.assertIn("atempo=1.1", f)
        self.assertIn("adelay=0|0", f)
        self.assertIn("adelay=2500|2500", f)
        self.assertIn("amix=inputs=2:normalize=0", f)
        self.assertTrue(f.endswith("[nar]"))


if __name__ == "__main__":
    unittest.main()
