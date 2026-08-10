#!/bin/bash
# 렌더 전 전수검사 — 본진에서 전부 돈다.
# 왜(2026-08-10 형 지시: "본진으로 보내라니까 왜 말을 안 들어 / 영상스틸도 본진이 뽑게해"):
# 지금까지 코워크 방이 자기 컨테이너로 파일을 끌어가 재고 스틸을 뽑았다.
# 그래서 방마다 다른 걸 보고 다른 판정을 냈다. 정본은 본진 하나다.
BASE="$HOME/atnown-content-pipeline"
OUT="$BASE/_cowork_sync/_sheets"
mkdir -p "$OUT"
cd "$BASE" || exit 1
echo "═══ 렌더 전 검사 $(date '+%m-%d %H:%M') ═══"
for j in "$@"; do
  [ -f "$j" ] || continue
  tag=$(basename "$j" .json)
  echo ""; echo "── $tag ──"
  python3 scripts/bridge_guard.py "$j" 2>&1 | sed -n '3,40p'
  python3 scripts/shot_variety.py "$j" 2>&1 | sed -n '2,20p'
  python3 scripts/cap_clip_sheet.py "$j" 2>&1 | tail -1
  mv -f "/tmp/capclip_${tag}.jpg" "$OUT/${tag}_대조표.jpg" 2>/dev/null && echo "   대조표 → _cowork_sync/_sheets/${tag}_대조표.jpg"
done
echo ""; echo "스틸·대조표 전부 $OUT 에 있다. 코워크 방은 여기서 가져다 본다."
