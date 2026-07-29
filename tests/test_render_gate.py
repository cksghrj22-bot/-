"""출력 게이트 잠금 테스트 — 정해놓은 표준이 조용히 무너지지 않게 코드로 못 박는다.

배경(2026-07-21 사고): 기본 프리셋이 컬러(v9)로 새고, 규격 게이트가 'grayscale일 때만'
돌아 흑백 검사를 건너뜀 → 컬러 시안이 그대로 나감. "실수다"로 넘기지 않고 게이트를 뜯어
①기본=흑백 ②게이트 무조건 실행 ③길이 40~50 을 코드로 잠근다. 이 테스트가 그 잠금이다.
"""
import inspect
import json
import re
import unittest
from pathlib import Path

from shorts import proof
from shorts import verify_render


class TestDefaultPresetIsGrayscale(unittest.TestCase):
    """기본 프리셋은 반드시 흑백(mind). 잊어도 컬러로 안 샌다."""

    def test_render_batch_default_preset_is_mind(self):
        default = inspect.signature(proof.render_batch).parameters["preset"].default
        self.assertEqual(default, "style_preset_mind")

    def test_cli_default_preset_is_mind(self):
        # argparse 기본값도 mind 여야 한다 (소스에서 확인 — 파서가 main 지역변수라 소스 검증).
        src = Path(proof.__file__).read_text(encoding="utf-8")
        m = re.search(r'add_argument\(\s*"--preset"\s*,\s*default="([^"]+)"', src)
        self.assertIsNotNone(m, "--preset 기본값 정의를 못 찾음")
        self.assertEqual(m.group(1), "style_preset_mind")

    def test_config_default_preset_actually_grayscale(self):
        cfg = json.loads(Path("shorts_config.json").read_text(encoding="utf-8"))
        self.assertTrue(cfg["style_preset_mind"].get("grayscale"),
                        "style_preset_mind 이 흑백이 아님 — 기본 룩이 깨짐")


class TestGateRunsUnconditionally(unittest.TestCase):
    """게이트가 grayscale 조건에 묶이면 컬러가 검사를 건너뛴다 → 조건 없이 돌아야 한다."""

    def test_gate_not_conditioned_on_grayscale(self):
        src = Path(proof.__file__).read_text(encoding="utf-8")
        # 회귀 방지: 'if verify and v9.get("grayscale")' 형태가 다시 생기면 실패.
        self.assertNotRegex(
            src, r'if\s+verify\s+and\s+v9\.get\(\s*["\']grayscale',
            "게이트가 grayscale 조건에 다시 묶임 — 컬러가 검사를 건너뛴다",
        )
        self.assertRegex(src, r'if\s+verify\s*:', "무조건 게이트(if verify:)가 없음")


class TestLengthGate(unittest.TestCase):
    """길이 40~50초 잠금 — 25초처럼 짧거나 50 넘으면 FAIL."""

    def test_too_short_fails(self):
        # 바닥 24초 — 그 밑(잘림버그 등 파손)만 FAIL (이찬호 2026-07-21 "28초도 괜찮아")
        self.assertTrue(verify_render.length_fails(20))
        self.assertTrue(verify_render.length_fails(23))

    def test_in_range_passes(self):
        # 24초 이상 ~ 45초 미만 (이찬호 2026-07-21 "28초도 괜찮아" → 바닥 30→24)
        self.assertEqual(verify_render.length_fails(28), [])
        self.assertEqual(verify_render.length_fails(32), [])
        self.assertEqual(verify_render.length_fails(39), [])
        self.assertEqual(verify_render.length_fails(44), [])

    def test_too_long_fails(self):
        self.assertTrue(verify_render.length_fails(50))
        self.assertTrue(verify_render.length_fails(48))

    def test_longform_allows_up_to_90s(self):
        # 육성 롱폼(버그#13): 상한 90초. 55초는 쇼츠기준 FAIL이지만 롱폼은 통과.
        self.assertTrue(verify_render.length_fails(55))               # 쇼츠 기준 FAIL
        self.assertEqual(verify_render.length_fails(55, longform=True), [])  # 롱폼 통과
        self.assertEqual(verify_render.length_fails(88, longform=True), [])
        self.assertTrue(verify_render.length_fails(95, longform=True))  # 롱폼도 90 넘으면 FAIL
        # 롱폼도 바닥 24초는 유지(파손 방어)
        self.assertTrue(verify_render.length_fails(20, longform=True))

    def test_verify_accepts_longform_kwarg(self):
        self.assertIn("longform", inspect.signature(verify_render.verify).parameters)

    def test_verify_accepts_duration_kwarg(self):
        # 렌더가 정확한 길이를 넘길 수 있어야 한다(ffmpeg 측정 플레이크 방어).
        self.assertIn("duration", inspect.signature(verify_render.verify).parameters)


class TestOutroDefaultOn(unittest.TestCase):
    """SNS 아웃트로가 '고쳐도 계속 빠지는' 것을 구조로 잠근다(형 2026-07-29).

    배경: 아웃트로가 opt-in(매니페스트에 매번 넣어야 발동)이라 새 매니페스트마다 깜빡하면 누락 +
    waive로 조용히 빠짐 → 부시시편에서 두 번 빠짐. 이제 default-on(자동주입)·waive는 사유 강제로 잠근다.
    """

    def _base(self, **extra):
        m = {"stem": "message", "phrases": [["훅", "훅", None, False]],
             "segments": [{"black": True, "bigcard": True, "untilLine": 0}]}
        m.update(extra)
        return m

    def test_outro_auto_injected_when_missing(self):
        # message/mind/product는 outro가 없어도 _normalize가 표준값을 자동으로 넣는다.
        from shorts import make
        for stem in ("message", "mind", "product"):
            m = self._base(stem=stem)
            self.assertNotIn("outro", m)
            make._normalize(m)
            self.assertEqual(m.get("outro"), make.DEFAULT_SNS_OUTRO,
                             f"{stem}: 아웃트로 자동주입 실패 — default-on이 깨졌다")

    def test_outro_not_injected_when_waived(self):
        # 명시적으로 waive했으면 자동주입하지 않는다(의도 존중).
        from shorts import make
        m = self._base(waive=["outro"])
        make._normalize(m)
        self.assertNotIn("outro", m)

    def test_waive_outro_requires_reason(self):
        # 아웃트로를 뺐는데 _notes 사유가 없으면 게이트가 막는다(조용한 누락 차단).
        # bw·bigcard도 waive해 다른 게이트를 배제 → 오직 '아웃트로 사유 없음'만 남게 격리.
        from shorts import make
        m = self._base(waive=["outro", "bw", "bigcard"])   # _notes 없음
        with self.assertRaises(ValueError) as cm:
            make._require(m)
        self.assertIn("outro", str(cm.exception))

    def test_waive_outro_with_reason_passes(self):
        from shorts import make
        m = self._base(waive=["outro", "bw", "bigcard"], _notes="의도적으로 뺀 사유 있음")
        make._require(m)   # 사유 있으면 통과(예외 없음)

    def test_ensure_outro_tail_prevents_collision(self):
        # 마지막이 중앙 카드(bigcard)이고 tail이 부족하면 아웃트로와 겹친다 → 자동으로 tail을 늘린다.
        from shorts import make
        from shorts import shortstyle as SS
        outro_dur = float(SS.OUTRO_CARD.get("dur", 2.6))
        m = self._base(outro=make.DEFAULT_SNS_OUTRO,
                       segments=[{"black": True, "bigcard": True, "untilLine": 0, "tail": 0.5}])
        make._ensure_outro_tail(m)
        total_tail = sum(float(s.get("tail", 0.0)) for s in m["segments"])
        self.assertGreaterEqual(total_tail, outro_dur,
                                "아웃트로↔엔딩카드 충돌방지 tail 자동확보 실패")

    def test_ensure_outro_tail_noop_without_outro(self):
        # 아웃트로가 없으면 tail을 건드리지 않는다.
        from shorts import make
        m = self._base(segments=[{"black": True, "bigcard": True, "untilLine": 0, "tail": 0.5}])
        make._ensure_outro_tail(m)
        self.assertEqual(m["segments"][-1]["tail"], 0.5)


if __name__ == "__main__":
    unittest.main()
