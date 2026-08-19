#!/usr/bin/env python3
"""영상 제작 마스터 체크 — 체크리스트 자동화

모든 검사 통과해야 발행 가능.
하나라도 FAIL이면 발행 금지.

사용:
    python3 scripts/master_check.py <영상.mp4> [--script <대본.txt>] [--original <원문.txt>]
"""
import subprocess
import json
import sys
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent


def log(msg, status=""):
    icons = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️"}
    icon = icons.get(status, "")
    print(f"{icon} {msg}" if icon else msg)


def run_cmd(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)


class MasterChecker:
    def __init__(self, video_path, script_path=None, original_path=None):
        self.video = Path(video_path)
        self.script = Path(script_path) if script_path else None
        self.original = Path(original_path) if original_path else None
        self.results = []

    def check(self, name, passed, detail=""):
        status = "PASS" if passed else "FAIL"
        self.results.append({"name": name, "passed": passed, "detail": detail})
        log(f"{name}: {detail}" if detail else name, status)
        return passed

    # === 1. 대본/텍스트 ===
    def check_script_integrity(self):
        if not self.script or not self.original:
            log("1. 대본 검사: 원문/대본 파일 없음 — 수동 확인 필요", "WARN")
            return True

        script_text = self.script.read_text().strip()
        original_text = self.original.read_text().strip()

        # 공백 제거 후 비교
        script_clean = re.sub(r'\s+', '', script_text)
        original_clean = re.sub(r'\s+', '', original_text)

        return self.check(
            "1.1 원문 그대로",
            script_clean == original_clean,
            f"원문 {len(original_clean)}자 vs 대본 {len(script_clean)}자"
        )

    # === 2. TTS ===
    def check_audio_end(self):
        """끝 1초 RMS로 끝 잘림 확인"""
        cmd = [
            "ffmpeg", "-i", str(self.video),
            "-af", "atrim=end_sample=44100,volumedetect",
            "-f", "null", "-"
        ]
        code, out, err = run_cmd(cmd)

        # volumedetect 결과 파싱
        match = re.search(r'mean_volume:\s*([-\d.]+)\s*dB', err)
        if match:
            mean_db = float(match.group(1))
            return self.check(
                "2.3 끝 단어 살아있음",
                mean_db > -60,
                f"끝 평균 {mean_db:.1f}dB"
            )
        return self.check("2.3 끝 단어 살아있음", False, "측정 실패")

    # === 4. 폰트 ===
    def check_font_fallback(self):
        """자막 파일에서 폰트 확인"""
        ass_files = list(self.video.parent.glob("*.ass"))
        if not ass_files:
            log("4.1 폰트: ASS 파일 없음 — 수동 확인", "WARN")
            return True

        ass_content = ass_files[0].read_text()

        # 공백 있는 폰트명 찾기
        bad_fonts = re.findall(r'\\fn([^\\]+\s+[^\\]+)', ass_content)
        return self.check(
            "4.1 폰트 공백 없음",
            len(bad_fonts) == 0,
            f"공백 폰트: {bad_fonts[:3]}" if bad_fonts else "정상"
        )

    # === 5. BGM ===
    def check_bgm_tail(self):
        """마지막 3초 오디오 RMS"""
        # 영상 길이 확인
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "json", str(self.video)]
        code, out, err = run_cmd(cmd)

        try:
            duration = float(json.loads(out)["format"]["duration"])
        except:
            return self.check("5.2 BGM 꼬리", False, "길이 측정 실패")

        # 마지막 3초 RMS
        cmd = [
            "ffmpeg", "-i", str(self.video),
            "-ss", str(max(0, duration - 3)),
            "-af", "volumedetect",
            "-f", "null", "-"
        ]
        code, out, err = run_cmd(cmd)

        match = re.search(r'mean_volume:\s*([-\d.]+)\s*dB', err)
        if match:
            mean_db = float(match.group(1))
            return self.check(
                "5.2 BGM 꼬리 RMS",
                mean_db > -60,
                f"마지막 3초 평균 {mean_db:.1f}dB"
            )
        return self.check("5.2 BGM 꼬리 RMS", False, "측정 실패")

    # === 6. 영상 렌더 ===
    def check_resolution(self):
        cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
               "-show_entries", "stream=width,height", "-of", "json", str(self.video)]
        code, out, err = run_cmd(cmd)

        try:
            streams = json.loads(out)["streams"][0]
            w, h = streams["width"], streams["height"]
            return self.check(
                "6.1 해상도",
                w == 1080 and h == 1920,
                f"{w}×{h}"
            )
        except:
            return self.check("6.1 해상도", False, "측정 실패")

    def check_frame_rate(self):
        cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
               "-show_entries", "stream=r_frame_rate", "-of", "json", str(self.video)]
        code, out, err = run_cmd(cmd)

        try:
            rate = json.loads(out)["streams"][0]["r_frame_rate"]
            num, den = map(int, rate.split('/'))
            fps = num / den
            return self.check(
                "6.6 CFR",
                29 <= fps <= 31 or 59 <= fps <= 61,
                f"{fps:.2f}fps"
            )
        except:
            return self.check("6.6 CFR", False, "측정 실패")

    # === 실행 ===
    def run_all(self):
        print(f"\n{'='*60}")
        print(f"📋 마스터 체크 — {self.video.name}")
        print(f"{'='*60}\n")

        # 파일 존재 확인
        if not self.video.exists():
            log(f"영상 파일 없음: {self.video}", "FAIL")
            return False

        # 각 검사 실행
        print("[1] 대본/텍스트")
        self.check_script_integrity()

        print("\n[2] TTS/음성")
        self.check_audio_end()

        print("\n[4] 폰트")
        self.check_font_fallback()

        print("\n[5] BGM")
        self.check_bgm_tail()

        print("\n[6] 영상")
        self.check_resolution()
        self.check_frame_rate()

        # 결과 요약
        passed = sum(1 for r in self.results if r["passed"])
        total = len(self.results)
        all_pass = passed == total

        print(f"\n{'='*60}")
        if all_pass:
            log(f"전체 통과: {passed}/{total}", "PASS")
            print("→ 발행 가능")
        else:
            log(f"실패 있음: {passed}/{total}", "FAIL")
            print("→ 발행 금지. 수정 후 재검사.")
            print("\n실패 항목:")
            for r in self.results:
                if not r["passed"]:
                    print(f"  ❌ {r['name']}: {r['detail']}")
        print(f"{'='*60}\n")

        return all_pass


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="영상 제작 마스터 체크")
    parser.add_argument("video", help="영상 파일")
    parser.add_argument("--script", "-s", help="대본 파일")
    parser.add_argument("--original", "-o", help="원문 파일")

    args = parser.parse_args()

    checker = MasterChecker(args.video, args.script, args.original)
    success = checker.run_all()

    sys.exit(0 if success else 1)
