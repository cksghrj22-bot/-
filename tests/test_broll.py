"""B롤 자동 선택 엔진 테스트 — 주제 판별·클립 선택·중복 회피가 맞는지."""
import copy
import json
import unittest
from pathlib import Path

from shorts import broll

CATALOG = json.loads(Path("knowledge/broll_catalog.json").read_text(encoding="utf-8"))


class TestClassify(unittest.TestCase):
    def test_커트_대본은_cut(self):
        cat, _ = broll.classify("숱이 없어도 볼륨을 살리는 커트가 있다")
        self.assertEqual(cat, "cut")

    def test_운동_대본은_workout(self):
        cat, _ = broll.classify("자기투자는 꾸준한 운동 같은 것, 오래 지속하는 태도")
        self.assertEqual(cat, "workout")

    def test_독서_대본은_reading(self):
        cat, _ = broll.classify("기록하는 사람이 성장한다. 책을 읽고 메모하라")
        self.assertEqual(cat, "reading")

    def test_브랜드마인드_대본은_aerial(self):
        cat, _ = broll.classify("네 위치는 네가 만든다. 브랜드는 방향이고 성장이다")
        self.assertEqual(cat, "aerial")

    def test_두피_대본은_scalp(self):
        cat, _ = broll.classify("두피 스케일링으로 탈모를 늦춘다")
        self.assertEqual(cat, "scalp")

    def test_무점수는_기본값_aerial(self):
        cat, scores = broll.classify("ㅁㄴㅇㄹ")
        self.assertEqual(cat, broll.DEFAULT_CATEGORY)
        self.assertEqual(max(scores.values()), 0)


class TestPick(unittest.TestCase):
    def test_덜쓴것_우선(self):
        cat = copy.deepcopy(CATALOG)
        # cut 클립 두 개의 uses를 조작
        for c in cat["clips"]:
            if c["id"] == "IMG_9496":
                c["uses"] = 5
            if c["id"] == "IMG_9497":
                c["uses"] = 0
        chosen = broll.pick("cut", cat)
        self.assertEqual(chosen["id"], "IMG_9497")  # 덜 쓴 것

    def test_require_file_id는_id있는것만(self):
        chosen = broll.pick("aerial", CATALOG, require_file_id=True)
        self.assertIsNone(chosen)  # aerial은 아직 file_id 없음 → None

    def test_없는_카테고리는_None(self):
        self.assertIsNone(broll.pick("존재안함", CATALOG))


class TestSelect(unittest.TestCase):
    def test_end_to_end(self):
        r = broll.select_for_script("커트로 숱을 정리한다", CATALOG)
        self.assertEqual(r["category"], "cut")
        self.assertIsNotNone(r["clip"])
        self.assertTrue(r["ready"])  # cut 클립엔 file_id 있음

    def test_aerial은_아직_미준비(self):
        r = broll.select_for_script("브랜드와 성장의 방향", CATALOG)
        self.assertEqual(r["category"], "aerial")
        self.assertFalse(r["ready"])  # file_id 없음 → A방 스캔 대기


if __name__ == "__main__":
    unittest.main()
