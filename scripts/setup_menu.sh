#!/bin/zsh
# 본진 메뉴 등록 — 한 번만 실행
# ~/.zshrc 에 넣으므로 맥 터미널·폰 SSH 양쪽에서 똑같이 먹는다.
RC="$HOME/.zshrc"
TARGET="$HOME/atnown-content-pipeline/scripts/menu.sh"
MARK="# >>> 본진 메뉴"

[ -f "$TARGET" ] || { echo "⛔ menu.sh 없음: $TARGET"; exit 1; }
touch "$RC"

if grep -q "scripts/menu.sh" "$RC" 2>/dev/null; then
  echo "✅ 이미 등록돼 있습니다."
else
  {
    printf '\n%s (전략기획및개인업무 방)\n' "$MARK"
    printf "alias 본진='zsh %s'\n" "$TARGET"
    printf "alias bj='zsh %s'\n" "$TARGET"
    printf '# <<< 본진 메뉴\n'
  } >> "$RC"
  echo "✅ 등록 완료 → $RC"
fi

echo ""
echo "───────────────────────────"
echo " 지금 바로 쓰려면 한 줄:"
echo ""
echo "   source ~/.zshrc"
echo ""
echo " 그 다음부터 언제든:"
echo "   본진   (한글)"
echo "   bj     (영문 — 폰에서 자판 안 바꿔도 됨)"
echo ""
echo " 맥 터미널·폰 SSH 둘 다 똑같이 됩니다."
echo "───────────────────────────"
