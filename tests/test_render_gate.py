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


if __name__ == "__main__":
    unittest.main()
