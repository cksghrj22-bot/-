#!/bin/zsh
# 옵시디언 볼트 → 리포 동기화
# iCloud 경로 접근 권한 필요

set -e

VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/앳나운_옵시디언_볼트"
DEST="$HOME/atnown-content-pipeline/_obsidian_mirror"
LOG="$HOME/atnown-logs/brainsync.log"

mkdir -p "$DEST"
mkdir -p "$(dirname "$LOG")"

echo "=== brain_sync $(date) ===" >> "$LOG"

# 복사할 파일들 (중요 브레인 파일만)
FILES=(
    "차노_브레인_생각의흐름.md"
    "차노_결정사항_대장.md"
    "차노_왜사전.md"
    "차노_단축어.md"
)

for f in "${FILES[@]}"; do
    src="$VAULT/$f"
    if [ -f "$src" ]; then
        cp "$src" "$DEST/" 2>> "$LOG" && echo "  ✓ $f" >> "$LOG" || echo "  ✗ $f (권한문제)" >> "$LOG"
    else
        echo "  - $f (없음)" >> "$LOG"
    fi
done

# 판단 폴더 동기화
if [ -d "$VAULT/판단" ]; then
    mkdir -p "$DEST/판단"
    rsync -a --ignore-errors "$VAULT/판단/" "$DEST/판단/" 2>> "$LOG"
    echo "  ✓ 판단 폴더" >> "$LOG"
fi

echo "=== 완료 ===" >> "$LOG"
