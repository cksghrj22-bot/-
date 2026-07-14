"""쇼츠 파이프라인 CLI.

    python -m shorts run [--config shorts_config.json] [--dry-run]

inbox 폴더에서 영상(.mp4/.mov)과 같은 이름의 대사 스크립트(.txt)를 짝지어:
자막 굽기 → BGM 믹싱 → 유튜브/인스타 업로드 → done/ 폴더로 이동.
--dry-run이면 업로드 없이 렌더링까지만 한다.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from . import render as render_mod
from . import upload_instagram, upload_youtube
from .subtitles import parse_script

VIDEO_EXTS = {".mp4", ".mov", ".m4v"}

DEFAULT_CONFIG = {
    "inbox": "~/Shorts/inbox",
    "done": "~/Shorts/done",
    "output": "~/Shorts/rendered",
    "bgm": "",
    "bgm_volume": 0.15,
    "subtitle_style": {},
    "youtube": {"enabled": True, "credentials": "secrets/youtube.json", "privacy": "private"},
    "instagram": {"enabled": False, "credentials": "secrets/instagram.json"},
}


def load_config(path: str | Path) -> dict:
    config = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
    p = Path(path)
    if p.exists():
        user_config = json.loads(p.read_text(encoding="utf-8"))
        for key, value in user_config.items():
            if isinstance(value, dict) and isinstance(config.get(key), dict):
                config[key].update(value)
            else:
                config[key] = value
    return config


def find_jobs(inbox: Path) -> list[tuple[Path, Path]]:
    """(영상, 스크립트) 짝 목록. 스크립트 없는 영상은 건너뛰고 알린다."""
    jobs = []
    for video in sorted(inbox.iterdir()):
        if video.suffix.lower() not in VIDEO_EXTS:
            continue
        script = video.with_suffix(".txt")
        if script.exists():
            jobs.append((video, script))
        else:
            print(f"건너뜀 (스크립트 없음): {video.name} — {script.name}을 만들어주세요")
    return jobs


def run(config: dict, dry_run: bool = False) -> None:
    inbox = Path(config["inbox"]).expanduser()
    done = Path(config["done"]).expanduser()
    out_dir = Path(config["output"]).expanduser()
    if not inbox.exists():
        raise SystemExit(f"inbox 폴더가 없습니다: {inbox}")

    jobs = find_jobs(inbox)
    if not jobs:
        print("처리할 영상이 없습니다.")
        return

    for video, script_path in jobs:
        script = parse_script(script_path.read_text(encoding="utf-8"))
        title = script.title or video.stem
        print(f"렌더링: {video.name} — {title}")
        rendered = render_mod.render(
            video,
            script,
            out_dir / f"{video.stem}_final.mp4",
            bgm=config["bgm"] or None,
            bgm_volume=config["bgm_volume"],
            style=config["subtitle_style"] or None,
            workdir=out_dir,
        )

        if dry_run:
            print(f"  dry-run: 업로드 생략 → {rendered}")
            continue

        if config["youtube"]["enabled"]:
            creds = upload_youtube.load_credentials(config["youtube"]["credentials"])
            metadata = upload_youtube.build_metadata(
                title=title,
                description=script.description,
                tags=script.tags,
                privacy=config["youtube"].get("privacy", "private"),
                publish_at=config["youtube"].get("publish_at"),
            )
            video_id = upload_youtube.upload(rendered, metadata, creds)
            print(f"  유튜브 업로드 완료: https://youtube.com/shorts/{video_id}")

        if config["instagram"]["enabled"]:
            creds = upload_instagram.load_credentials(config["instagram"]["credentials"])
            caption = f"{title}\n\n{script.description}".strip()
            media_id = upload_instagram.upload_reel(rendered, caption, creds)
            print(f"  인스타 릴스 게시 완료: media_id={media_id}")

        done.mkdir(parents=True, exist_ok=True)
        shutil.move(str(video), done / video.name)
        shutil.move(str(script_path), done / script_path.name)
        print(f"  완료 → {done / video.name}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="shorts", description="쇼츠 자동화 파이프라인")
    sub = parser.add_subparsers(dest="command", required=True)
    p_run = sub.add_parser("run", help="inbox의 영상을 일괄 처리")
    p_run.add_argument("--config", default="shorts_config.json")
    p_run.add_argument("--dry-run", action="store_true", help="업로드 없이 렌더링까지만")
    args = parser.parse_args()

    run(load_config(args.config), dry_run=args.dry_run)


if __name__ == "__main__":
    main()
