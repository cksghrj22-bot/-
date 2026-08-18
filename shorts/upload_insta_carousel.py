#!/usr/bin/env python3
"""영상 캐러셀 인스타 발행 — 로컬 파일에서 끝까지

1. 로컬 영상들 → 드라이브 업로드 (공개 URL 획득)
2. 공개 URL들 → 인스타 캐러셀 발행

사용:
    python3 shorts/upload_insta_carousel.py video1.mp4 video2.mp4 ... --caption "캡션" [--dry-run]
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def upload_video_carousel(
    video_paths: list[str | Path],
    caption: str,
    folder_id: str = None,
    dry_run: bool = True
) -> str:
    """영상 캐러셀 발행.
    
    Args:
        video_paths: 로컬 영상 파일 경로 (2~10개)
        caption: 캡션
        folder_id: 드라이브 업로드 폴더 (없으면 루트)
        dry_run: True면 URL 실측만, False면 실제 발행
    
    Returns:
        미디어 ID (dry_run이면 "(dry-run)")
    """
    from shorts.make_public_url import make_public_urls
    from shorts.upload_instagram import load_credentials, upload_mixed_carousel
    
    video_paths = [Path(p) for p in video_paths]
    
    # 1) 파일 존재 확인
    for p in video_paths:
        if not p.exists():
            raise FileNotFoundError(f"영상 없음: {p}")
    
    print(f"[1/3] 드라이브 업로드 ({len(video_paths)}개)...")
    urls = make_public_urls(video_paths, folder_id)
    for p, u in zip(video_paths, urls):
        print(f"  {p.name} → {u[:60]}...")
    
    # 2) 인스타 업로드용 아이템 구성
    items = [{"url": u, "kind": "video"} for u in urls]
    
    print(f"\n[2/3] 인스타 캐러셀 준비...")
    creds = load_credentials(ROOT / "secrets/instagram.json")
    
    # 3) 발행
    print(f"\n[3/3] {'DRY RUN' if dry_run else '발행'}...")
    media_id = upload_mixed_carousel(items, caption, creds, dry_run=dry_run)
    
    if not dry_run:
        print(f"\n✅ 발행 완료: {media_id}")
    
    return media_id


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="영상 캐러셀 인스타 발행")
    parser.add_argument("videos", nargs="+", help="영상 파일들")
    parser.add_argument("--caption", "-c", required=True, help="캡션")
    parser.add_argument("--folder", "-f", help="드라이브 폴더 ID")
    parser.add_argument("--publish", action="store_true", help="실제 발행 (기본: dry-run)")
    
    args = parser.parse_args()
    
    try:
        result = upload_video_carousel(
            args.videos,
            args.caption,
            folder_id=args.folder,
            dry_run=not args.publish
        )
        print(f"\n결과: {result}")
    except Exception as e:
        print(f"\n❌ 실패: {e}")
        sys.exit(1)
