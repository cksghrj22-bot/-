"""creator_short — 창엽/육성 교육 쇼츠 '잠긴' 렌더 함수 (2026-07-28).

⛔ 존재 이유(형 2026-07-28 지적): 규칙이 문서(박제)에만 있고 코드에 없어서 매 세션 손으로
다시 만들다 드리프트(폰트폴백·CFR누락·싱크밀림·규격무시)가 반복됨. → **규격을 코드에 박고,
렌더 전 전제조건을 강제 검사(게이트)하고, 렌더 후 자가 QC로 불량이면 예외를 던진다.**
이 함수만 쓰면 즉흥 파이프라인이 사라져 같은 실수 재발이 구조적으로 막힌다.

스타일은 shorts.shortstyle(정본 코드)에서만 가져온다. 절대 값 하드코딩·재구현 금지.
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, "/home/user/-")
import shorts.shortstyle as SS

REPO = Path("/home/user/-")
WARM = ("eq=saturation=0.90:contrast=1.06:brightness=0.02,"
        "colorbalance=rm=0.03:bm=-0.03:rh=0.02:bh=-0.03,"
        "curves=all='0/0.03 0.5/0.5 1/0.98'")
DIM = 0.22
VY = 460          # 정사각 영상 y(상단밴드 바로 아래) — 형 승인(v3)
CANVAS = (1080, 1920)


# ── 게이트 1: 환경(폰트) 재현성 ──────────────────────────────────────────────
def ensure_env() -> None:
    """POP/교보 폰트가 실제 로드되는지 강제. 없으면 repo자산→~/.fonts 설치 후 캐시.
    (폰트 미설치→폴백→글자체 사고 재발방지. 2026-07-28 실사고)"""
    fonts = {
        "nsqr_eb.ttf": REPO / "assets/fonts/nsqr_eb.ttf",
        "KyoboHandwriting2019.ttf": REPO / "assets/fonts/KyoboHandwriting2019.ttf",
    }
    dst = Path("/root/.fonts"); dst.mkdir(parents=True, exist_ok=True)
    changed = False
    for name, src in fonts.items():
        if src.exists() and not (dst / name).exists():
            (dst / name).write_bytes(src.read_bytes()); changed = True
    if changed:
        subprocess.run(["fc-cache", "-f"], capture_output=True)
    # 실제 해석 검증 — 폴백이면 예외
    fam = SS.bold_gothic_family()
    hit = subprocess.run(["fc-match", fam], capture_output=True, text=True).stdout
    if "NanumSquareRound" not in hit:
        raise RuntimeError(f"POP 폰트 폴백 위험: fc-match '{fam}' → {hit.strip()}. "
                           f"assets/fonts/nsqr_eb.ttf 또는 apt fonts-nanum-extra 필요.")


# ── CFR은 '출력'에서 보장 ────────────────────────────────────────────────────
# 번인 자막은 libass가 프레임 PTS로 매칭하므로 소스가 VFR이어도 싱크가 맞다.
# 문제는 '출력'이 VFR로 나가 외부 재생·재편집서 밀리는 것 → 렌더 필터에 fps=30 +
# 출력 -r 30 으로 항상 CFR 30fps 출력을 강제한다. (QC가 출력 fps를 재검증)


def _ts(x: float) -> str:
    h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _style(name: str, d: dict) -> str:
    return (f"Style: {name},{d['font']},{d['size']},{d['primary_color']},{d['outline_color']},"
            f"&H00000000,-1,0,0,0,100,100,0,0,{d['border_style']},{d['outline']},{d.get('shadow',0)},"
            f"{d['alignment']},60,60,{d['margin_v']},1")


def build(clip_mp4: str | Path, A: float, B: float,
          title_yellow: str, title_white: str,
          cues: list[tuple[float, float, str, str | None]],
          out_mp4: str | Path, crop: str = "1080:1080:420:0") -> Path:
    """잠긴 렌더. cues=[(start,end,ko,en)] (영상시각 A기준 0). 전제검사→렌더→자가QC.
    자막·제목 스타일은 shortstyle(POP) 고정. 실패 시 예외(불량 출력 금지)."""
    ensure_env()
    clip_mp4 = Path(clip_mp4); out_mp4 = Path(out_mp4)
    DUR = B - A
    head = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {CANVAS[0]}\nPlayResY: {CANVAS[1]}\n"
            f"WrapStyle: 0\nScaledBorderAndShadow: yes\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, "
            "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
            "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"{_style('title', SS.POP_TITLE)}\n{_style('cap', SS.SUB)}\n[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            f"Dialogue: 0,{_ts(0)},{_ts(DUR)},title,,0,0,0,,{SS.pop_title(title_yellow, title_white)}\n")
    body = "".join(f"Dialogue: 0,{_ts(s)},{_ts(e)},cap,,0,0,0,,{SS.ko_en(ko, en)}\n"
                   for s, e, ko, en in cues)
    ass = out_mp4.with_suffix(".ass"); ass.write_text(head + body, encoding="utf-8")
    vf = (f"[0:v]crop={crop},{WARM},drawbox=c=black@{DIM}:t=fill,scale=1080:1080,fps=30,setsar=1[v];"
          f"color=c=black:s={CANVAS[0]}x{CANVAS[1]}:d={DUR}[bg];[bg][v]overlay=0:{VY}[b1];"
          f"[b1]subtitles={ass}[vout];"
          f"[1:a]volume=0.14,afade=t=out:st={DUR-1.5}:d=1.5[bgm];"
          f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=0[aout]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(A), "-t", str(DUR),
        "-i", str(clip_mp4), "-i", str(REPO / "shorts/assets/bgm_piano_long.mp3"),
        "-filter_complex", vf, "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
        "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out_mp4)], check=True)
    qc(out_mp4, DUR)
    return out_mp4


# ── 게이트 3: 렌더 후 자가 QC(불량 출력 차단) ───────────────────────────────
def qc(path: Path, expect_dur: float) -> None:
    info = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,avg_frame_rate", "-of", "json", str(path)],
        capture_output=True, text=True).stdout
    v = json.loads(info)["streams"][0]
    if (v["width"], v["height"]) != CANVAS:
        raise RuntimeError(f"QC실패 해상도 {v['width']}x{v['height']} ≠ {CANVAS}")
    num, den = (v["avg_frame_rate"].split("/") + ["1"])[:2]
    fps = float(num) / float(den or 1)
    if abs(fps - 30) > 0.05:
        raise RuntimeError(f"QC실패 출력 VFR/비30fps({fps:.3f}) — 외부툴 자막밀림 위험")
    # 오디오 존재
    a = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
        "stream=codec_type", "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip()
    if "audio" not in a:
        raise RuntimeError("QC실패 오디오 없음")
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip())
    if abs(dur - expect_dur) > 1.0:
        raise RuntimeError(f"QC실패 길이 {dur:.1f}s ≠ 예상 {expect_dur:.1f}s")


def _wrap2(words: list[str], per: int = 15) -> str:
    """단어 리스트를 ≤2줄로 배치(각 줄 ~per자). 우리 정본 쇼츠 자막 규격(≤2줄·짧게)."""
    text = " ".join(words)
    if len(text) <= per:
        return text
    # 중앙 근처 단어 경계에서 2줄로 분할
    best = None; acc = 0
    for i, wd in enumerate(words[:-1]):
        acc += len(wd) + 1
        if best is None or abs(acc - len(text) / 2) < best[0]:
            best = (abs(acc - len(text) / 2), i)
    i = best[1]
    return " ".join(words[:i + 1]) + r"\N" + " ".join(words[i + 1:])


def cues_from_diar(diar_json: str | Path, A: float, B: float, teacher_only: bool = False):
    """diar_p(프록시정렬)에서 [A,B] 자막 큐 자동추출(한글). 영어는 호출측이 채운다.
    ⚠️2026-07-29 형 지적 수정: 토큰은 단어 단위라 **공백으로 조인**(안 그러면 글자 다 겹침).
    한 큐 ≤ 약 22자(넘으면 새 큐), 렌더 시 ≤2줄로 래핑. teacher_only=False=학생질문 포함(맥락)."""
    w = json.load(open(diar_json))
    tea = Counter(x["spk"] for x in w).most_common(1)[0][0]
    seg = [x for x in w if A <= x["s"] <= B and (not teacher_only or x["spk"] == tea)]
    cues = []; cur = []
    def flush(pad):
        words = [c["t"].strip() for c in cur if c["t"].strip()]
        if words:
            cues.append((round(cur[0]["s"] - A, 2), round(cur[-1]["e"] - A + pad, 2), _wrap2(words)))
    for x in seg:
        cur.append(x)
        j = " ".join(c["t"] for c in cur); d = cur[-1]["e"] - cur[0]["s"]
        if x["t"].strip().endswith(('.', '?', '!', '요', '다', '까', '고', '지', '네', '든', '야', '죠')) or len(j) >= 22 or d >= 3.6:
            flush(0.35); cur = []
    if cur:
        flush(0.5)
    return cues, tea


# ── 매니페스트 러너(스키마 검증) — 손튜플 오타(name 누락 등) 원천차단 ──────────
REQUIRED = ("clip", "A", "B", "yellow", "white", "name", "cues")


def render_batch(items: list[dict], srcdir: str | Path, outdir: str | Path) -> list[Path]:
    """items=[{clip,A,B,yellow,white,name,cues}]. 각 항목 키를 검증(누락시 명확한 예외),
    creator_short.build로 렌더. 튜플 위치오류(2026-07-28 2회 재발) 구조적 차단."""
    srcdir, outdir = Path(srcdir), Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    done = []
    for i, it in enumerate(items):
        missing = [k for k in REQUIRED if k not in it]
        if missing:
            raise KeyError(f"매니페스트 항목#{i}({it.get('name','?')}) 필수키 누락: {missing}")
        out = outdir / f"창엽쇼츠_{it['name']}.mp4"
        build(srcdir / f"{it['clip']}.mp4", it["A"], it["B"], it["yellow"], it["white"],
              it["cues"], out)
        done.append(out); print(f"✅ {it['name']}", flush=True)
    return done
