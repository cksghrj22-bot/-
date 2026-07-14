"""shorts.gdrive 드라이브 업로더 테스트 — 네트워크 없이 통과해야 한다."""

import json
import tempfile
import unittest
from pathlib import Path

from shorts import gdrive


class TestSecrets(unittest.TestCase):
    def _write(self, data: dict) -> Path:
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(data, f)
        f.close()
        return Path(f.name)

    def test_valid_secrets(self):
        creds = gdrive.load_secrets(self._write({"client_id": "c", "client_secret": "s"}))
        self.assertEqual(creds["client_id"], "c")

    def test_missing_client_secret_raises(self):
        with self.assertRaises(ValueError):
            gdrive.load_secrets(self._write({"client_id": "c"}))

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            gdrive.load_secrets("secrets/없는파일.json")

    def test_refresh_token_required_for_access(self):
        with self.assertRaises(ValueError):
            gdrive.access_token({"client_id": "c", "client_secret": "s"})


class TestConstants(unittest.TestCase):
    def test_scope_is_device_flow_allowed(self):
        # 기기 인증이 허용하는 스코프만 사용해야 한다 (전체 drive 스코프는 거부됨)
        self.assertEqual(gdrive.SCOPE, "https://www.googleapis.com/auth/drive.file")


if __name__ == "__main__":
    unittest.main()
