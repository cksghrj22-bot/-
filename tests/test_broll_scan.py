"""B롤 자동스캔 카탈로그 테스트 — 네트워크 없이, 목록(dict)만으로 판정이 맞는지."""
import unittest

from shorts import broll_scan as bs


def _listing(files):
    return {"files": files}


SAMPLE = _listing([
    {"id": "A", "title": "IMG_1.MOV", "fileSize": "1000", "createdTime": "2026-07-15T00:00:00Z",
     "parentId": "174TFm5_cJyfi-U0X3HM_JKGN3gc3avYA", "fileExtension": "MOV", "viewUrl": "u/A"},
    {"id": "B", "title": "IMG_2.MP4", "fileSize": "2000", "createdTime": "2026-07-16T00:00:00Z",
     "parentId": "174TFm5_cJyfi-U0X3HM_JKGN3gc3avYA", "fileExtension": "MP4", "viewUrl": "u/B"},
    # 0바이트 = 업로드 실패분 → 제외돼야
    {"id": "Z", "title": "BROKEN.MP4", "fileSize": "0", "createdTime": "2026-07-16T01:00:00Z",
     "parentId": "174TFm5_cJyfi-U0X3HM_JKGN3gc3avYA", "fileExtension": "MP4"},
    # A의 중복(같은 id) → 한 번만
    {"id": "A", "title": "IMG_1.MOV", "fileSize": "1000", "createdTime": "2026-07-15T00:00:00Z",
     "parentId": "174TFm5_cJyfi-U0X3HM_JKGN3gc3avYA", "fileExtension": "MOV", "viewUrl": "u/A"},
])


class TestBrollScan(unittest.TestCase):
    def _fresh(self):
        cat = bs.load("__없는파일__.json")  # 존재하지 않으면 빈 카탈로그
        return cat

    def test_merge_skips_zero_and_dedups(self):
        cat = self._fresh()
        st = bs.merge_listing(cat, SAMPLE)
        self.assertEqual(st["added"], 2)          # A, B만
        self.assertEqual(st["skipped_zero"], 1)   # Z 제외
        self.assertEqual(st["duplicate"], 1)      # A 중복 한 번
        self.assertNotIn("Z", cat["clips"])
        self.assertEqual(set(cat["clips"]), {"A", "B"})

    def test_source_name_resolved_from_folder(self):
        cat = self._fresh()
        bs.merge_listing(cat, SAMPLE)
        self.assertEqual(cat["clips"]["A"]["source"], "폰_자동업로드")

    def test_pick_oldest_first(self):
        cat = self._fresh()
        bs.merge_listing(cat, SAMPLE)
        picks = bs.pick(cat, 1)
        self.assertEqual(picks[0]["id"], "A")  # 2026-07-15가 07-16보다 먼저

    def test_no_reuse(self):
        """이미 쓴 클립은 다시 추천되지 않아야(재사용 금지)."""
        cat = self._fresh()
        bs.merge_listing(cat, SAMPLE)
        bs.mark_used(cat, "09_테스트", ["A"])
        ids = [c["id"] for c in bs.pick(cat, 5)]
        self.assertNotIn("A", ids)
        self.assertEqual(ids, ["B"])

    def test_used_preserved_on_remerge(self):
        """다시 스캔해서 병합해도 사용기록(used_in)은 살아있어야."""
        cat = self._fresh()
        bs.merge_listing(cat, SAMPLE)
        bs.mark_used(cat, "09_테스트", ["A"])
        bs.merge_listing(cat, SAMPLE)  # 재스캔
        self.assertEqual(cat["clips"]["A"]["used_in"], ["09_테스트"])
        self.assertNotIn("A", [c["id"] for c in bs.pick(cat, 5)])

    def test_mark_used_idempotent(self):
        cat = self._fresh()
        bs.merge_listing(cat, SAMPLE)
        bs.mark_used(cat, "09_테스트", ["A"])
        bs.mark_used(cat, "09_테스트", ["A"])  # 두 번
        self.assertEqual(cat["clips"]["A"]["used_in"], ["09_테스트"])

    def test_summary(self):
        cat = self._fresh()
        bs.merge_listing(cat, SAMPLE)
        bs.mark_used(cat, "x", ["A"])
        self.assertEqual(bs.summary(cat), {"total": 2, "usable": 1, "used": 1})


if __name__ == "__main__":
    unittest.main()
