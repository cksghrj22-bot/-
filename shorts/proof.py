"""시안 배치 렌더러 — 대본 폴더 전체를 편별 고유 그라디언트 배경 + style_preset_v9로 렌더한다.

사용:
    python3 -m shorts.proof content/shorts/2026-07-16 --out content/shorts/2026-07-16/보이스_시안
    python3 -m shorts.proof content/shorts/2026-07-16 --no-tts --out /tmp/시안테스트   # 무음 검증용

- 배경: 편별 고유 그라디언트 플레이스홀더 (발행 렌더는 제작시트의 편별 지정 B롤 원본 — 본진 전담)
- 보이스: secrets/elevenlabs.json이 있고 api.elevenlabs.io가 뚫려 있으면 차노 보이스클론 나레이션 합성.
  네트워크가 차단이면 조용히 무음으로 넘어가지 않고 **에러로 중단**한다 (보이스_시안 폴더에
  무음본이 섞이는 사고 방지). 무음 검증이 목적이면 --no-tts를 명시할 것.
- 산출물은 시안이다. 발행본 아님.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from . import tts
from .render import render
from .subtitles import parse_script

VIDEO_W, VIDEO_H = 1080, 1350  # 레터박스 안쪽 영상 영역 (4:5) — v9 정본 구성
FULL_W, FULL_H = 1080, 1920    # 풀블리드 (dim 레이아웃: 화면 전체 반투명 블랙 + 흰 글씨)
FPS = 30
TAIL_SECONDS = 0.8  # 마지막 자막 뒤 여유

# 편별 고유 그라디언트 팔레트 (2026-07-16 배치용 — 기존 시안과 색 조합 중복 없음)
PALETTES: list[tuple[str, str]] = [
    ("0x1B2A4A", "0xA8B8E8"),  # 01 심야 남색 → 새벽 라벤더
    ("0x2E4A3B", "0xBFE3C0"),  # 02 장마 숲 → 비 갠 민트
    ("0x4A2B3C", "0xF2C1CE"),  # 03 자두 와인 → 벚꽃 핑크
    ("0x3A3A2B", "0xEDE3B5"),  # 04 올리브 → 모래빛
    ("0x1F3A4A", "0x9FD8E8"),  # 05 심해 청록 → 아침 하늘
    ("0x40342B", "0xE8C9A8"),  # 06 에스프레소 → 라떼
    ("0x4A2B2B", "0xF2B8A0"),  # 07 탄 적갈 → 살구 (열손상 편)
    ("0x2B2B4A", "0xC9C1F2"),  # 08 남보라 → 연보라 (사전 편)
    ("0x2B4A4A", "0xB8E8DC"),  # 09 딥 틸 → 여름 쿨민트
    ("0x3C2B4A", "0xE8B8D8"),  # 10 가지 보라 → 석양 로즈
]


def gradient_colors(index: int, slug: str) -> tuple[str, str]:
    """편 번호(1부터)의 고유 색 쌍. 팔레트를 넘어가면 슬러그 해시로 결정적 생성."""
    if 1 <= index <= len(PALETTES):
        return PALETTES[index - 1]
    h = hashlib.sha256(slug.encode("utf-8")).digest()
    dark = f"0x{h[0] % 64:02X}{h[1] % 64:02X}{h[2] % 64:02X}"
    light = f"0x{160 + h[3] % 96:02X}{160 + h[4] % 96:02X}{160 + h[5] % 96:02X}"
    return dark, light


def gradient_cmd(
    colors: tuple[str, str], duration: float, out_path: str | Path,
    size: tuple[int, int] = (VIDEO_W, VIDEO_H),
) -> list[str]:
    """편별 그라디언트 배경(mp4, 무음) 생성 ffmpeg 명령. 대각 방향 + 미세한 흐름."""
    c0, c1 = colors
    w, h = size
    src = (
        f"gradients=s={w}x{h}:c0={c0}:c1={c1}"
        f":x0=0:y0=0:x1={w}:y1={h}:speed=0.01:d={duration:.2f}:r={FPS}"
    )
    return [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", src,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
        str(out_path),
    ]


def find_scripts(scripts_dir: str | Path) -> list[Path]:
    """폴더에서 NN_*.txt 대본을 번호순으로 찾는다."""
    return sorted(Path(scripts_dir).glob("[0-9][0-9]_*.txt"))


BROLL_EXTS = (".mp4", ".mov", ".MOV", ".MP4")


def match_broll(txt_stem: str, broll: str | Path | None) -> Path | None:
    """대본에 배정할 B롤 원본을 찾는다.

    broll이 파일이면 그대로(단일 편 렌더용), 폴더면 대본과 같은 NN_ 접두사의
    영상을 찾는다. 없으면 None → 그라디언트 플레이스홀더로 렌더.
    """
    if broll is None:
        return None
    p = Path(broll)
    if p.is_file():
        return p
    prefix = txt_stem[:3]  # "NN_"
    for ext in BROLL_EXTS:
        hits = sorted(p.glob(f"{prefix}*{ext}"))
        if hits:
            return hits[0]
    return None


def broll_bg_cmd(
    src: str | Path, start: float, duration: float, out_path: str | Path,
    size: tuple[int, int] = (VIDEO_W, VIDEO_H), dim: float = 0.0,
) -> list[str]:
    """B롤 원본을 영상 영역에 맞춰 자른 배경(mp4, 무음) 생성 ffmpeg 명령.

    dim > 0이면 화면 전체에 반투명 블랙을 덮는다 (마인드 라인 스타일 —
    화면 전체가 불투명도 있는 블랙, 그 위에 흰 글씨. 2026-07-14 이찬호 지시).
    """
    w, h = size
    vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={FPS}"
    if dim > 0:
        vf += f",drawbox=c=black@{dim}:t=fill"
    return [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", f"{start:.2f}", "-t", f"{duration:.2f}", "-i", str(src),
        "-vf", vf,
        "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
        str(out_path),
    ]


def render_batch(
    scripts_dir: str | Path,
    out_dir: str | Path,
    use_tts: bool = True,
    config_path: str | Path = "shorts_config.json",
    workdir: str | Path | None = None,
    broll: str | Path | None = None,
    broll_start: float = 0.0,
    preset: str = "style_preset_v9",
    only: str | None = None,
) -> list[Path]:
    cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
    v9 = cfg[preset]
    layout = v9.get("layout", "letterbox")
    if layout == "dim":
        bg_size = (FULL_W, FULL_H)
        dim = float(v9.get("dim_opacity", 0.45))
    else:
        bg_size = (VIDEO_W, VIDEO_H)
        dim = 0.0
    creds = tts.load_credentials(cfg["tts"]["credentials"]) if use_tts else None

    scripts = find_scripts(scripts_dir)
    if only:
        scripts = [s for s in scripts if s.stem.startswith(only)]
    if not scripts:
        raise FileNotFoundError(f"대본 없음: {scripts_dir}/NN_*.txt (only={only})")

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    work = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="shorts_proof_"))
    work.mkdir(parents=True, exist_ok=True)

    outputs: list[Path] = []
    for i, txt in enumerate(scripts, 1):
        script = parse_script(txt.read_text(encoding="utf-8"))
        ends = [l.end for l in script.lines if l.end is not None]
        if not ends:
            raise ValueError(f"타이밍 없는 대본 (시안 렌더는 타이밍 필수): {txt.name}")
        duration = max(ends) + TAIL_SECONDS

        bg = work / f"{txt.stem}_bg.mp4"
        src = match_broll(txt.stem, broll)
        if src is not None:
            subprocess.run(broll_bg_cmd(src, broll_start, duration, bg, size=bg_size, dim=dim), check=True)
        else:
            subprocess.run(gradient_cmd(gradient_colors(i, txt.stem), duration, bg, size=bg_size), check=True)

        narration = None
        if creds:
            narration = tts.build_narration(
                script.lines, creds, work / txt.stem, work / f"{txt.stem}_나레이션.m4a"
            )

        suffix = "보이스시안" if narration else "시안"
        out = render(
            bg, script, out_dir / f"{txt.stem}_{suffix}.mp4",
            style=v9.get("subtitle_style"), title_style=v9.get("title_style"),
            layout="full" if layout == "dim" else layout,  # dim은 배경에 이미 구움
            workdir=work, narration=narration,
        )
        print(f"  ✅ {out.name}")
        outputs.append(out)
    return outputs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="시안 배치 렌더 (그라디언트 배경 + v9 + 보이스클론)")
    ap.add_argument("scripts_dir")
    ap.add_argument("--out", required=True, help="출력 폴더")
    ap.add_argument("--no-tts", action="store_true", help="나레이션 없이 무음 시안 (검증용)")
    ap.add_argument("--config", default="shorts_config.json")
    ap.add_argument("--workdir", default=None, help="중간 파일 폴더 (기본: 임시폴더)")
    ap.add_argument("--broll", default=None,
                    help="배경 원본: 파일(전 편 공통) 또는 폴더(NN_ 접두사 매칭). 없으면 그라디언트")
    ap.add_argument("--broll-start", type=float, default=0.0, help="B롤 시작 지점(초)")
    ap.add_argument("--preset", default="style_preset_v9", help="shorts_config.json의 스타일 프리셋 키")
    ap.add_argument("--only", default=None, help="이 접두사(NN)로 시작하는 대본만 렌더")
    args = ap.parse_args(argv)
    try:
        outs = render_batch(args.scripts_dir, args.out, use_tts=not args.no_tts,
                            config_path=args.config, workdir=args.workdir,
                            broll=args.broll, broll_start=args.broll_start,
                            preset=args.preset, only=args.only)
    except OSError as e:
        print(f"❌ 중단: {e}\n   api.elevenlabs.io 차단이면 네트워크 정책 확인 (연결지도.md), "
              f"무음 검증은 --no-tts.", file=sys.stderr)
        return 1
    print(f"🎬 {len(outs)}편 완료 → {args.out} (시안 — 발행본 아님)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
