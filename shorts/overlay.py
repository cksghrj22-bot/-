"""이미지 오버레이 합성기 — 렌더된 영상 위에 누끼(투명배경 PNG)를 시각·위치 지정해 페이드로 얹는다.

원용중 릴스류 '참고 사진 팝업' 포맷(이찬호 2026-07-21): 말하는 영상 위에 어울리는 머리 예시
컷을 띄워 설명. 사진은 Adobe(Firefly) 배경제거로 누끼 → 이 모듈이 시각·위치·페이드로 합성.

overlay spec = {"png": 경로, "start": 초, "end": 초, "pos": "mid-left|mid-right|center|...",
                "scale": 화면폭 대비 비율(0~1), "fade": 초}
컬러 PNG면 흑백 영상 위에서 톡 튄다(이찬호 '컬러로' 지시). 한 번에 ≤2장 권장.
"""
from __future__ import annotations
import subprocess
from pathlib import Path

W, H = 1080, 1920

# 위치 프리셋 → (x, y) 식. iw/ih=오버레이 크기, W/H=캔버스. 제목(상단)·자막(하단) 안 가리게 중간대.
POS = {
    "mid-left":  ("40", "H*0.30"),
    "mid-right": (f"{W}-w-40", "H*0.30"),
    "center":    ("(W-w)/2", "H*0.34"),
    "lower-left":  ("40", "H*0.52"),
    "lower-right": (f"{W}-w-40", "H*0.52"),
}


def build_overlay_cmd(video: str | Path, overlays: list[dict], out: str | Path) -> list[str]:
    """ffmpeg 명령을 만든다. overlays 각각을 scale→fade→overlay(enable 구간) 체인으로 얹는다."""
    video, out = str(video), str(out)
    cmd = ["ffmpeg", "-y", "-i", video]
    # 정지 PNG는 -loop 1 로 스트림화해야 fade(st=절대시각)가 동작한다.
    # (단일 프레임이면 fade가 t=start에 못 닿아 알파 0으로 투명해지는 버그)
    for ov in overlays:
        cmd += ["-loop", "1", "-framerate", "30", "-i", str(ov["png"])]
    parts = []
    last = "[0:v]"
    for i, ov in enumerate(overlays, start=1):
        scale = float(ov.get("scale", 0.34))
        fade = float(ov.get("fade", 0.3))
        s, e = float(ov["start"]), float(ov["end"])
        pos = ov.get("pos", "mid-right")
        x_expr, y_expr = POS.get(pos, POS["mid-right"])
        tw = int(W * scale)
        # 스케일 + 알파 페이드 in/out (투명배경 유지 위해 format rgba)
        parts.append(
            f"[{i}:v]scale={tw}:-1,format=rgba,"
            f"fade=t=in:st={s:.2f}:d={fade}:alpha=1,"
            f"fade=t=out:st={e - fade:.2f}:d={fade}:alpha=1[ov{i}]"
        )
        outlab = f"[v{i}]" if i < len(overlays) else "[vout]"
        parts.append(
            f"{last}[ov{i}]overlay=x={x_expr}:y={y_expr}:"
            f"enable='between(t,{s:.2f},{e:.2f})'{outlab}"
        )
        last = f"[v{i}]"
    filt = ";".join(parts)
    cmd += ["-filter_complex", filt, "-map", "[vout]", "-map", "0:a?",
            "-c:a", "copy", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            "-shortest", out]  # -loop 1 이미지가 무한이라 -shortest로 본영상 길이에 맞춤
    return cmd


def apply_overlays(video: str | Path, overlays: list[dict], out: str | Path) -> Path:
    cmd = build_overlay_cmd(video, overlays, out)
    subprocess.run(cmd, check=True, capture_output=True)
    return Path(out)


if __name__ == "__main__":
    import sys, json
    video, spec_json, out = sys.argv[1], sys.argv[2], sys.argv[3]
    overlays = json.loads(spec_json)
    apply_overlays(video, overlays, out)
    print("overlay 완료 →", out)
