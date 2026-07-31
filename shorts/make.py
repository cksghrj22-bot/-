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
def _dusang_zones_frames(frames_dir: Path, lines: list, num_line: int, total: float,
                         seg_start: float = 0.0, fps: int = 30) -> None:
    """두상 원 + 존별 % 도식. num_line부터 존 순차 등장. seg_start=이 anim 세그의 절대 시작초(오프닝 메시지 뒤에 오는 경우)."""
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
        base = lines[idx].start if idx < len(lines) else lines[num_line].start + k * 0.9
        return base - seg_start   # 세그 로컬 시간으로 변환(오프닝 메시지 뒤에 애니가 오는 구조)
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


def _strand_zones_frames(frames_dir: Path, lines: list, num_line: int, total: float,
                         seg_start: float = 0.0, fps: int = 30) -> None:
    """모발 한 가닥(뿌리→끝) 손상 그라데이션 도식. num_line부터 구간(자연곱슬→녹은+탄→만성) 순차 등장.
    끝으로 갈수록 손상%가 커지고(게이지), 만성 구간은 속심(내부)까지 파고드는 코어선으로 표현."""
    from PIL import Image, ImageDraw, ImageFont
    frames_dir.mkdir(parents=True, exist_ok=True)
    for p in frames_dir.glob("*.png"):
        p.unlink()
    W, H = 1080, 1920
    BG = (18, 20, 26)
    f_title = ImageFont.truetype(KYOBO, 92); f_lab = ImageFont.truetype(KYOBO, 40)
    f_pct = ImageFont.truetype(NSQR, 58); f_tag = ImageFont.truetype(KYOBO, 30)
    BLUE=(120,190,255); ORANGE=(255,140,60); RED=(235,70,70); GREY=(90,96,110); DGREY=(150,158,170)
    CX = 380; HW = 44; TOP = 380; BOT = 1520
    def _z0(k):
        idx = num_line + k
        base = lines[idx].start if idx < len(lines) else lines[num_line].start + k * 0.9
        return base - seg_start
    # (라벨, 색, 손상%, y0, y1, 박스중심, 등장시각, 코어여부)
    Z = [
        ("자연곱슬",  BLUE,   10, TOP,  560,  (760, 470),  _z0(1), False),
        ("녹은+탄",   ORANGE, 60, 560,  1010, (760, 780),  _z0(2), False),
        ("만성손상",  RED,    95, 1010, BOT,  (760, 1120), _z0(3), True),
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
        kct(d, W/2, 120, "곱슬? 손상?", f_title, (255,212,0))
        d.text((CX-150, TOP-42), "뿌리", font=f_tag, fill=DGREY)
        d.text((CX-140, BOT+6), "끝", font=f_tag, fill=DGREY)
        d.rounded_rectangle([CX-HW, TOP, CX+HW, BOT], radius=HW, outline=GREY, width=4)
        for label,col,dmg,y0,y1,(bx,by),t0,core in Z:
            a = ease((t - t0) / 0.8)
            if a <= 0:
                continue
            fill_y1 = y0 + (y1 - y0) * a
            d.rounded_rectangle([CX-HW+3, y0, CX+HW-3, fill_y1], radius=HW-3, fill=col)
            if core and a > 0.4:
                ca = ease((a - 0.4) / 0.6)
                d.line([(CX, y0+10), (CX, y0 + (y1 - y0 - 20) * ca)], fill=(70,12,12), width=10)
            cy = (y0 + y1) / 2
            d.line([(CX+HW, cy), (bx-160, by)], fill=col, width=3)
            d.ellipse([CX+HW-6, cy-6, CX+HW+6, cy+6], fill=col)
            bw, bh = 320, 150; x0, yy0 = bx - bw//2, by - bh//2
            d.rounded_rectangle([x0, yy0, x0+bw, yy0+bh], radius=16, fill=(28,32,42), outline=col, width=3)
            d.text((x0+22, yy0+14), label, font=f_lab, fill=col)
            d.text((x0+22, yy0+62), f"손상 {int(dmg*a)}%", font=f_pct, fill=col)
            bx0, by0 = x0+22, yy0+128; blen = 276
            d.rounded_rectangle([bx0, by0, bx0+blen, by0+12], radius=6, fill=(50,55,66))
            d.rounded_rectangle([bx0, by0, bx0+int(blen*dmg/100*a), by0+12], radius=6, fill=col)
        img.save(frames_dir / f"z{i:04d}.png")


# ── 귀여운 캐릭터: 앞머리 찰랑 내려오고 눈 반짝(앞머리=눈매 강조 설명 인서트) ────────
def _bang_sparkle_frames(frames_dir: Path, lines: list, num_line: int, total: float,
                         seg_start: float = 0.0, fps: int = 30) -> None:
    """둥근 얼굴 캐릭터: ①앞머리 없음 → ②앞머리가 찰랑 내려옴 → ③앞머리가 눈매를 감싸며 눈이 반짝.
    '앞머리는 눈매를 강조하는 디자인'을 귀엽게 시각화(실사 사이 설명 인서트)."""
    from PIL import Image, ImageDraw
    import math as _m
    frames_dir.mkdir(parents=True, exist_ok=True)
    for p in frames_dir.glob("*.png"):
        p.unlink()
    W, H = 1080, 1920
    CX, CY, R = W // 2, 840, 300               # 얼굴 중심·반지름
    SKIN = (255, 227, 209); SKIN_L = (255, 214, 194)
    HAIR = (74, 52, 40); HAIR_D = (54, 36, 27)
    BLUSH = (255, 170, 165); EYE = (60, 44, 40); YEL = (255, 214, 66)
    EY = CY - 30                               # 눈 y
    EXL, EXR = CX - 118, CX + 118              # 좌우 눈 x

    def sm(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

    def star(d, cx, cy, s, col, a=255):
        pts = []
        for k in range(8):
            ang = _m.pi / 4 * k
            rr = s if k % 2 == 0 else s * 0.4
            pts.append((cx + rr * _m.cos(ang), cy + rr * _m.sin(ang)))
        d.polygon(pts, fill=(*col, a))

    N = max(1, round(total * fps))
    for i in range(N):
        t = i / (N - 1) if N > 1 else 1.0
        grow = sm((t - 0.28) / 0.30)           # 앞머리 내려오는 진행(0→1)
        spark = sm((t - 0.60) / 0.30)          # 눈 반짝 진행
        sway = _m.sin(t * _m.pi * 5) * 14 * grow   # 찰랑(좌우 흔들)
        edge = min(1.0, i / 6, (N - 1 - i) / 6)

        img = Image.new("RGB", (W, H), (255, 243, 232))   # 크림 배경
        d = ImageDraw.Draw(img, "RGBA")
        # 배경 파스텔 점
        for (px, py, pr, pc) in [(180, 380, 60, (255, 214, 194)), (900, 520, 44, (255, 224, 236)),
                                 (150, 1300, 52, (255, 224, 236)), (930, 1360, 66, (214, 236, 255))]:
            d.ellipse([px-pr, py-pr, px+pr, py+pr], fill=(*pc, 90))
        # 목 + 둥근 두상 헤어(얼굴보다 크게·위 둥글게) + 옆 긴머리 — 항상 존재
        d.rounded_rectangle([CX-70, CY+R-70, CX+70, CY+R+120], radius=30, fill=SKIN_L)
        d.ellipse([CX-R-28, CY-R-50, CX+R+28, CY+R+24], fill=HAIR)             # 둥근 두상
        for sgn in (-1, 1):                                                     # 옆으로 흐르는 긴 머리(두상에 밀착·뾰족X)
            d.polygon([(CX+sgn*(R+4), CY-R+150), (CX+sgn*(R+18), CY+R+150),
                       (CX+sgn*(R-30), CY+R+150), (CX+sgn*(R-14), CY-20)], fill=HAIR)
        d.ellipse([CX-R, CY-R, CX+R, CY+R], fill=SKIN, outline=(230, 195, 175), width=5)  # 얼굴
        # 볼터치
        d.ellipse([EXL-58, EY+92, EXL+18, EY+140], fill=(*BLUSH, 150))
        d.ellipse([EXR-18, EY+92, EXR+58, EY+140], fill=(*BLUSH, 150))
        # 눈(반짝하면 커지고 광채)
        eg = 1.0 + 0.12 * spark
        for ex in (EXL, EXR):
            ew, eh = int(52*eg), int(66*eg)
            d.ellipse([ex-ew, EY-eh, ex+ew, EY+eh], fill=(255, 255, 255))
            d.ellipse([ex-int(38*eg), EY-int(46*eg), ex+int(38*eg), EY+int(46*eg)], fill=EYE)
            d.ellipse([ex-14, EY-28, ex+6, EY-8], fill=(255, 255, 255))          # 큰 광채
            d.ellipse([ex+10, EY+6, ex+22, EY+18], fill=(255, 255, 255, 220))    # 작은 광채
        # 입(방긋)
        d.arc([CX-42, EY+70, CX+42, EY+130], 20, 160, fill=(200, 120, 110), width=8)
        # 앞머리 — 옆단은 얼굴 원 곡선을 따르되(사각 블록 X) **아랫단은 눈 위에서 직선**으로 멈춰
        # 눈을 가리지 않는다 → 눈매가 드러나 강조됨(형 지시: 눈에서 직선·눈 안 가림).
        if grow > 0.02:
            crownY = CY - R - 6                                   # 이마 위 시작(두상에 붙음)
            eyeTopFull = EY - 82                                  # 눈 위 여유(반짝여 커진 눈도 안 가림)
            browY = crownY + int((eyeTopFull - crownY) * grow)    # 눈 바로 위에서 멈춤(직선단)
            cphi = max(-0.985, min(0.985, (CY - browY) / R))
            phi_side = _m.acos(cphi)                              # 옆단이 얼굴 원에 닿는 각(0=정수리)
            Rin = R - 3                                           # 얼굴선 안쪽으로 flush(삐져나옴 0)
            xEdge = Rin * _m.sin(phi_side)
            steps = 30
            pts = []                                              # 윗변=얼굴 원 크라운·아랫변=눈 위 직선
            for s in range(steps + 1):                            # → 원의 현(chord). 두상에 정확히 flush·좌우 대칭.
                phi = -phi_side + 2 * phi_side * s / steps
                pts.append((CX + Rin * _m.sin(phi), CY - Rin * _m.cos(phi)))
            pts.append((CX + xEdge, browY))                      # 아랫단: 눈 위 수평 직선(오른→왼)
            pts.append((CX - xEdge, browY))
            d.polygon(pts, fill=HAIR)
            for k in range(-4, 5):                                # 결(가는 세로선·직선단까지·미세 찰랑)
                u = k / 4.5
                x0 = CX + xEdge * u * 0.9
                d.line([(x0, crownY + 40), (x0 + sway * 0.35, browY - 6)], fill=(*HAIR_D, 150), width=4)
        # 눈 반짝 별(눈매 강조) — 크게·글로우
        if spark > 0.05:
            a = int(255 * spark)
            tw = 0.7 + 0.3 * _m.sin(t * _m.pi * 8)
            for (sx, sy, sz, sc, sa) in [(EXR + 92, EY - 78, 58, YEL, a), (EXL - 92, EY - 64, 42, YEL, int(a*0.95)),
                                         (EXR + 46, EY + 66, 30, (255, 255, 255), int(a*0.85)),
                                         (EXL - 52, EY + 72, 24, (255, 255, 255), int(a*0.8))]:
                d.ellipse([sx-sz, sy-sz, sx+sz, sy+sz], fill=(*sc, int(sa*0.18)))   # 글로우
                star(d, sx, sy, sz * tw, sc, sa)
        if edge < 1.0:                          # 앞뒤 페이드
            ov = Image.new("RGBA", (W, H), (255, 243, 232, int(255 * (1 - edge))))
            img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
        img.save(frames_dir / f"z{i:04d}.png")


# 브랜드 표준 SNS 아웃트로 — message/mind/product의 default-on 값(계속 빠지던 것).
DEFAULT_SNS_OUTRO = "SNS에 일기를 쓰고 있어요"
_OUTRO_STEMS = ("message", "mind", "product")


def _normalize(m: dict) -> None:
    """표준요소 **자동 주입** — '깜빡해서 빠지는' 것을 구조로 차단(형 2026-07-29 '문제는 고쳐도 계속 빠진다는거').

    아웃트로는 이제 opt-in이 아니라 **default-on**: message/mind/product 스템은 매니페스트에
    outro가 없어도 표준 SNS 아웃트로가 자동으로 붙는다. 빼려면 명시적으로 waive:["outro"]+_notes 사유.
    → 사람이 매번 넣어야 발동하던 구조(=까먹으면 누락)를 뒤집는다: 넣는 게 기본, 빼는 게 예외.
    """
    stem = m.get("stem")
    waived = set(m.get("waive", []))
    if stem in _OUTRO_STEMS and "outro" not in waived and not m.get("outro"):
        m["outro"] = DEFAULT_SNS_OUTRO
        print(f"ⓘ [auto] {stem} 스템 표준 SNS 아웃트로 자동 주입: '{DEFAULT_SNS_OUTRO}' "
              f"— 매니페스트에 없어 기본값 적용(빼려면 waive:[\"outro\"]+_notes 사유).")


def _ensure_outro_tail(m: dict) -> None:
    """아웃트로↔엔딩카드 **충돌 자동방지**(형 2026-07-29 발견). 아웃트로는 영상 끝 outro_dur초에
    중앙정렬로 뜬다. 마지막 세그가 중앙 카드(black/bigcard)면 아웃트로와 겹쳐 글자가 깨진다
    (부시시편 44s 실증) → 손으로 tail 안 맞춰도 되게 총 tail을 outro_dur+여유 이상으로 자동 확보.
    """
    segs = m.get("segments") or []
    if not (m.get("outro") and segs):
        return
    outro_dur = float(SS.OUTRO_CARD.get("dur", 2.6))
    need = outro_dur + 0.3
    last = segs[-1]
    if not (last.get("black") or last.get("bigcard")):
        return  # 마지막이 하단자막/실사면 중앙 아웃트로와 안 겹침
    seg_tails = sum(float(s.get("tail", 0.0)) for s in segs)
    if seg_tails < need:
        bump = round(need - seg_tails, 3)
        last["tail"] = round(float(last.get("tail", 0.0)) + bump, 3)
        print(f"ⓘ [auto] 아웃트로↔엔딩카드 충돌방지 — 마지막 세그 tail +{bump:.2f}s "
              f"(총 tail {need:.2f}s 확보 → 카드 종료 후 아웃트로 단독표시).")


def _require(m: dict) -> None:
    """줄기별 필수요소 검증. 기본은 강제(잊어서 빠뜨리는 실수 차단)하되, **의도적 예외는 `waive`로 허용**.

    형 원칙(2026-07-28): "유동적이어야 해, 무조건은 없어. 메시지를 유리하게 전달할 모든 방법을
    기존것+새로배운것 총동원." → 규약은 '기본값'이지 '절대'가 아니다. 판단해서 뺀 건
    매니페스트에 `"waive": ["실사", "outro", ...]`(사유는 _notes)로 통과. 잊어서 빠진 건 여전히 거부.

    정본 줄기 규약: content/manifests/_TEMPLATE_줄기.md
    """
    stem = m.get("stem")
    phrases = m.get("phrases", [])
    segs = m.get("segments", [])
    waived = set(m.get("waive", []))   # 의도적 예외(유동적)
    errs = []
    if stem not in ("message", "mind", "product", "magic"):
        errs.append("stem 미지정('message'/'product'/'magic')")
    if not phrases:
        errs.append("phrases 없음")
    # 공통: 메시지로 시작 — 첫 줄이 핵심 물음/메시지여야(빈 줄 금지)
    if phrases and not (phrases[0][0] or "").strip():
        errs.append("오프닝 메시지(phrases[0]) 비어있음")
    # 아웃트로: 메시지·제품·마인드 계열 전부 SNS 아웃트로 기본 필수(계속 빠뜨린 부분).
    # ⚠️_normalize가 먼저 자동 주입하므로 여기서 '누락'은 사실상 안 뜬다. 남은 유일한 탈출구=waive인데,
    #   조용히 빠지던 게 문제였으므로(형 '고쳐도 계속 빠진다') **waive는 _notes 사유 필수 + 큰 경고**로 막는다.
    if stem in _OUTRO_STEMS and "outro" not in waived and not m.get("outro"):
        errs.append(f"[{stem}] outro(SNS 아웃트로) 누락 — 표준요소. (_normalize 자동주입 미작동?) 의도면 waive:[\"outro\"]+_notes.")
    if "outro" in waived:
        if not (m.get("_notes") or "").strip():
            errs.append("[outro waive] 아웃트로를 뺐다면 _notes에 **사유 필수** — 조용한 누락 방지(형 '고쳐도 계속 빠진다').")
        else:
            print("⚠️⚠️ [outro WAIVED] SNS 아웃트로를 의도적으로 뺐다. 정말 맞나? "
                  "(message/mind/product 표준요소·사유=_notes) — 미용 message편은 waive 금지가 기본.")
    if stem in ("message", "mind"):
        if not any(s.get("bw") for s in segs) and "bw" not in waived:
            errs.append("[message] 흑백(bw) 세그먼트 누락. 컬러가 메시지에 유리하면 waive:[\"bw\"].")
        if not any(s.get("bigcard") for s in segs) and "bigcard" not in waived:
            errs.append("[message] 큰 중앙 메시지카드(bigcard) 없음. 의도면 waive:[\"bigcard\"].")
        if segs and not (segs[0].get("bigcard") or segs[0].get("black")):
            print("⚠️ [message] '메시지로 시작' 권장 — 첫 세그를 bigcard/검은 훅카드로 여는 게 정본 줄기.")
    # 실사 필수 선언(어느 스템이든) — 실사가 메시지의 '본체'인 영상은 애니만으로 렌더 금지.
    # ⚠️부시시편 사고(2026-07-29): message 스템이라 아래 magic 게이트를 안 타 → 실사 없이
    #   애니(strand_zones)만 대사 3~11 전부를 덮어 렌더됨. 형 "영상 써서 하고 애니는 설명에만".
    #   재발 방지: 실사가 본체인 매니페스트는 "require_실사": true 로 선언 → src 없으면 거부.
    if m.get("require_실사") and not any(s.get("src") for s in segs) and "실사" not in waived:
        errs.append("[require_실사] 실사(src) 세그먼트 없음 — 이 영상은 실사가 본체다. "
                    "애니만 렌더 금지(부시시편 사고 재발방지). 드라이브 footage fileId를 src로 넣어라. "
                    "진짜 의도면 waive:[\"실사\"]+_notes 사유.")
    if stem == "magic":
        # 실사(사람 매직하는 장면) 기본 필수 — 계속 빠뜨린 최악의 실수(형 "빼지마 절대").
        if not any(s.get("src") for s in segs) and "실사" not in waived:
            errs.append("[magic] 실사(사람 매직하는 장면 src) 없음 — 기본 절대금지. 진짜 의도면 waive:[\"실사\"]+_notes 사유.")
        if any(s.get("anim") == "dusang_zones" for s in segs) and "존" not in waived:
            joined = " ".join((p[0] or "") for p in phrases)
            for zone in ("정수리", "페이스", "뒤통수", "뒷목"):
                if zone not in joined:
                    errs.append(f"[magic] 도식 4존 중 '{zone}' 누락 — 계속 빠뜨린 부분")
    if errs:
        raise ValueError("❌ 매니페스트 필수요소 누락(줄기 규약): " + " / ".join(errs)
                         + "\n→ 잊은 거면 채우고, 의도면 waive로 명시. 규약: content/manifests/_TEMPLATE_줄기.md")
    if waived:
        print(f"ⓘ 의도적 예외(waive) 적용: {sorted(waived)} — 유동적 판단(무조건 없음).")


def make(manifest_path: str | Path, out: str | Path | None = None,
         workdir: str | Path | None = None) -> Path:
    m = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    _normalize(m)          # 표준요소 자동 주입(아웃트로 default-on) — 깜빡 누락 구조 차단
    _ensure_outro_tail(m)  # 아웃트로↔엔딩카드 충돌 자동방지(tail 자동 확보)
    _require(m)            # 줄기 필수요소 강제 — 누락이면 여기서 멈춤
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
                _dusang_zones_frames(fdir, lines, seg.get("numLine", 2), dur, seg_start=prev_end)
            elif seg["anim"] == "strand_zones":
                _strand_zones_frames(fdir, lines, seg.get("numLine", 2), dur, seg_start=prev_end)
            elif seg["anim"] == "bang_sparkle":
                _bang_sparkle_frames(fdir, lines, seg.get("numLine", 2), dur, seg_start=prev_end)
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
    # 자막 높이 오버라이드(POV 등 헤어가 화면 아래 있을 때 자막을 위로): sub_margin_v
    sub_style = dict(SS.SUB)
    if m.get("sub_margin_v") is not None:
        sub_style["margin_v"] = int(m["sub_margin_v"])
    R.render(str(comp), script, str(out_path),
             bgm=bgm, bgm_volume=SS.BGM_VOLUME, style=sub_style, layout="full",
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
