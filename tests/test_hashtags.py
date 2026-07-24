"""줄기별 해시태그 자동첨부 테스트 (네트워크 없이)."""
import unittest

from shorts import hashtags
from shorts.upload_youtube import build_metadata


class TestHashtags(unittest.TestCase):
    def test_brand_always_present(self):
        for stem in ["교육", "컬러", "흑백", "만화카드", "미용"]:
            tags = hashtags.tag_list(stem)
            self.assertIn("앳나운", tags)
            self.assertIn("ATNOWN", tags)  # 영어 무조건

    def test_alias_resolves(self):
        self.assertEqual(hashtags.resolve("커트의정석"), "교육")
        self.assertEqual(hashtags.resolve("반보"), "컬러")
        self.assertEqual(hashtags.resolve("마인드"), "흑백")
        self.assertEqual(hashtags.resolve("카드"), "만화카드")
        self.assertEqual(hashtags.resolve("몰라요"), "미용")  # 기본값

    def test_stem_specific_tag(self):
        self.assertIn("커트의정석", hashtags.tag_list("교육"))
        self.assertNotIn("커트의정석", hashtags.tag_list("컬러"))

    def test_block_format(self):
        block = hashtags.hashtag_block("교육")
        self.assertTrue(block.startswith("#앳나운"))
        self.assertIn("#커트의정석", block)

    def test_caption_appends_once(self):
        body = "창엽 부원장의 커트 강의."
        out = hashtags.caption_with_tags(body, "교육")
        self.assertIn(body, out)
        self.assertIn("#커트의정석", out)
        # 이미 태그가 있으면 다시 붙이지 않음
        again = hashtags.caption_with_tags(out, "교육")
        self.assertEqual(again.count("#앳나운"), 1)

    def test_limit_30(self):
        self.assertLessEqual(len(hashtags.tag_list("미용")), 30)
        self.assertLessEqual(len(hashtags.youtube_tags("교육")), 30)

    def test_build_metadata_injects_hashtags(self):
        meta = build_metadata("커트의 정석", description="본문", stem="교육")
        self.assertIn("#커트의정석", meta["snippet"]["description"])
        self.assertIn("앳나운", meta["snippet"]["tags"])

    def test_build_metadata_no_stem_unchanged(self):
        meta = build_metadata("제목", description="본문")
        self.assertEqual(meta["snippet"]["description"], "본문")
        self.assertEqual(meta["snippet"]["tags"], [])


if __name__ == "__main__":
    unittest.main()
