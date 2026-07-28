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


def _frame_vf(frame: str, hflip: bool, bw: bool = False, zoom: float = 1.0) -> str:
    fl = "hflip," if hflip else ""
    gray = ",hue=s=0" if bw else ""   # 흑백(마인드/메시지 줄기)
    w, h = round(1080 * zoom), round(1350 * zoom)   # zoom>1 = 인물 확대(배경 줄임)
    if frame == "portrait":
        return (f"{fl}scale={w}:{h}:force_original_aspect_ratio=increase,"
                f"crop=1080:1350,pad=1080:1920:0:285:black,fps=30{gray}")
    # landscape(기본): 4:5 확대크롭 + 상하밴드
    return f"{fl}crop=ih*4/5:ih,scale={w}:{h},crop=1080:1350,pad=1080:1920:0:285:black,fps=30{gray}"


# ── 화이팅 애니: 주먹을 들어올리는 데이터 모션(흑백 위 노랑 포인트) ───────────────
def _fist_raise_frames(frames_dir: Path, lines: list, line_idx: int, fps: int = 30) -> tuple[float, float]:
    """line_idx(화이팅 줄) 구간에 주먹이 아래→위로 솟구치고 '화이팅!'이 터진다. RGBA 오버레이."""
    from PIL import Image, ImageDraw, ImageFont
    frames_dir.mkdir(parents=True, exist_ok=True)
    for p in frames_dir.glob("*.png"):
        p.unlink()
    ln = lines[line_idx]; off, end = ln.start, ln.end
    N = max(1, round((end - off) * fps))
    W, H = 1080, 1920
    YEL = (255, 212, 0); WHITE = (245, 245, 245)
    f_big = ImageFont.truetype(NSQR, 132); f_k = ImageFont.truetype(KYOBO, 44)

    def ease_out(t): t = max(0, min(1, t)); return 1 - (1 - t) ** 3

    def fist(d, cx, cy, s, col):
        # 스타일 주먹(플랫): 손등 라운드+너클 4개+엄지+팔뚝
        bw_, bh_ = int(150*s), int(130*s)
        d.rounded_rectangle([cx-bw_//2, cy-bh_//2, cx+bw_//2, cy+bh_//2], radius=int(26*s), fill=col)
        kw = bw_ // 4
        for i in range(4):  # 너클
            kx = cx - bw_//2 + kw//2 + i*kw
            d.ellipse([kx-int(15*s), cy-bh_//2-int(14*s), kx+int(15*s), cy-bh_//2+int(16*s)], fill=col)
        d.ellipse([cx-bw_//2-int(20*s), cy-int(6*s), cx-bw_//2+int(20*s), cy+int(46*s)], fill=col)  # 엄지
        d.rounded_rectangle([cx-int(46*s), cy+bh_//2-int(6*s), cx+int(46*s), cy+bh_//2+int(150*s)],
                            radius=int(22*s), fill=col)  # 팔뚝

    for i in range(N):
        t = i / (N - 1) if N > 1 else 1.0
        p = ease_out(t)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
        edge = min(1.0, i/8, (N-1-i)/6)
        d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(150 * edge)))   # 부드러운 스크림
        cy = int(1500 - 560 * p)          # 아래→위로 솟구침
        # 스피드 라인(상승감)
        for k in range(5):
            lx = W//2 - 200 + k*100
            a = int(140 * max(0.0, min(1.0, (p-0.15)*2)) * (1 if (i//2 + k) % 2 else 0.5))
            d.line([(lx, cy+260), (lx, cy+430)], fill=(*YEL, a), width=6)
        fist(d, W//2, cy, 1.0, WHITE)
        if p > 0.55:                      # 화이팅! 터짐
            a = ease_out((p-0.55)/0.45)
            tx = "화이팅!"; tw = d.textlength(tx, font=f_big)
            d.text((W/2 - tw/2, cy-330), tx, font=f_big, fill=(*YEL, int(255*a)))
        img.save(frames_dir / f"f{i:04d}.png")
    return off, end


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


# ── 데이터 애니: 볼륨매직 두상 존-% 도식(실사 아님) ───────────────────────────
def _dusang_zones_frames(frames_dir: Path, lines: list, num_line: int, total: float, fps: int = 30) -> None:
    """두상 원 + 존별(톱/페이스/백/네이프) % 도식. num_line(퍼센트 나열 줄) 구간에 존 순차 등장."""
    from PIL import Image, ImageDraw, ImageFont
    frames_dir.mkdir(parents=True, exist_ok=True)
    for p in frames_dir.glob("*.png"):
        p.unlink()
    W, H = 1080, 1920
    BG = (18, 20, 26); CX, CY, R = 540, 930, 250
    f_title = ImageFont.truetype(KYOBO, 92); f_lab = ImageFont.truetype(KYOBO, 38)
    f_pct = ImageFont.truetype(NSQR, 64); f_why = ImageFont.truetype(KYOBO, 20)
    BLUE=(120,190,255); GREEN=(130,220,150); YEL=(255,212,0); ORANGE=(255,140,60); GREY=(150,158,170)
    # 각 존은 자기 나레이션 줄(num_line, +1, +2, +3)에서 등장. 마지막 줄 없으면 num_line 기준 분할.
    def _z0(k):
        idx = num_line + k
        return lines[idx].start if idx < len(lines) else lines[num_line].start + k * 0.9
    # (라벨,색,목표%,박스중심,원위연결점,등장시각,호각도)
    Z = [
        ("정수리",     BLUE,   10, (430,555),  (CX, CY-R),       _z0(0), (-108,-72)),
        ("페이스라인", GREEN,  30, (250,860),  (CX-R+18,CY-30),  _z0(1), (150,210)),
        ("뒤통수",     YEL,    15, (830,860),  (CX+R-18,CY-30),  _z0(2), (-30,30)),
        ("뒷목",      ORANGE, 70, (560,1250), (CX, CY+R),       _z0(3), (72,108)),
    ]
    def ease(t): t=max(0,min(1,t)); return t*t*(3-2*t)
    def kct(d,cx,y,txt,fnt,fill):
        ws=txt.split(" "); gap=fnt.size*0.30; wd=[d.textlength(w,font=fnt) for w in ws]
        tot=sum(wd)+gap*(len(ws)-1); x=cx-tot/2
        for w,ww in zip(ws,wd): d.text((x,y),w,font=fnt,fill=fill); x+=ww+gap
    N = max(1, round(total * fps))
    for i in range(N):
        t = i / fps
        img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
        kct(d, W/2, 120, "볼륨매직?", f_title, YEL)
        d.ellipse([CX-R,CY-R,CX+R,CY+R], outline=GREY, width=4)
        d.polygon([(CX-R-4,CY-16),(CX-R-4,CY+16),(CX-R-26,CY)], fill=GREY)
        for label,col,tgt,(bx,by),(px,py),t0,arc in Z:
            a = ease((t-t0)/0.9)
            if a <= 0:
                continue
            d.arc([CX-R,CY-R,CX+R,CY+R], arc[0], arc[1], fill=col, width=8)
            d.line([(px,py),(bx,by)], fill=col, width=3); d.ellipse([px-6,py-6,px+6,py+6], fill=col)
            bw,bh=270,124; x0,y0=bx-bw//2,by-bh//2
            d.rounded_rectangle([x0,y0,x0+bw,y0+bh], radius=16, fill=(28,32,42), outline=col, width=3)
            d.text((x0+20,y0+12), label, font=f_lab, fill=col)
            d.text((x0+20,y0+50), f"{int(tgt*a)}%", font=f_pct, fill=col)
            bx0,by0=x0+150,y0+60; blen=100
            d.rounded_rectangle([bx0,by0,bx0+blen,by0+14], radius=7, fill=(50,55,66))
            d.rounded_rectangle([bx0,by0,bx0+int(blen*tgt/100*a),by0+14], radius=7, fill=col)
            d.text((x0+150,y0+82), "펴는 정도", font=f_why, fill=(120,128,140))
        img.save(frames_dir / f"z{i:04d}.png")


def _require(m: dict) -> None:
    """줄기별 필수요소 강제 검증. 누락 시 렌더 거부(형 '실수한 부분 꼭 끼기' — 변명 대신 코드로 막음).

    정본 줄기 규약: content/manifests/_TEMPLATE_줄기.md
    - message(마인드/흑백): stem·흑백(bw)·**메시지로 시작**(첫 세그=bigcard/검은 훅카드)·**outro(SNS)**·bigcard 최소1.
    - magic(미용 도식): stem·**메시지로 시작**(첫 줄 훅 물음)·도식 **4존 전부**(톱/페이스/백/네이프).
    """
    stem = m.get("stem")
    phrases = m.get("phrases", [])
    segs = m.get("segments", [])
    errs = []
    if stem not in ("message", "mind", "product", "magic"):
        errs.append("stem 미지정('message'/'product'/'magic')")
    if not phrases:
        errs.append("phrases 없음")
    # 공통: 메시지로 시작 — 첫 줄이 핵심 물음/메시지여야(빈 줄 금지)
    if phrases and not (phrases[0][0] or "").strip():
        errs.append("오프닝 메시지(phrases[0]) 비어있음")
    # 아웃트로: 메시지·제품·마인드 계열 전부 SNS 아웃트로 필수(계속 빠뜨린 부분)
    if stem in ("message", "mind", "product") and not m.get("outro"):
        errs.append(f"[{stem}] outro(SNS 아웃트로) 필수 — 계속 빠뜨린 부분")
    if stem in ("message", "mind"):
        if not any(s.get("bw") for s in segs):
            errs.append("[message] 흑백(bw) 세그먼트 필수")
        if not any(s.get("bigcard") for s in segs):
            errs.append("[message] 큰 중앙 메시지카드(bigcard) 최소 1개")
        if segs and not (segs[0].get("bigcard") or segs[0].get("black")):
            print("⚠️ [message] '메시지로 시작' 권장 — 첫 세그를 bigcard/검은 훅카드로 여는 게 정본 줄기.")
    if stem == "magic":
        if any(s.get("anim") == "dusang_zones" for s in segs):
            joined = " ".join((p[0] or "") for p in phrases)
            for zone in ("정수리", "페이스", "뒤통수", "뒷목"):
                if zone not in joined:
                    errs.append(f"[magic] 도식 4존 중 '{zone}' 누락 — 계속 빠뜨린 부분")
    if errs:
        raise ValueError("❌ 매니페스트 필수요소 누락(줄기 규약 위반): " + " / ".join(errs)
                         + "\n→ content/manifests/_TEMPLATE_줄기.md 대조 후 채워서 다시.")


def make(manifest_path: str | Path, out: str | Path | None = None,
         workdir: str | Path | None = None) -> Path:
    m = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    _require(m)   # 줄기 필수요소 강제 — 누락이면 여기서 멈춤
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
    bigcard_idx = set()   # 큰 중앙 메시지카드(검은화면·물음/핵심메시지 확대)
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
            if seg.get("card", True):  # 검은 카드=자막 중앙. card:false면 하단 유지(도식 위 나레이션 등)
                for li, ln in enumerate(lines):
                    mid = (ln.start + ln.end) / 2
                    if prev_end <= mid < seg_end:
                        (bigcard_idx if seg.get("bigcard") else black_line_idx).add(li)
        elif seg.get("anim"):
            fdir = wd / f"anim_seg_{k:02d}"
            if seg["anim"] == "dusang_zones":
                _dusang_zones_frames(fdir, lines, seg.get("numLine", 2), dur)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30",
                            "-i", str(fdir / "z%04d.png"), "-t", f"{dur:.3f}",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", str(out_seg)], check=True)
        else:
            DS.extract(seg["src"], seg["ss"], dur, out_seg,
                       vf=_frame_vf(seg.get("frame", "landscape"), seg.get("hflip", False),
                                    seg.get("bw", False), float(seg.get("zoom", 1.0))),
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
        elif ov["type"] == "fist_raise":
            fdir = wd / f"fist_{j}"
            off, end = _fist_raise_frames(fdir, lines, ov["line"])
            nxt = wd / f"comp_{j}.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(comp),
                            "-itsoffset", f"{off:.3f}", "-framerate", "30", "-i", str(fdir / "f%04d.png"),
                            "-filter_complex",
                            f"[0][1]overlay=0:0:enable='between(t,{off:.3f},{end + 0.1:.3f})':format=auto[v]",
                            "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", str(nxt)], check=True)
            comp = nxt

    # 4) 자막 Line(훅/엔딩=검은카드 중앙 / bigcard=큰 중앙 메시지) + 렌더
    tl = []
    for li, ln in enumerate(lines):
        if li in bigcard_idx:
            txt = r"{\an5\fs104\b1}" + ln.text   # 큰 중앙 메시지카드(강조)
        elif li in black_line_idx:
            txt = r"{\an5}" + ln.text
        else:
            txt = ln.text
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
