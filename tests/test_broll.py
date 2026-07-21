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
        # 합성 카탈로그: file_id 없는 카테고리는 require_file_id=True면 None (상태 비의존)
        synthetic = {"clips": [{"id": "X", "category": "cut", "file_id": None, "start": 0, "uses": 0}]}
        self.assertIsNone(broll.pick("cut", synthetic, require_file_id=True))
        chosen2 = broll.pick("aerial", CATALOG, require_file_id=True)
        self.assertIsNotNone(chosen2)  # aerial은 DJI 스캔 완료 → 있음
        self.assertTrue(chosen2.get("file_id"))

    def test_없는_카테고리는_None(self):
        self.assertIsNone(broll.pick("존재안함", CATALOG))


class TestUsableFilter(unittest.TestCase):
    """usable:false 클립은 uses=0이어도 자동선택 제외 (2026-07-21 실내오분류·다운불가 사고방지)."""

    def test_usable_false는_제외(self):
        synthetic = {"clips": [
            {"id": "BAD", "category": "aerial", "file_id": "x", "start": 0, "uses": 0, "usable": False},
            {"id": "GOOD", "category": "aerial", "file_id": "y", "start": 0, "uses": 3},
        ]}
        chosen = broll.pick("aerial", synthetic)
        self.assertEqual(chosen["id"], "GOOD")  # uses 많아도 usable한 것

    def test_전부_usable_false면_None(self):
        synthetic = {"clips": [
            {"id": "BAD", "category": "cut", "file_id": "x", "start": 0, "uses": 0, "usable": False},
        ]}
        self.assertIsNone(broll.pick("cut", synthetic))

    def test_usable_생략은_기본_사용가능(self):
        synthetic = {"clips": [{"id": "OK", "category": "cut", "file_id": "x", "start": 0, "uses": 0}]}
        self.assertEqual(broll.pick("cut", synthetic)["id"], "OK")

    def test_실카탈로그_실내DJI_다운불가_제외됨(self):
        # 실내 오분류 DJI 4개 + 다운불가 MVI_8980 은 어떤 카테고리 선택에도 안 뽑힘
        banned = {"MVI_8980", "DJI_155319", "DJI_153152", "DJI_152313", "DJI_153345"}
        for cat in {c["category"] for c in CATALOG["clips"]}:
            chosen = broll.pick(cat, CATALOG)
            if chosen:
                self.assertNotIn(chosen["id"], banned)


class TestSelect(unittest.TestCase):
    def test_end_to_end(self):
        r = broll.select_for_script("커트로 숱을 정리한다", CATALOG)
        self.assertEqual(r["category"], "cut")
        self.assertIsNotNone(r["clip"])
        self.assertTrue(r["ready"])  # cut 클립엔 file_id 있음

    def test_aerial은_DJI스캔완료(self):
        r = broll.select_for_script("브랜드와 성장의 방향", CATALOG)
        self.assertEqual(r["category"], "aerial")
        self.assertTrue(r["ready"])  # DJI file_id 채워짐 → 렌더 가능

    def test_scalp도_스캔완료(self):
        # A방 2026-07-18 두피 스캔완료 → 이제 렌더 가능
        r = broll.select_for_script("두피 스케일링 탈모 관리", CATALOG)
        self.assertEqual(r["category"], "scalp")
        self.assertTrue(r["ready"])

    def test_file_id없으면_not_ready(self):
        # 동작 자체(스캔 대기 표시)는 합성 카탈로그로 계속 검증 — 실카탈로그가 다 차도 유효
        synthetic = {"clips": [{"id": "X", "category": "scalp", "file_id": None, "start": 0, "uses": 0}]}
        r = broll.select_for_script("두피 스케일링 탈모 관리", synthetic)
        self.assertFalse(r["ready"])


if __name__ == "__main__":
    unittest.main()
