"""shorts.make — 대본(매니페스트) 1개 → 완성본 1개. **단일 명령**(2026-07-28 이찬호 지시).

형 정곡: "박제가 글이라 매번 내가 읽어야 발동한다. 영상마다 손으로 스크립트를 새로 짜니 매번 새 버그다.
대본 1개 넣으면 완성본 1개 나오는 단일 명령을 만들어야 한다." → 이 파일이 그 명령이다.
손으로 하던 TTS→footage 조립→애니 오버레이→자막·BGM 렌더를 **매니페스트 하나로** 결정론적으로 돌린다.
영상마다 코드를 새로 안 짠다 = 새 버그가 없다. 본진 크론이 대본 큐를 밤새 이걸로 돌리면 형 없이 돈다.

규칙(코드로 박힘 — 안 틀림): 교보 자막·타임스탬프 싱크(syncbuild)·정사각 4:5+밴드·진한 스크림 애니·
footage 스트리밍 추출(drive_stream, 통다운 금지)·중앙 훅/엔딩 카드·아웃트로 카드.

매니페스트(JSON) 스키마:
{
  "title": "메타안경 산 후기",
  "voice": {"stability":0.42,"style":0.15,"speed":1.05},   # 생략 시 기본 자연톤
  "bgm": "<scratch내 mp3 파일명 or 절대경로>",
  "outro": "SNS에 일기를 쓰고 있어요",                       # 없으면 아웃트로 없음
  "phrases": [["raw(합성/정렬)","disp(자막·\\N줄바꿈)","en 또는 null", false], ...],
  "segments": [                                             # 시간축 순서대로(빈틈 없이 total 채움)
    {"black": true, "untilLine": 0},                        # 훅 검은카드 (line index 0까지)
    {"src":"<fileId>","ss":6,"hflip":true,"frame":"landscape","untilLine":3},   # 언박싱 beat
    {"src":"<consultId>","ss":2,"frame":"portrait","untilLine":10},             # 상담 인서트
    {"black": true, "untilLine": 13, "tail": 3.4}           # 엔딩 검은카드 + 아웃트로 여유
  ],
  "overlays": [ {"type":"value_gap","fromLine":2,"toLine":4} ]   # 데이터 애니(선택)
}
※ 각 segment 시간 = [직전 segment 끝, lines[untilLine].end]. footage는 그 길이에 맞춰 잘림.
※ black segment에 걸린 자막 줄은 자동 중앙정렬(\an5). 마지막 black의 tail(초)만큼 영상 뒤 여유+아웃트로.

쓰는 법:
    python3 -m shorts.make content/manifests/메타안경.json [--out out.mp4] [--workdir DIR]
"""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

from .subtitles import Script, Line
from . import tts, syncbuild, render as R, shortstyle as SS, drive_stream as DS

ROOT = Path(__file__).resolve().parent.parent
SECRETS = ROOT / "secrets" / "elevenlabs.json"
KYOBO = "/root/.fonts/KyoboHandwriting2019.ttf"
NSQR = "/root/.fonts/nsqr_eb.ttf"


def _frame_vf(frame: str, hflip: bool) -> str:
    fl = "hflip," if hflip else ""
    if frame == "portrait":
        return (f"{fl}scale=1080:1350:force_original_aspect_ratio=increase,"
                "crop=1080:1350,pad=1080:1920:0:285:black,fps=30")
    # landscape(기본): 4:5 확대크롭 + 상하밴드
    return f"{fl}crop=ih*4/5:ih,scale=1080:1350,pad=1080:1920:0:285:black,fps=30"


# ── 데이터 애니: 가치 격차(소득 100만 vs 버는 능력 → 9억9,900만) ─────────────────
def _value_gap_frames(frames_dir: Path, lines: list, i3: int, i4: int, i5: int, fps: int = 30) -> tuple[float, float]:
    """line i3(소득)·i4(능력)·i5(격차) 타이밍에 맞춰 단계 등장. 반환 (offset_sec, end_sec)."""
    from PIL import Image, ImageDraw, ImageFont
    frames_dir.mkdir(parents=True, exist_ok=True)
    for p in frames_dir.glob("*.png"):
        p.unlink()
    l3, l4, l5 = lines[i3], lines[i4], lines[i5]
    off, end = l3.start, l5.end
    N = max(1, round((end - off) * fps))
    f_lab = ImageFont.truetype(KYOBO, 50); f_num = ImageFont.truetype(NSQR, 54)
    f_bigk = ImageFont.truetype(KYOBO, 54); f_big = ImageFont.truetype(NSQR, 104)
    YEL = (255, 212, 0, 255); BLUE = (120, 190, 255, 255); WHITE = (245, 245, 245, 255); GREY = (185, 195, 205, 255)
    W, H = 1080, 1920

    def sm(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

    def ctext(d, cx, y, txt, fnt, fill):
        ws = txt.split(" "); gap = fnt.size * 0.30; wd = [d.textlength(w, font=fnt) for w in ws]
        tot = sum(wd) + gap * (len(ws) - 1); x = cx - tot / 2
        for w, ww in zip(ws, wd):
            d.text((x, y), w, font=fnt, fill=fill); x += ww + gap

    def kmoney(w):
        eok = w // 10**8; man = (w % 10**8) // 10**4
        return (f"{eok}억 {man:,}만" if man else f"{eok}억") if eok else f"{man:,}만"

    def a(v):  # alpha tuple helper
        return int(255 * max(0.0, min(1.0, v)))

    LX, RX, B, MAXH, IH = 320, 760, 1230, 600, 40
    for i in range(N):
        t = off + i / fps
        si = sm((t - l3.start) / max(0.3, l3.end - l3.start))          # 소득 등장
        ai = sm((t - l4.start) / max(0.3, l4.end - l4.start))          # 능력 등장
        gp = sm((t - l5.start) / max(0.3, l5.end - l5.start))          # 격차 성장/롤업
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
        edge = min(1.0, i / 12, (N - 1 - i) / 12)
        d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(214 * edge)))     # 진한 스크림
        # 좌: 소득 100만
        if si > 0:
            d.rounded_rectangle([LX - 78, B - IH, LX + 78, B], radius=14, outline=(*BLUE[:3], a(si)), width=5, fill=(20, 50, 80, a(si)))
            ctext(d, LX, 470, "소득", f_lab, (*BLUE[:3], a(si)))
            ctext(d, LX, B + 22, "100만 원", f_lab, (*BLUE[:3], a(si)))
        # 우: 버는 능력 (등장 후 격차구간에 성장)
        if ai > 0:
            ctext(d, RX, 470, "버는 능력", f_lab, (*YEL[:3], a(ai)))
            h = IH + (MAXH - IH) * gp
            d.rounded_rectangle([RX - 78, B - h, RX + 78, B], radius=16, outline=(*YEL[:3], a(ai)), width=5, fill=(70, 58, 0, a(ai)))
            if gp <= 0.80:
                ctext(d, RX, B + 22, kmoney(int(10 ** (6 + 3 * gp))) + " 원", f_num, (*YEL[:3], a(min(ai, 1) * (1 if gp <= 0.8 else 0))))
        # 격차 임팩트(끝)
        if gp > 0.80:
            aa = sm((gp - 0.80) / 0.20)
            ctext(d, W / 2, 820, "가치 차이", f_bigk, (*GREY[:3], a(aa)))
            ctext(d, W / 2, 890, "9억 9,900만 원", f_big, (*YEL[:3], a(aa)))
        img.save(frames_dir / f"a{i:04d}.png")
    return off, end


def make(manifest_path: str | Path, out: str | Path | None = None,
         workdir: str | Path | None = None) -> Path:
    m = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    wd = Path(workdir) if workdir else Path(manifest_path).resolve().parent / "_build"
    wd.mkdir(parents=True, exist_ok=True)

    # 1) TTS + 타임스탬프 싱크
    creds = tts.load_credentials(SECRETS)
    v = m.get("voice", {})
    creds["voice_settings"] = {**creds["voice_settings"],
                               **{k: v[k] for k in ("stability", "style", "similarity_boost") if k in v}}
    creds["speed"] = v.get("speed", creds.get("speed"))
    phrases = [tuple(p) for p in m["phrases"]]
    narr = " ".join(p[0] for p in phrases)
    lines, narr_path = syncbuild.build(narr, phrases, creds, wd / "narr.mp3")
    total = max(l.end for l in lines)

    # 2) 세그먼트 → 연속 base (footage 스트리밍 추출 + 검은카드)
    tok = DS.access_token()
    seg_files = []
    prev_end = 0.0
    black_line_idx = set()
    tail = 0.0
    for k, seg in enumerate(m["segments"]):
        seg_end = lines[seg["untilLine"]].end
        seg_tail = float(seg.get("tail", 0.0))
        dur = max(0.1, seg_end - prev_end) + seg_tail
        tail += seg_tail
        out_seg = wd / f"seg_{k:02d}.mp4"
        if seg.get("black"):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
                            "-i", f"color=black:s=1080x1920:r=30:d={dur:.3f}",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", str(out_seg)], check=True)
            for li, ln in enumerate(lines):
                mid = (ln.start + ln.end) / 2
                if prev_end <= mid < seg_end:
                    black_line_idx.add(li)
        else:
            DS.extract(seg["src"], seg["ss"], dur, out_seg,
                       vf=_frame_vf(seg.get("frame", "landscape"), seg.get("hflip", False)),
                       tok=tok)
        seg_files.append(out_seg)
        prev_end = seg_end
    video_total = total + tail

    base = wd / "base.mp4"
    # 세그먼트별 인코드 파라미터가 미세하게 달라도 안전하게 재인코딩 concat(글리치 방지).
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for p in seg_files:
        cmd += ["-i", str(p)]
    fc = "".join(f"[{i}:v]" for i in range(len(seg_files))) + f"concat=n={len(seg_files)}:v=1:a=0[base]"
    cmd += ["-filter_complex", fc, "-map", "[base]", "-r", "30",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", str(base)]
    subprocess.run(cmd, check=True)

    # 3) 오버레이(데이터 애니)
    comp = base
    for j, ov in enumerate(m.get("overlays", [])):
        if ov["type"] == "value_gap":
            fdir = wd / f"anim_{j}"
            off, end = _value_gap_frames(fdir, lines, ov["fromLine"], ov["fromLine"] + 1, ov["toLine"])
            nxt = wd / f"comp_{j}.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(comp),
                            "-itsoffset", f"{off:.3f}", "-framerate", "30", "-i", str(fdir / "a%04d.png"),
                            "-filter_complex",
                            f"[0][1]overlay=0:0:enable='between(t,{off:.3f},{end + 0.1:.3f})':format=auto[v]",
                            "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", str(nxt)], check=True)
            comp = nxt

    # 4) 자막 Line(훅/엔딩=검은카드 중앙) + 렌더
    tl = []
    for li, ln in enumerate(lines):
        txt = (r"{\an5}" + ln.text) if li in black_line_idx else ln.text
        tl.append(Line(text=txt, start=ln.start, end=ln.end))
    script = Script(lines=tl, title=None)

    bgm = m.get("bgm")
    if bgm and not Path(bgm).is_absolute():
        cand = wd / bgm
        bgm = str(cand) if cand.exists() else bgm
    out_path = Path(out) if out else wd / (m.get("title", "output").replace(" ", "_") + ".mp4")
    R.render(str(comp), script, str(out_path),
             bgm=bgm, bgm_volume=SS.BGM_VOLUME, style=SS.SUB, layout="full",
             workdir=str(wd), narration=str(narr_path),
             outro=m.get("outro"), outro_style=SS.OUTRO_CARD if m.get("outro") else None)
    return out_path


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="대본(매니페스트) → 완성본 단일 명령")
    ap.add_argument("manifest")
    ap.add_argument("--out", default=None)
    ap.add_argument("--workdir", default=None)
    a = ap.parse_args(argv)
    p = make(a.manifest, out=a.out, workdir=a.workdir)
    print(f"✅ 완성본: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
