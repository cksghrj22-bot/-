"""인입 자동스캔 로직 테스트 — 네트워크·드라이브 없이 통과."""
import json
import unittest
from pathlib import Path
import tempfile

from shorts.intake_scan import categorize, register_new


class TestCategorize(unittest.TestCase):
    def test_keyword_categories(self):
        cases = {
            "새치염색_도포_클로즈업.mp4": "color",
            "흰머리_탈색줄.mov": "color",
            "희주샘_아이롱2.mov": "perm",
            "물결펌_스타일링.mp4": "perm",
            "가발커트_3585.mp4": "cut",
            "숱치기_손동작.mp4": "cut",
            "상담_경로짚기.mp4": "consult",
            "두피_스케일링.mp4": "scalp",
            "하이록스_팀훈련.mp4": "workout",
            "교토_강변_도보.mp4": "aerial",
            "빨간책_독서.mp4": "reading",
        }
        for name, cat in cases.items():
            self.assertEqual(categorize(name), cat, name)

    def test_unknown_returns_none(self):
        self.assertIsNone(categorize("IMG_9999.mp4"))
        self.assertIsNone(categorize("무제_영상.mov"))


class TestRegister(unittest.TestCase):
    def _catalog(self, clips):
        d = {"_설명": "t", "_카테고리": {}, "clips": clips}
        p = Path(tempfile.mkdtemp()) / "cat.json"
        p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        return p

    def test_adds_new_video_with_category(self):
        p = self._catalog([])
        res = register_new([{"id": "FID1", "name": "새치염색_도포.mp4"}], p)
        self.assertEqual(len(res["added"]), 1)
        self.assertEqual(res["added"][0]["category"], "color")
        cat = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(cat["clips"][0]["file_id"], "FID1")

    def test_skips_existing_file_id(self):
        p = self._catalog([{"id": "old", "category": "cut", "file_id": "FID1"}])
        res = register_new([{"id": "FID1", "name": "가발커트_x.mp4"}], p)
        self.assertEqual(res["added"], [])
        self.assertIn("가발커트_x.mp4", res["skipped_existing"])

    def test_skips_finished_and_nonvideo(self):
        p = self._catalog([])
        res = register_new([
            {"id": "A", "name": "13_이런_디자이너_보이스시안.mp4"},   # 완성본
            {"id": "B", "name": "메모.txt"},                          # 비영상
        ], p)
        self.assertEqual(res["added"], [])
        self.assertIn("13_이런_디자이너_보이스시안.mp4", res["skipped_finished"])
        self.assertIn("메모.txt", res["skipped_nonvideo"])

    def test_unknown_category_flagged_manual(self):
        p = self._catalog([])
        res = register_new([{"id": "Z", "name": "IMG_0001.mp4"}], p)
        self.assertEqual(len(res["added"]), 1)
        self.assertIsNone(res["added"][0]["category"])
        self.assertIn("IMG_0001.mp4", res["manual"])

    def test_key_collision_suffixed(self):
        p = self._catalog([{"id": "새치염색_도포", "category": "color", "file_id": "OLD"}])
        res = register_new([{"id": "NEW", "name": "새치염색_도포.mp4"}], p)
        self.assertEqual(res["added"][0]["id"], "새치염색_도포_2")


if __name__ == "__main__":
    unittest.main()
