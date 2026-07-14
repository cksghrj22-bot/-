"""CLI 진입점.

사용법:
    python -m pipeline add <파일_또는_디렉터리> [--index data/index.json]
    python -m pipeline search "질의어" [--index data/index.json] [--top-k 5]
    python -m pipeline briefing [--date YYYY-MM-DD] [--config config.json]
"""

from __future__ import annotations

import argparse
import datetime
from pathlib import Path

from .briefing import generate_briefing, load_config
from .chunk import chunk_document
from .index import Index
from .ingest import load_directory, load_file

DEFAULT_INDEX = "data/index.json"


def _load_or_create(index_path: Path) -> Index:
    return Index.load(index_path) if index_path.exists() else Index()


def cmd_add(args: argparse.Namespace) -> None:
    index_path = Path(args.index)
    index = _load_or_create(index_path)

    target = Path(args.path)
    docs = list(load_directory(target)) if target.is_dir() else [load_file(target)]

    total_chunks = 0
    for doc in docs:
        chunks = chunk_document(doc)
        index.add_all(chunks)
        total_chunks += len(chunks)

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index.save(index_path)
    print(f"문서 {len(docs)}건, 청크 {total_chunks}개 인덱싱 완료 → {index_path}")


def cmd_search(args: argparse.Namespace) -> None:
    index_path = Path(args.index)
    if not index_path.exists():
        raise SystemExit(f"인덱스가 없습니다: {index_path} (먼저 add를 실행하세요)")
    index = Index.load(index_path)

    results = index.search(args.query, top_k=args.top_k)
    if not results:
        print("검색 결과가 없습니다.")
        return
    for rank, (chunk, score) in enumerate(results, start=1):
        preview = chunk.text.replace("\n", " ")[:120]
        print(f"{rank}. [{score:.3f}] {chunk.source} ({chunk.chunk_id})")
        print(f"   {preview}")


def cmd_add_vault(args: argparse.Namespace) -> None:
    from .obsidian import load_vault

    index_path = Path(args.index)
    index = _load_or_create(index_path)

    docs = list(load_vault(args.path))
    total_chunks = 0
    for doc in docs:
        chunks = chunk_document(doc)
        index.add_all(chunks)
        total_chunks += len(chunks)

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index.save(index_path)
    print(f"옵시디언 노트 {len(docs)}건, 청크 {total_chunks}개 인덱싱 완료 → {index_path}")


def cmd_briefing(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    date_str = args.date or datetime.date.today().isoformat()
    output = generate_briefing(date_str, config)
    print(f"브리핑 생성 완료 → {output}")
    print(output.read_text(encoding="utf-8"))


def cmd_youtube_stats(args: argparse.Namespace) -> None:
    from .youtube_stats import fetch_recent_videos, load_secrets, render_report

    key, channel = load_secrets(args.secrets)
    videos = fetch_recent_videos(key, channel, limit=args.limit)
    report = render_report(videos, top=args.top)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"리포트 저장 → {out}")
    print(report)


def main() -> None:
    parser = argparse.ArgumentParser(prog="pipeline", description="지식파이프라인 CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="파일/디렉터리를 인덱스에 추가")
    p_add.add_argument("path")
    p_add.add_argument("--index", default=DEFAULT_INDEX)
    p_add.set_defaults(func=cmd_add)

    p_search = sub.add_parser("search", help="인덱스에서 검색")
    p_search.add_argument("query")
    p_search.add_argument("--index", default=DEFAULT_INDEX)
    p_search.add_argument("--top-k", type=int, default=5)
    p_search.set_defaults(func=cmd_search)

    p_vault = sub.add_parser("add-vault", help="Obsidian vault를 인덱스에 추가")
    p_vault.add_argument("path", help="vault 폴더 경로 (iCloud: ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/볼트이름)")
    p_vault.add_argument("--index", default=DEFAULT_INDEX)
    p_vault.set_defaults(func=cmd_add_vault)

    p_stats = sub.add_parser("youtube-stats", help="채널 조회수 리포트 (조합 엔진 입력)")
    p_stats.add_argument("--secrets", default="secrets")
    p_stats.add_argument("--limit", type=int, default=50)
    p_stats.add_argument("--top", type=int, default=15)
    p_stats.add_argument("--output", default=None, help="저장할 마크다운 경로")
    p_stats.set_defaults(func=cmd_youtube_stats)

    p_brief = sub.add_parser("briefing", help="피드 수집 + 인덱싱 + 아침 브리핑 생성")
    p_brief.add_argument("--date", default=None, help="YYYY-MM-DD (기본: 오늘)")
    p_brief.add_argument("--config", default="config.json")
    p_brief.set_defaults(func=cmd_briefing)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
