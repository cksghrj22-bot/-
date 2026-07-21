"""shorts.drive_download 단위테스트 — 네트워크 없이 HTML감지·confirm토큰 파싱·검증 로직 검증."""
import unittest

from shorts import drive_download as dd


class TestHtmlSniff(unittest.TestCase):
    def test_detects_doctype_html(self):
        self.assertTrue(dd._looks_like_html(b"<!DOCTYPE html><html>..."))
        self.assertTrue(dd._looks_like_html(b"   \n<html lang='en'>"))

    def test_detects_drive_title(self):
        self.assertTrue(dd._looks_like_html(b"<head><title>Google Drive - Virus scan warning</title>"))

    def test_real_video_bytes_not_html(self):
        # QuickTime ftyp 헤더는 HTML이 아님
        self.assertFalse(dd._looks_like_html(b"\x00\x00\x00\x18ftypqt  "))


class TestConfirmTokenParse(unittest.TestCase):
    def test_parses_hidden_inputs(self):
        html = (b'<form><input type="hidden" name="confirm" value="t">'
                b'<input type="hidden" name="uuid" value="abc-123">'
                b'<input type="hidden" name="id" value="FILEID"></form>')
        params = dd._parse_confirm_token(html)
        self.assertEqual(params.get("confirm"), "t")
        self.assertEqual(params.get("uuid"), "abc-123")
        self.assertEqual(params.get("id"), "FILEID")

    def test_parses_href_query(self):
        html = b'<a href="/uc?export=download&amp;confirm=xyz&amp;uuid=u9">Download anyway</a>'
        params = dd._parse_confirm_token(html)
        self.assertEqual(params.get("confirm"), "xyz")
        self.assertEqual(params.get("uuid"), "u9")

    def test_empty_when_no_token(self):
        self.assertEqual(dd._parse_confirm_token(b"<html>nothing here</html>"), {})


class TestDownloadValidation(unittest.TestCase):
    """download() 내부 검증 경로를 _fetch 몽키패치로 네트워크 없이 확인."""

    def setUp(self):
        self._orig_fetch = dd._fetch
        self._orig_sleep = dd.time.sleep
        dd.time.sleep = lambda *_: None  # 백오프 즉시

    def tearDown(self):
        dd._fetch = self._orig_fetch
        dd.time.sleep = self._orig_sleep

    def test_success_direct_video(self):
        payload = b"\x00\x00\x00\x18ftypqt  " + b"\x11" * 50_000
        dd._fetch = lambda opener, url, timeout=1800: (payload, "video/mp4")
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            dest = os.path.join(d, "out.mov")
            info = dd.download("FID", dest)
            self.assertEqual(info["bytes"], len(payload))
            self.assertEqual(info["attempts"], 1)
            with open(dest, "rb") as f:
                self.assertEqual(f.read(), payload)

    def test_interstitial_then_video(self):
        html = (b'<!DOCTYPE html><html><input name="confirm" value="t">'
                b'<input name="uuid" value="u1"></html>')
        video = b"\x00\x00\x00\x18ftypqt  " + b"\x22" * 50_000
        calls = {"n": 0}

        def fake(opener, url, timeout=1800):
            calls["n"] += 1
            return (html, "text/html") if calls["n"] == 1 else (video, "video/mp4")

        dd._fetch = fake
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            dest = os.path.join(d, "out.mov")
            info = dd.download("FID", dest)
            self.assertEqual(info["bytes"], len(video))
            self.assertGreaterEqual(calls["n"], 2)

    def test_truncated_size_mismatch_raises(self):
        # 기대보다 훨씬 작으면(잘림) 실패로 재시도 후 RuntimeError
        short = b"\x00\x00\x00\x18ftyp" + b"\x33" * 20_000
        dd._fetch = lambda opener, url, timeout=1800: (short, "video/mp4")
        with self.assertRaises(RuntimeError):
            dd.download("FID", "/tmp/never.mov", expected_size=5_000_000, max_retries=2)

    def test_only_html_raises(self):
        html = b"<!DOCTYPE html><html>virus scan</html>"
        dd._fetch = lambda opener, url, timeout=1800: (html, "text/html")
        with self.assertRaises(RuntimeError):
            dd.download("FID", "/tmp/never.mov", max_retries=2)


if __name__ == "__main__":
    unittest.main()
