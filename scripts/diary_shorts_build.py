#!/usr/bin/env python3
"""Build the split-screen AI diary short from a fresh interview take.

Usage:
    python3 scripts/diary_shorts_build.py interview.mov screen.mov output.mp4

The interview is cut once inside a single ffmpeg filter graph.  This avoids the
audio drift observed when separately encoded chunks are concatenated.  A
faster-whisper installation is used by default; ``--words-json`` provides a
deterministic/offline input for repeatable builds and tests.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable, Sequence


FILLERS = {"어", "아", "음", "그", "저", "저기", "자"}
SCREEN_PRESETS = {
    "general_a": (742.0, "1612:1147:139:250"),
    "rules": (222.0, "1612:1147:380:140"),
    "general_b": (700.0, "1612:1147:139:250"),
    "log": (796.0, "1612:1147:139:300"),
    "check": (768.0, "1612:1147:139:453"),
    "blocked": (224.0, "1612:1147:1740:718"),
    "summary": (822.0, "1612:1147:139:250"),
}


@dataclass(frozen=True)
class Span:
    start: float
    end: float

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass(frozen=True)
class Word:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class Caption:
    start: float
    end: float
    text: str


def run(cmd: Sequence[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(cmd), check=True, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def duration(path: Path) -> float:
    cp = run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", str(path),
    ], capture=True)
    return float(cp.stdout.strip())


def parse_silences(stderr: str) -> list[Span]:
    starts: list[float] = []
    silences: list[Span] = []
    for line in stderr.splitlines():
        match = re.search(r"silence_start:\s*([0-9.]+)", line)
        if match:
            starts.append(float(match.group(1)))
            continue
        match = re.search(r"silence_end:\s*([0-9.]+)", line)
        if match and starts:
            silences.append(Span(starts.pop(0), float(match.group(1))))
    return silences


def speech_from_silences(silences: Sequence[Span], total: float) -> list[Span]:
    speech: list[Span] = []
    cursor = 0.0
    for silence in sorted(silences, key=lambda item: item.start):
        if silence.start > cursor:
            speech.append(Span(cursor, min(total, silence.start)))
        cursor = max(cursor, silence.end)
    if cursor < total:
        speech.append(Span(cursor, total))
    return [item for item in speech if item.duration >= 0.08]


def normalize_token(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]", "", text).lower()


def words_in_span(words: Sequence[Word], span: Span) -> list[Word]:
    return [word for word in words if word.end > span.start and word.start < span.end]


def clean_speech_spans(speech: Sequence[Span], words: Sequence[Word], total: float) -> list[Span]:
    """Remove leading filler tokens and retain no more than 0.40s between chunks."""
    cleaned: list[tuple[Span, str]] = []
    for raw in speech:
        chunk_words = words_in_span(words, raw)
        if not chunk_words:
            continue
        first_real = 0
        while first_real < len(chunk_words) - 1 and normalize_token(chunk_words[first_real].text) in FILLERS:
            first_real += 1
        start = max(raw.start, chunk_words[first_real].start - 0.15)
        end = min(total, raw.end)
        if end - start < 0.12:
            continue
        text = " ".join(normalize_token(w.text) for w in chunk_words[first_real:])
        cleaned.append((Span(start, end), text))

    # If two adjacent speech chunks are effectively the same take, retain the latter.
    keep = [True] * len(cleaned)
    for index in range(len(cleaned) - 1):
        left, right = cleaned[index][1], cleaned[index + 1][1]
        if min(len(left), len(right)) >= 5 and SequenceMatcher(None, left, right).ratio() >= 0.88:
            keep[index] = False

    selected = [item[0] for index, item in enumerate(cleaned) if keep[index]]
    if not selected:
        return []

    padded: list[Span] = []
    for index, item in enumerate(selected):
        start = max(0.0, item.start - (0.15 if index else 0.0))
        end = min(total, item.end + (0.25 if index + 1 < len(selected) else 0.55))
        if padded and start - padded[-1].end <= 0.40:
            padded[-1] = Span(padded[-1].start, max(padded[-1].end, end))
        else:
            padded.append(Span(start, end))
    return padded


def map_source_time(source_time: float, kept: Sequence[Span]) -> float:
    result = 0.0
    for item in kept:
        if source_time >= item.end:
            result += item.duration
        elif source_time > item.start:
            result += source_time - item.start
            break
        else:
            break
    return result


def wrap_caption(text: str, limit: int = 26) -> str:
    tokens = text.split()
    if len(text) <= limit or len(tokens) <= 1:
        return text
    lines = [""]
    for token in tokens:
        extra = len(token) + (1 if lines[-1] else 0)
        if lines[-1] and len(lines[-1]) + extra > limit and len(lines) < 2:
            lines.append("")
        lines[-1] = (lines[-1] + " " + token).strip()
    return "\\N".join(line for line in lines if line)


def captions_for_spans(kept: Sequence[Span], words: Sequence[Word]) -> list[Caption]:
    captions: list[Caption] = []
    for span in kept:
        chunk = words_in_span(words, span)
        if not chunk:
            continue
        while len(chunk) > 1 and normalize_token(chunk[0].text) in FILLERS:
            chunk.pop(0)
        groups: list[list[Word]] = []
        for word in chunk:
            proposed = " ".join(item.text.strip() for item in (groups[-1] if groups else []) + [word])
            new_phrase = bool(groups and word.start - groups[-1][-1].end >= 0.20)
            if not groups or new_phrase or len(proposed) > 48:
                groups.append([word])
            else:
                groups[-1].append(word)
        for group in groups:
            text = " ".join(word.text.strip() for word in group).strip()
            text = text.replace("{", "(").replace("}", ")")
            start = map_source_time(max(span.start, group[0].start - 0.08), kept)
            end = map_source_time(min(span.end, group[-1].end + 0.18), kept)
            if text and end > start:
                captions.append(Caption(start, end, wrap_caption(text)))
    return captions


def ass_time(value: float) -> str:
    value = max(0.0, value)
    hours = int(value // 3600)
    minutes = int(value % 3600 // 60)
    seconds = value % 60
    return f"{hours}:{minutes:02d}:{seconds:05.2f}"


def write_ass(path: Path, captions: Sequence[Caption], total: float) -> None:
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: KR,Noto Sans CJK KR,60,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,3,10,0,2,40,40,760,1
Style: HD,Noto Sans CJK KR,34,&H4DFFFFFF,&H4DFFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,3,40,44,268,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    for item in captions:
        lines.append(
            f"Dialogue: 0,{ass_time(item.start)},{ass_time(item.end)},KR,,0,0,0,,{item.text}\n"
        )
    lines.append(f"Dialogue: 0,0:00:00.00,{ass_time(total)},HD,,0,0,0,,@Atnownchano\n")
    path.write_text("".join(lines), encoding="utf-8")


def load_words(path: Path) -> list[Word]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_words = payload.get("words", payload) if isinstance(payload, dict) else payload
    return [Word(float(item["start"]), float(item["end"]), str(item.get("text", item.get("word", ""))))
            for item in raw_words]


def transcribe(audio: Path, model_name: str) -> list[Word]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper가 없습니다. 설치 후 다시 실행하거나 --words-json을 지정하세요."
        ) from exc
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(
        str(audio), language="ko", word_timestamps=True, vad_filter=False, beam_size=5,
    )
    return [Word(float(word.start), float(word.end), (word.word or "").strip())
            for segment in segments for word in (segment.words or []) if (word.word or "").strip()]


def detect_speech(audio: Path, total: float) -> list[Span]:
    cp = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(audio),
         "-af", "silencedetect=noise=-36dB:d=0.20", "-f", "null", "-"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if cp.returncode:
        raise RuntimeError("silencedetect 실패\n" + cp.stderr[-2000:])
    return speech_from_silences(parse_silences(cp.stderr), total)


def joined_text(captions: Sequence[Caption]) -> str:
    return " ".join(item.text.replace("\\N", " ") for item in captions)


def find_caption_time(captions: Sequence[Caption], needles: Iterable[str], default: float) -> float:
    normalized_needles = [normalize_token(item) for item in needles]
    for item in captions:
        haystack = normalize_token(item.text.replace("\\N", " "))
        if any(needle in haystack for needle in normalized_needles):
            return item.start
    return default


def screen_sections(captions: Sequence[Caption], total: float) -> list[tuple[str, float]]:
    # Keyword anchors preserve evidence-to-dialogue matching after a different take.
    points = [
        ("general_a", 0.0),
        ("rules", find_caption_time(captions, ["지켜야", "몇 초까지"], total * 0.17)),
        ("general_b", find_caption_time(captions, ["문서에", "적어놨어"], total * 0.34)),
        ("log", find_caption_time(captions, ["검사하는", "자동으로"], total * 0.48)),
        ("check", find_caption_time(captions, ["길이가 넘", "자막이 아래"], total * 0.62)),
        ("blocked", find_caption_time(captions, ["아예 안", "열 컷"], total * 0.73)),
        ("summary", find_caption_time(captions, ["제 눈", "통과한"], total * 0.84)),
    ]
    points.sort(key=lambda item: item[1])
    sections: list[tuple[str, float]] = []
    for index, (name, start) in enumerate(points):
        end = points[index + 1][1] if index + 1 < len(points) else total
        if end - start >= 0.05:
            sections.append((name, end - start))
    return sections


def render(interview: Path, screen: Path, output: Path, kept: Sequence[Span],
           captions: Sequence[Caption], ass_path: Path) -> None:
    total = sum(item.duration for item in kept)
    filters: list[str] = []
    concat_labels: list[str] = []
    for index, item in enumerate(kept, 1):
        filters.append(
            f"[0:v]trim={item.start:.6f}:{item.end:.6f},setpts=PTS-STARTPTS[tv{index}]"
        )
        filters.append(
            f"[0:a]atrim={item.start:.6f}:{item.end:.6f},asetpts=PTS-STARTPTS[ta{index}]"
        )
        concat_labels.append(f"[tv{index}][ta{index}]")
    filters.append(
        "".join(concat_labels) + f"concat=n={len(kept)}:v=1:a=1[mv][ma]"
    )
    filters.append("[mv]scale=1080:1920,crop=1080:1152:0:180,setsar=1,fps=30[top]")

    inputs = ["-i", str(interview)]
    bottom_labels: list[str] = []
    sections = screen_sections(captions, total)
    for index, (name, section_duration) in enumerate(sections, 1):
        offset, crop = SCREEN_PRESETS[name]
        inputs.extend(["-ss", f"{offset:.3f}", "-i", str(screen)])
        filters.append(
            f"[{index}:v]trim=0:{section_duration:.6f},setpts=PTS-STARTPTS,"
            f"tpad=stop_mode=clone:stop_duration={section_duration:.6f},"
            f"trim=0:{section_duration:.6f},crop={crop},scale=1080:768,setsar=1,fps=30[b{index}]"
        )
        bottom_labels.append(f"[b{index}]")
    filters.append("".join(bottom_labels) + f"concat=n={len(bottom_labels)}:v=1:a=0[bot]")
    filters.append("[top][bot]vstack=inputs=2[stack]")
    escaped_ass = str(ass_path).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    fade_start = max(0.0, total - 1.3)
    filters.append(f"[stack]ass='{escaped_ass}',fade=t=out:st={fade_start:.6f}:d=1.3[v]")
    filters.append(
        f"[ma]aresample=48000,loudnorm=I=-15.4:TP=-1.5:LRA=11,"
        f"afade=t=out:st={max(0.0, total - 1.2):.6f}:d=1.2[a]"
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    run([
        "ffmpeg", "-y", "-hide_banner", *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[v]", "-map", "[a]", "-t", f"{total:.6f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
        str(output),
    ])


def verify_output(path: Path) -> dict[str, object]:
    cp = run([
        "ffprobe", "-v", "error", "-show_entries",
        "stream=codec_type,width,height,r_frame_rate,sample_rate,duration:format=duration,size",
        "-of", "json", str(path),
    ], capture=True)
    payload = json.loads(cp.stdout)
    video = next(item for item in payload["streams"] if item["codec_type"] == "video")
    audio = next(item for item in payload["streams"] if item["codec_type"] == "audio")
    video_duration = float(video.get("duration", payload["format"]["duration"]))
    audio_duration = float(audio.get("duration", payload["format"]["duration"]))
    result = {
        "width": int(video["width"]), "height": int(video["height"]),
        "fps": video["r_frame_rate"], "sample_rate": int(audio["sample_rate"]),
        "video_duration": video_duration, "audio_duration": audio_duration,
        "av_delta": abs(video_duration - audio_duration),
        "bytes": int(payload["format"]["size"]),
    }
    if (result["width"], result["height"]) != (1080, 1920):
        raise RuntimeError(f"출력 해상도 실패: {result['width']}x{result['height']}")
    if result["sample_rate"] != 48000:
        raise RuntimeError(f"출력 오디오 샘플레이트 실패: {result['sample_rate']}")
    if result["av_delta"] > 0.05:
        raise RuntimeError(f"A/V 싱크 길이차 실패: {result['av_delta']:.3f}s")
    return result


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("interview", type=Path)
    parser.add_argument("screen", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--words-json", type=Path, help="offline word timestamps")
    parser.add_argument("--model", default="medium", help="faster-whisper model (default: medium)")
    parser.add_argument("--dry-run", action="store_true", help="write plan/ASS without rendering")
    parser.add_argument("--no-gate", action="store_true", help="skip scripts/shorts_gate.py")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    for binary in ("ffmpeg", "ffprobe"):
        if not shutil.which(binary):
            raise SystemExit(f"필수 실행파일 없음: {binary}")
    for path in (args.interview, args.screen):
        if not path.is_file():
            raise SystemExit(f"입력파일 없음: {path}")

    total = duration(args.interview)
    with tempfile.TemporaryDirectory(prefix="diary-shorts-") as temp_dir:
        temp = Path(temp_dir)
        audio = temp / "interview.wav"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(args.interview),
             "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(audio)])
        speech = detect_speech(audio, total)
        try:
            words = load_words(args.words_json) if args.words_json else transcribe(audio, args.model)
        except RuntimeError as exc:
            raise SystemExit(str(exc)) from exc
        kept = clean_speech_spans(speech, words, total)
        if not kept:
            raise SystemExit("남길 완성 문장을 찾지 못했습니다.")
        captions = captions_for_spans(kept, words)
        if not captions:
            raise SystemExit("자막용 대사를 찾지 못했습니다.")

        out_total = sum(item.duration for item in kept)
        sidecar = args.output.with_suffix(".build.json")
        ass_path = args.output.with_suffix(".ass")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_ass(ass_path, captions, out_total)
        plan = {
            "interview": str(args.interview), "screen": str(args.screen),
            "output": str(args.output), "source_duration": total,
            "output_duration_planned": out_total,
            "kept_spans": [item.__dict__ for item in kept],
            "captions": [item.__dict__ for item in captions],
            "screen_sections": screen_sections(captions, out_total),
            "transcript": joined_text(captions),
        }
        sidecar.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if args.dry_run:
            print(json.dumps(plan, ensure_ascii=False, indent=2))
            return 0

        render(args.interview, args.screen, args.output, kept, captions, ass_path)
        measured = verify_output(args.output)
        plan["verified"] = measured
        sidecar.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(measured, ensure_ascii=False, indent=2))

        if not args.no_gate:
            gate = Path(__file__).with_name("shorts_gate.py")
            if not gate.is_file():
                raise SystemExit(f"게이트 없음: {gate}")
            run([sys.executable, str(gate), str(args.output)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
