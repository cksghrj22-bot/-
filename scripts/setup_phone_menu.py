#!/usr/bin/env python3
"""
폰용 마무리 설치 — 전략실이 원격으로 실행 (2026-08-17)
  ① ~/.zshrc 에 본진/bj 별칭 등록 (있으면 건너뜀)
  ② ~/.codex/config.toml 의 model 줄 제거 — o4-mini 가 ChatGPT 계정에서 400 나던 것
백업을 남기고, 아무것도 삭제하지 않는다.
"""
import re, shutil, time
from pathlib import Path

HOME = Path.home()
TARGET = HOME / "atnown-content-pipeline" / "scripts" / "menu.sh"
out = []

# ① 별칭
rc = HOME / ".zshrc"
rc.touch(exist_ok=True)
body = rc.read_text()
if "scripts/menu.sh" in body:
    out.append("① 별칭: 이미 등록돼 있음")
elif not TARGET.exists():
    out.append(f"① 별칭: ⛔ menu.sh 없음 ({TARGET})")
else:
    shutil.copy2(rc, rc.with_suffix(f".zshrc.bak.{int(time.time())}"))
    rc.write_text(body.rstrip("\n") + (
        "\n\n# >>> 본진 메뉴 (전략기획및개인업무 방)\n"
        f"alias 본진='zsh {TARGET}'\n"
        f"alias bj='zsh {TARGET}'\n"
        "# <<< 본진 메뉴\n"))
    out.append("① 별칭: ✅ 본진 · bj 등록 완료 (.zshrc 백업함)")

# ② Codex 모델
cfg = HOME / ".codex" / "config.toml"
if not cfg.exists():
    out.append(f"② Codex: ⛔ 설정파일 없음 ({cfg})")
else:
    txt = cfg.read_text()
    hit = [l for l in txt.splitlines() if re.match(r'^\s*model\s*=', l)]
    if not hit:
        out.append("② Codex: model 줄 없음 — 이미 기본값")
    else:
        shutil.copy2(cfg, cfg.with_name(f"config.toml.bak.{int(time.time())}"))
        new = "\n".join(l for l in txt.splitlines() if not re.match(r'^\s*model\s*=', l))
        cfg.write_text(new + "\n")
        out.append(f"② Codex: ✅ 제거함 → {' / '.join(x.strip() for x in hit)}  (백업함)")

print("\n".join(out))
