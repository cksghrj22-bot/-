#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""쇼츠 영상 — 렌더 게이트 (자동 검사 + 발행 전 스샷 시트).

차노 원칙: "표준은 글 아니라 검사코드로 잠근다."
차노 지시(2026-08-14): "영상 발행 전은 항상 스샷으로 띄워서 전체적으로 볼 수 있게 하고 렌더링하기."

쓰는 법:
    python3 scripts/shorts_gate.py <영상.mp4 또는 폴더>
    → 통과 exit 0 / 하나라도 걸리면 exit 1

검사 (knowledge/제작규격_정본.md 기준)
  [S1] 1080x1920 (프리뷰는 경고만, 탈락 아님)
  [S2] 길이 26~59초 — 보완게이트 기준
  [S3] 오디오 스트림 있음 (쇼츠는 나레이션+BGM)
  [S4] 경계 무음 없음 — 앞뒤 0.5초에 소리가 죽어 있으면 경고 (짧은 BGM loop 사고 #207)
  [S5] **하단 UI존(바닥 20%)에 자막 침범** — 흰 픽셀 비율로 자동 검출
       규격: 한글 최하단줄 y=1436 / 영어 y=1500 → 바닥에서 420px 위. 1540 아래는 비어야 한다.
  [S6] 발행 전 스샷 시트 — 등간격 12컷 + **UI존 경계선을 그려서** 한눈에 보이게 만든다.
"""
from __future__ import annotations
import argparse, difflib, json, re, statistics, subprocess, sys, tempfile
from pathlib import Path

try:  # `python scripts/...`와 `python -m scripts...` 둘 다 지원
    from shot_variety import SIM_LIMIT, cos
except ImportError:
    from scripts.shot_variety import SIM_LIMIT, cos

ROOT = Path(__file__).resolve().parent.parent
FF, FP = "ffmpeg", "ffprobe"
# 1080x1920 기준 UI존 — 다른 해상도는 비율로 계산
UI_ZONE_RATIO = 1540 / 1920  # 바닥 20%가 UI존
S9_LIMIT = 0.80
MIN_CUT_SEC = 1.6
# 2026-08-17 차노 지시 — "불필요한 상한선·제한 때문에 새 렌더가 다 막힌다. 기존 규약 말고 요즘 규약으로 바꿔라"
#
# ⛔ 폐기한 상한 (2026-08-14 「충돌방지 상한」)
#    · 자료컷 4개  ← 소재를 많이 쓸수록 탈락시켜 반복을 조장했다. 목적과 정반대라 삭제
#    · 연속 사용 2컷 ← 클립 기준 연속 제한. 아래 「한 인물 연속 12초」로 대체
#    · 출처 3종    ← 아래 「등장 인물 3명 이상」으로 대체
#
# ✅ 적용 규약 = 보완게이트 정본 §10-1 (차노 2026-08-16 확정, 요즘 규약)
MAX_ASSET_SHARE = 0.40        # 동일 소스 파일 사용 한 편에 최대 40%
MAX_PERSON_RUN_SEC = 12.0     # 한 인물 연속 노출 12초 초과 금지 — 넘으면 다른 인물 컷을 끼운다
MIN_PERSONS = 3               # 한 편 내 등장 인물 3명 이상 (구 「2명 이상」에서 상향)


def probe(p: Path) -> dict:
    v = json.loads(subprocess.check_output(
        [FP, "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,avg_frame_rate,duration", "-of", "json", str(p)], text=True))["streams"][0]
    a = subprocess.check_output([FP, "-v", "error", "-select_streams", "a", "-show_entries",
                                 "stream=index", "-of", "csv=p=0", str(p)], text=True).strip()
    v["audio"] = len([x for x in a.split("\n") if x])
    return v


def ui_zone_hits(p: Path, w: int, h: int, dur: float, tmp: Path) -> list[tuple[float, float]]:
    """UI존에 **자막 글자**가 있는지 본다.

    ⚠️ 2026-08-17 수정 — 예전엔 그냥 「밝은 픽셀 비율」을 셌다. 그래서 **흰 커트보·조명·흰 벽**이
    전부 자막으로 잡혔다(실측: v5 23.45초에서 44.52% — 실제로는 글자 0개, 커트보였다).
    자막은 **흰 글씨 + 검은 테두리**다. 아주 밝은 픽셀 바로 옆에 아주 어두운 픽셀이 있어야 글자다.
    커트보는 넓게 밝기만 하고 옆에 검정이 없다.
    """
    try:
        from PIL import Image, ImageFilter
    except ImportError:
        return []

    ui_zone_top = int(h * UI_ZONE_RATIO)
    ui_zone_height = h - ui_zone_top
    if ui_zone_height <= 0:
        return []

    hits = []
    for i in range(12):
        t = dur * (i + 0.5) / 12
        f = tmp / f"ui_{i:02d}.png"
        subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.2f}",
                        "-i", str(p), "-frames:v", "1",
                        "-vf", f"crop={w}:{ui_zone_height}:0:{ui_zone_top}",
                        str(f)], check=True)
        im = Image.open(f).convert("L")
        near_dark = im.filter(ImageFilter.MinFilter(5))   # 5x5 안에 어두운 픽셀이 있으면 어두워진다
        px, nd = im.load(), near_dark.load()
        W, H = im.size
        step = 2                                          # 2픽셀 간격 샘플 — 속도
        outlined = total = 0
        for y in range(0, H, step):
            for x in range(0, W, step):
                total += 1
                if px[x, y] > 235 and nd[x, y] < 60:      # 아주 밝은데 바로 옆이 아주 어둡다 = 글자 획
                    outlined += 1
        ratio = outlined / max(1, total)
        if ratio > 0.004:
            hits.append((round(t, 2), round(ratio * 100, 2)))
    return hits


def load_cut_manifest(path: Path | None) -> list[dict]:
    """JSON cuts/beats 또는 표 형태 MD의 말/화면/일치를 읽는다."""
    if not path:
        return []
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("cuts") or data.get("beats") or data.get("segments") or []
    cuts = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(cells) < 5 or not re.fullmatch(r"\d+", cells[0]):
            continue
        m = re.match(r"([0-9.]+)\s*[~〜-]\s*([0-9.]+)", cells[1])
        if not m:
            continue
        cut = {"start": float(m.group(1)), "end": float(m.group(2)),
               "말": cells[2], "화면": cells[3], "일치": cells[4]}
        # 2026-08-17 수정: 출처 열을 안 읽어 MD 매니페스트는 항상 「출처 0종」으로 탈락했다
        if len(cells) >= 6: cut["source"] = cells[5]
        cuts.append(cut)
    return cuts


def cut_bounds(cut: dict) -> tuple[float, float]:
    start = float(cut.get("start", cut.get("t0", cut.get("s", 0))))
    end = float(cut.get("end", cut.get("t1", cut.get("e", start))))
    if end <= start and cut.get("duration") is not None:
        end = start + float(cut["duration"])
    return start, end


def s9_match(cuts: list[dict]) -> dict:
    weighted = total = 0.0
    missing = 0
    for cut in cuts:
        start, end = cut_bounds(cut); length = max(0.0, end - start)
        raw = cut.get("일치", cut.get("match", cut.get("matched")))
        if raw is None:
            missing += 1; continue
        if isinstance(raw, str):
            value = raw.strip().lower()
            if value.endswith("%"):
                raw = float(value[:-1]) / 100.0
            elif value in ("✅", "yes", "true", "일치"):
                raw = 1.0
            elif value in ("❌", "no", "false", "불일치"):
                raw = 0.0
            else:
                try:
                    raw = float(value)
                except ValueError:
                    missing += 1
                    continue
        score = float(raw)
        if score > 1: score /= 100.0
        weighted += length * max(0.0, min(1.0, score)); total += length
    return {"score": weighted / total if total else None, "missing": missing, "seconds": total}


def _gray_frames(p: Path, fps: float = 2.0, w: int = 24, h: int = 42) -> list[list[float]]:
    raw = subprocess.run([FF, "-v", "error", "-i", str(p), "-vf",
                          f"fps={fps},scale={w}:{h},format=gray", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    n = w * h
    return [[float(x) for x in raw[i:i+n]] for i in range(0, len(raw)-n+1, n)]


def s7_variety(p: Path) -> dict:
    """완성본 프레임을 구간으로 접고, 떨어진 구간끼리 shot_variety 지문으로 비교."""
    fps = 2.0; frames = _gray_frames(p, fps=fps)
    if not frames: return {"scenes": 0, "duplicates": []}
    runs = [[0, frames[0]]]
    for i, frame in enumerate(frames[1:], 1):
        if cos(runs[-1][1], frame) < SIM_LIMIT:
            runs.append([i, frame])
        else:
            # 같은 연속구간은 평균 대표 프레임으로 접는다.
            runs[-1][1] = [(a+b)/2 for a, b in zip(runs[-1][1], frame)]
    hits = []
    for i in range(len(runs)):
        for j in range(i + 2, len(runs)):  # 이웃 구간은 컷 연결이므로 중복으로 세지 않는다.
            sim = cos(runs[i][1], runs[j][1])
            if sim >= SIM_LIMIT:
                hits.append((round(runs[i][0]/fps, 2), round(runs[j][0]/fps, 2), round(sim, 3)))
    return {"scenes": len(runs), "duplicates": hits}


def s7_manifest(cuts: list[dict]) -> list[str]:
    """소재 편중 검사 — 정본 §10-1 (2026-08-16). 소재 가짓수에는 상한을 걸지 않는다."""
    problems = []
    if not cuts: return problems
    secs_per, persons = {}, set()
    total = 0.0
    run_person, run_sec = None, 0.0
    for cut in cuts:
        start, end = cut_bounds(cut); length = max(0.0, end-start); total += length
        asset  = str(cut.get("clip", cut.get("asset", cut.get("화면", "")))).strip()
        person = str(cut.get("source", cut.get("출처", cut.get("인물", "")))).strip()
        if asset: secs_per[asset] = secs_per.get(asset, 0.0) + length
        if person and person != "카드": persons.add(person)
        # 한 인물 연속 노출
        if person and person == run_person:
            run_sec += length
        else:
            run_person, run_sec = person, length
        if person and person != "카드" and run_sec > MAX_PERSON_RUN_SEC + 1e-6:
            problems.append(f"인물 '{person}' 연속 {run_sec:.1f}초 > {MAX_PERSON_RUN_SEC:.0f}초 — 다른 인물 컷을 끼울 것")
            run_sec = 0.0
        if 0 < length < MIN_CUT_SEC - 1e-6:
            problems.append(f"{asset or '컷'} {length:.2f}초 < {MIN_CUT_SEC}초")
    if total > 0:
        for asset, sec in sorted(secs_per.items()):
            if sec / total > MAX_ASSET_SHARE + 1e-6:
                problems.append(f"{asset} 분량 {sec/total*100:.0f}% > {MAX_ASSET_SHARE*100:.0f}%")
    if persons and len(persons) < MIN_PERSONS:
        problems.append(f"등장 인물 {len(persons)}명 < {MIN_PERSONS}명")
    return problems


def _caption_changes(p: Path, w: int, h: int) -> list[float]:
    fps = 10; top = int(h * .56); height = int(h * .24)
    raw = subprocess.run([FF, "-v", "error", "-i", str(p), "-vf",
                          f"crop={w}:{height}:0:{top},fps={fps},scale=180:72,format=gray",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    n = 180*72; fs = [raw[i:i+n] for i in range(0, len(raw)-n+1, n)]
    diffs = [sum(abs(a-b) for a,b in zip(fs[i-1][::4], fs[i][::4]))/(n/4) for i in range(1,len(fs))]
    if not diffs: return []
    med = statistics.median(diffs); mad = statistics.median(abs(x-med) for x in diffs)
    threshold = max(3.0, med + 6*mad)
    out=[]
    for i, value in enumerate(diffs, 1):
        t=i/fps
        if value > threshold and (not out or t-out[-1] > .45): out.append(t)
    return out


def _whisper_words(p: Path) -> list[dict] | None:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    with tempfile.TemporaryDirectory(prefix="shorts_s8_") as td:
        wav = Path(td)/"audio.wav"
        subprocess.run([FF,"-y","-v","error","-i",str(p),"-ac","1","-ar","16000",str(wav)], check=True)
        model=WhisperModel("small", device="cpu", compute_type="int8")
        segs,_=model.transcribe(str(wav),language="ko",word_timestamps=True,vad_filter=False,beam_size=5)
        return [{"start":float(w.start),"end":float(w.end),"word":(w.word or "").strip()}
                for s in segs for w in (s.words or []) if (w.word or "").strip()]


def _norm(value: object) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]+", "", str(value)).lower()


def _aligned_speech_onsets(script_units: list[str], words: list[dict]) -> tuple[list[float], float]:
    """대본 구간 시작을 전사 단어 시각에 대응한다.

    문자 단위 difflib 정렬을 쓰므로 숫자 읽기/오독이 뒤 구간까지 누적되지 않는다.
    0.45초 이상 쉰 뒤 시작하며 대본 구간 첫 글자와 실제로 정렬된 단어만 앵커다.
    """
    script_chars = "".join(_norm(x) for x in script_units)
    stt_parts = [_norm(w.get("word", "")) for w in words]
    stt_chars = "".join(stt_parts)
    if not script_chars or not stt_chars:
        return [], 0.0

    script_starts, pos = [], 0
    for unit in script_units:
        script_starts.append(pos)
        pos += len(_norm(unit))
    word_at = []
    for idx, part in enumerate(stt_parts):
        word_at.extend([idx] * len(part))

    matcher = difflib.SequenceMatcher(None, script_chars, stt_chars, autojunk=False)
    script_to_stt = {}
    matched = 0
    for block in matcher.get_matching_blocks():
        for offset in range(block.size):
            script_to_stt[block.a + offset] = block.b + offset
        matched += block.size

    onsets = []
    for start in script_starts:
        stt_pos = script_to_stt.get(start)
        if stt_pos is None or stt_pos >= len(word_at):
            continue
        wi = word_at[stt_pos]
        is_onset = wi == 0 or float(words[wi]["start"]) - float(words[wi - 1]["end"]) >= .45
        if is_onset:
            onsets.append(float(words[wi]["start"]))
    return onsets, matched / max(len(script_chars), len(stt_chars))


def s8_sync(p: Path, w: int, h: int, cuts: list[dict], words: list[dict] | None = None) -> dict:
    caps=_caption_changes(p,w,h); words=_whisper_words(p) if words is None else words
    if words is None: return {"ok":False,"reason":"로컬 faster-whisper 없음"}
    script_units=[str(c.get("말",c.get("speech",c.get("text","")))) for c in cuts]
    script_units=[x for x in script_units if _norm(x)]
    onsets, ratio = _aligned_speech_onsets(script_units, words)
    if not caps or not onsets: return {"ok":False,"reason":"자막 전환 또는 말 시작 검출 실패","align":ratio}
    # 양쪽 모두 시간순 실제 관측치다. 개수가 다르면 가까운 점을 반복 매칭해
    # 좋아 보이게 만들지 않고, 대응 가능한 앞 구간만 비교하며 개수 차이도 탈락시킨다.
    paired=list(zip(caps,onsets))
    errors=[abs(c-o) for c,o in paired]
    if not errors:
        return {"ok":False,"reason":"정렬된 싱크 앵커 없음","align":ratio}
    median=statistics.median(errors); maximum=max(errors)
    count_mismatch = len(caps) != len(onsets)
    return {"ok":maximum <= .30 and not count_mismatch,"median":round(median,3),"max":round(maximum,3),
            "caption_changes":len(caps),"speech_onsets":len(onsets),"align":None if ratio is None else round(ratio,3)}


def log_to_rooms(msg: str):
    """_ROOMS_LOG.md에 자동 기록 — 방이 빼먹을 수 없게."""
    from datetime import datetime
    log_path = Path(__file__).parent.parent / "_ROOMS_LOG.md"
    ts = datetime.now().strftime("%m-%d %H:%M")
    line = f"- `{ts}` **유튜브쇼츠방** — {msg}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)
    print(f"[로그 자동기록] {line.strip()}")


def main() -> int:
    parser=argparse.ArgumentParser(description="쇼츠 S1~S9 렌더 게이트")
    parser.add_argument("target", type=Path)
    parser.add_argument("--manifest", type=Path, help="컷 매니페스트(JSON/MD, S9와 S7 상한의 근거)")
    args=parser.parse_args()
    tgt = args.target
    cuts=load_cut_manifest(args.manifest)
    vids = sorted(tgt.glob("*.mp4")) if tgt.is_dir() else [tgt]
    vids = [v for v in vids if not v.name.startswith("_")]
    if not vids:
        print(f"[탈락] {tgt} 에 mp4 없음"); return 1

    fails, warns = [], []
    for p in vids:
        print(f"\n== 쇼츠 게이트: {p.name} ==")
        v = probe(p)
        w, h, dur = v["width"], v["height"], float(v["duration"])
        is_preview = (w, h) != (1080, 1920)

        if is_preview:
            print(f"  {w}x{h} [프리뷰]  {v['avg_frame_rate']}  {dur:.2f}s  audio={v['audio']}")
        else:
            print(f"  {w}x{h}  {v['avg_frame_rate']}  {dur:.2f}s  audio={v['audio']}")

        # S2: 길이 26~59초 (보완게이트 기준)
        if dur > 59.0:
            fails.append(f"[S2] {p.name} 길이 {dur:.2f}초 — **59초 초과 금지**")
        elif dur < 26.0:
            fails.append(f"[S2] {p.name} 길이 {dur:.2f}초 — **26초 미만 금지**")

        if v["audio"] == 0:
            fails.append(f"[S3] {p.name} 오디오 없음 (쇼츠는 나레이션+BGM)")

        # S8 최우선: starts[]가 아닌 완성본 자막띠 픽셀과 로컬 Whisper만 사용한다.
        sync=s8_sync(p,w,h,cuts)
        if not sync.get("ok"):
            if "max" in sync:
                fails.append(f"[S8] {p.name} 실측 싱크 중앙 {sync['median']:.3f}s · 최대 {sync['max']:.3f}s; "
                             f"앵커 자막/말 {sync['caption_changes']}/{sync['speech_onsets']} (기준 최대 0.300s·개수 일치)")
            else:
                fails.append(f"[S8] {p.name} {sync.get('reason','실측 실패')}")
        else:
            print(f"  S8 실측 싱크 중앙 {sync['median']:.3f}s · 최대 {sync['max']:.3f}s")

        # S9: 말/화면/일치 근거가 없는 렌더도 산출물로 인정하지 않는다.
        if not cuts:
            fails.append(f"[S9] {p.name} 컷 매니페스트 없음 — --manifest에 말/화면/일치를 적어야 한다")
        else:
            match=s9_match(cuts)
            if match["score"] is None or match["missing"]:
                fails.append(f"[S9] {p.name} 일치 판정 누락 {match['missing']}컷")
            elif match["score"] < S9_LIMIT:
                fails.append(f"[S9] {p.name} 말↔화면 길이가중 {match['score']:.1%} < 80%")
            else:
                print(f"  S9 말↔화면 길이가중 {match['score']:.1%}")

        # S7: 완성본 픽셀 중복 + 문서에만 있던 소재 상한을 함께 잠근다.
        variety=s7_variety(p)
        duplicate_count=len(variety["duplicates"])
        if duplicate_count >= 2:
            fails.append(f"[S7] {p.name} 떨어진 중복구간 {duplicate_count}건 >= 2 {variety['duplicates'][:4]}")
        elif duplicate_count == 1:
            warns.append(f"[S7] {p.name} 떨어진 중복구간 1건 {variety['duplicates'][0]}")
        else:
            print(f"  S7 접은 장면 {variety['scenes']}개 · 떨어진 중복 0건")
        for problem in s7_manifest(cuts):
            fails.append(f"[S7] {p.name} {problem}")

        tmp = p.parent / "_review" / f"_gate_{p.stem}"; tmp.mkdir(parents=True, exist_ok=True)
        for f in tmp.glob("*.png"):
            try: f.unlink()
            except OSError: pass   # 임시파일 정리 실패가 검사 결과를 삼키면 안 된다 (2026-08-17)
        for f in tmp.glob("*.jpg"):
            try: f.unlink()
            except OSError: pass

        # S4 경계 무음
        if v["audio"]:
            r = subprocess.run([FF, "-hide_banner", "-i", str(p),
                                "-af", "silencedetect=noise=-45dB:d=0.4", "-f", "null", "-"],
                               capture_output=True, text=True)
            for line in r.stderr.splitlines():
                if "silence_start" in line:
                    try:
                        st = float(line.split("silence_start:")[1].strip())
                        if st < 0.5 or st > dur - 1.2:
                            warns.append(f"[S4] {p.name} 경계 무음 {st:.2f}s — 짧은 BGM loop 사고 확인")
                    except Exception:
                        pass

        # S5 UI존 침범 (해상도에 맞게 계산)
        hits = ui_zone_hits(p, w, h, dur, tmp)
        ui_zone_top = int(h * UI_ZONE_RATIO)
        if hits:
            fails.append(f"[S5] {p.name} 하단 UI존(y>{ui_zone_top})에 자막 침범 "
                         f"{len(hits)}컷 {hits[:4]} — 유튜브 채널바에 묻힌다")
        else:
            print(f"  UI존(y>{ui_zone_top}) 깨끗")

        # S6 발행 전 스샷 시트 (해상도에 맞게)
        ui_zone_top = int(h * UI_ZONE_RATIO)
        ui_zone_height = h - ui_zone_top
        thumb_w, thumb_h = 240, int(240 * h / w)

        # 2026-08-17 수정: 맥 ffmpeg 는 fontfile 없는 drawtext 에서 rc=8 로 죽는다.
        # 시트는 참고용이다 — 실패해도 검사 결과를 삼키면 안 된다.
        _font = ROOT / "assets/fonts/nsqr_eb.ttf"
        _label = (f",drawtext=fontfile={_font}:text='{{t}}s':x=10:y=10:fontsize=28:"
                  "fontcolor=yellow:box=1:boxcolor=black@0.7") if _font.exists() else ""
        for i in range(12):
            t = dur * (i + 0.5) / 12
            vf = (f"drawbox=x=0:y={ui_zone_top}:w={w}:h={ui_zone_height}:color=red@0.9:t=4"
                  + _label.replace("{t}", f"{t:.1f}")
                  + f",scale={thumb_w}:{thumb_h}")
            r = subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.2f}",
                                "-i", str(p), "-frames:v", "1", "-vf", vf,
                                "-q:v", "4", str(tmp / f"sheet_{i:02d}.jpg")], capture_output=True)
            if r.returncode:   # 라벨 없이 한 번 더
                subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.2f}",
                                "-i", str(p), "-frames:v", "1",
                                "-vf", f"drawbox=x=0:y={ui_zone_top}:w={w}:h={ui_zone_height}:color=red@0.9:t=4,scale={thumb_w}:{thumb_h}",
                                "-q:v", "4", str(tmp / f"sheet_{i:02d}.jpg")], capture_output=True)

        sheet = p.parent / f"_발행전_스샷_{p.stem}.jpg"
        subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error",
                        "-pattern_type", "glob", "-i", str(tmp / "sheet_*.jpg"),
                        "-filter_complex", "tile=6x2:margin=8:padding=8:color=0x101014",
                        "-frames:v", "1", "-q:v", "3", str(sheet)], check=True)

        label = "[프리뷰]" if is_preview else ""
        print(f"  스샷 시트{label}: {sheet}")

    print()
    for wmsg in warns:
        print("  [경고] " + wmsg)
    if fails:
        print("\n[게이트 탈락] 이건 산출물이 아니다.")
        for f in fails:
            print("   " + f)
        # 탈락도 로그에 기록
        names = ", ".join(v.name for v in vids)
        log_to_rooms(f"게이트 탈락. {names}. 사유: {fails[0][:50]}...")
        return 1

    print("[통과] 수치 규격 S1~S9")
    print("\n[S6] 발행 전 필수 — 위 스샷 시트를 **차노에게 띄우고** 전체를 보게 한 다음 발행한다.")
    print("   빨간 박스 = 유튜브 UI존. 그 안에 자막이 걸리면 안 된다.")
    print("   코드가 못 잡는 것(톤·어색함·컷 연결)은 만든 쪽이 직접 보고 판단한다.")

    # 자동 로그 기록 — 방이 빼먹을 수 없게
    names = ", ".join(v.name for v in vids)
    log_to_rooms(f"게이트 통과. {names}. 스샷시트 생성. **형 확인 후 발행 대기.**")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
