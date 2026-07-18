"""정본 점검기 테스트 — config가 정본과 맞는지, 어긋나면 잡아내는지."""
import json
import unittest
from pathlib import Path

from shorts.spec import check_spec, GRADE_PALETTE
from shorts.proof import GRADES

CONFIG = json.loads(Path("shorts_config.json").read_text(encoding="utf-8"))


class TestSpec(unittest.TestCase):
    def test_live_config_matches_spec(self):
        """실제 shorts_config.json이 정본과 완전히 일치해야 한다 (하나라도 빠지면 실패)."""
        issues = check_spec(CONFIG, set(GRADES))
        self.assertEqual(issues, [], "정본 어긋남:\n" + "\n".join(issues))

    def test_palette_intact(self):
        self.assertTrue(GRADE_PALETTE.issubset(set(GRADES)), "필터 팔레트에서 grade가 빠짐")

    def test_detects_grade_changed(self):
        """기본 필터가 정본(bw 흑백)에서 바뀌면 점검이 잡아내야 한다.
        (2026-07-18 이찬호: 이 방=흑백이 기준. warm_film 등으로 덮이면 잡는다.)"""
        bad = json.loads(json.dumps(CONFIG))
        bad["style_preset_mind"]["grade"] = "warm_film"
        self.assertTrue(any("grade" in i or "필터" in i for i in check_spec(bad, set(GRADES))))

    def test_detects_outro_changed(self):
        bad = json.loads(json.dumps(CONFIG))
        bad["style_preset_mind"]["outro_text"] = "저장해두세요"
        issues = check_spec(bad, set(GRADES))
        self.assertTrue(any("outro" in i or "저장" in i for i in issues))

    def test_detects_title_not_bigger(self):
        bad = json.loads(json.dumps(CONFIG))
        bad["style_preset_mind"]["title_style"]["size"] = 90  # 자막 98보다 작게
        self.assertTrue(any("제목" in i for i in check_spec(bad, set(GRADES))))


if __name__ == "__main__":
    unittest.main()
