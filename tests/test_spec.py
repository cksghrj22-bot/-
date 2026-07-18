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

    def test_detects_dim_dropped(self):
        """dim이 꺼지면(0.0) 점검이 잡아내야 한다 (예전 실수 재현)."""
        bad = json.loads(json.dumps(CONFIG))
        bad["style_preset_mind"]["dim_opacity"] = 0.0
        self.assertTrue(any("dim" in i for i in check_spec(bad, set(GRADES))))

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
