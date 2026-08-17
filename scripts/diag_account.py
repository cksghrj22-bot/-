#!/usr/bin/env python3
"""본진 클로드 코드에 로그인된 계정 확인
   ⚠️ 토큰·키는 출력하지 않는다. 계정 식별 정보만."""
import json
from pathlib import Path

HOME = Path.home()
KEYS = ("email", "emailAddress", "accountUuid", "organizationName",
        "subscriptionType", "planType", "billingType")

def walk(o, path=""):
    hits = []
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, (dict, list)):
                hits += walk(v, f"{path}.{k}")
            elif k in KEYS:
                hits.append((f"{path}.{k}".lstrip("."), v))
    elif isinstance(o, list):
        for i, v in enumerate(o[:20]):
            hits += walk(v, f"{path}[{i}]")
    return hits

found = False
for name in (".claude.json", ".claude/config.json", ".config/claude/config.json"):
    f = HOME / name
    if not f.exists():
        continue
    try:
        d = json.loads(f.read_text())
    except Exception as e:
        print(f"[{name}] 읽기 실패: {e}"); continue
    hits = walk(d)
    if hits:
        found = True
        print(f"[{name}]")
        for k, v in hits:
            print(f"   {k} = {v}")
if not found:
    print("설정 파일에서 계정 정보를 못 찾음 — 터미널에서 /status 로 확인 필요")
