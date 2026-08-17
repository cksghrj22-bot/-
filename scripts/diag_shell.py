#!/usr/bin/env python3
"""셸 진입 진단 — 접속하면 왜 클로드 코드가 먼저 뜨나?
   ⚠️ .zshrc 전문을 찍지 않는다(키가 들어있을 수 있음). 판정 결과만."""
import re
from pathlib import Path

HOME = Path.home()
out = []
for name in (".zshrc", ".zprofile", ".zlogin", ".zshenv"):
    f = HOME / name
    if not f.exists():
        continue
    lines = [l for l in f.read_text(errors="ignore").splitlines()]
    live = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    launch = [l.strip() for l in live
              if re.search(r'(^|\s|;|&&|\|\|)(claude|exec\s+claude)(\s|$)', l)
              and not l.strip().startswith("alias")]
    aliases = [l.strip() for l in live if l.strip().startswith("alias") and
               re.search(r'(본진|bj|클로드|claude)', l)]
    out.append(f"[{name}] 총 {len(live)}줄")
    if launch:
        out.append("  ⚠️ 접속하면 자동 실행되는 줄:")
        out += [f"     {l}" for l in launch]
    else:
        out.append("  ✅ 자동 실행 줄 없음")
    if aliases:
        out.append("  별칭:")
        out += [f"     {l}" for l in aliases]
    if live:
        out.append(f"  마지막 줄: {live[-1][:70]}")
print("\n".join(out))
