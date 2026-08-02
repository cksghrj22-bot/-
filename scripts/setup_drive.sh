#!/usr/bin/env bash
# 🚗 코덱스/새 세션 구글드라이브 원클릭 세팅 — 플러그인(MCP) 없이 코드로 붙인다.
# 배경: Drive는 커넥터 플러그인이 아니라 (1)공유링크 다운로드 (2)secrets/gdrive.json OAuth 로 붙는다.
# 사용:
#   bash scripts/setup_drive.sh              # 상태 진단 + 다음 할 일 안내
#   bash scripts/setup_drive.sh <fileId>     # 공유링크 다운로드 실측 테스트(키 불필요)
set -u
cd "$(dirname "$0")/.." || exit 1
SEC="secrets/gdrive.json"
echo "== 구글드라이브 세팅 진단 =="

# 1) 공유링크 다운로드 경로 (키 0개) — 항상 가능
echo "[1] 공유링크 다운로드(키 불필요): python3 -m shorts.drive_download <fileId> <저장경로>"
if [ "${1:-}" != "" ]; then
  echo "    → 실측 테스트: $1"
  mkdir -p /tmp/drive_test
  if python3 -m shorts.drive_download "$1" "/tmp/drive_test/out.bin"; then
    echo "    ✅ 공유링크 다운로드 OK (/tmp/drive_test/out.bin)"
  else
    echo "    🚫 실패 — 파일이 'anyone-with-link 뷰어' 공유인지 확인(인트레이 폴더는 이미 공유됨)"
  fi
fi

# 2) OAuth 풀연동(업로드+읽기+youtube) — secrets/gdrive.json 필요
echo "[2] OAuth 풀연동(업로드/읽기): $SEC"
if [ -f "$SEC" ]; then
  if python3 - "$SEC" <<'PY'
import json,sys
p=sys.argv[1]
d=json.load(open(p,encoding="utf-8"))
need={"client_id","client_secret"}
miss=need-set(d)
if miss:
    print(f"    🔶 {p} 있음 — 누락 필드 {sorted(miss)}"); sys.exit(2)
if "refresh_token" not in d:
    print(f"    🔶 {p} 있음(client_id/secret OK) — refresh_token 없음 → 'python3 -m shorts.gdrive auth' 로 채움"); sys.exit(3)
print("    ✅ gdrive.json 형식 유효(client_id/secret/refresh_token) — 업로드/읽기 가능")
PY
  then :; fi
else
  cat <<'EOF'
    ❌ 없음 → 노션 「📱 코드방 상태판 → 🔑 세션 연결 정보」의 gdrive JSON을 아래 경로로 저장:
       secrets/gdrive.json  (형식: {"client_id":"...apps.googleusercontent.com","client_secret":"...","refresh_token":"..."})
    저장 후 다시 이 스크립트 실행. refresh_token이 없으면: python3 -m shorts.gdrive auth
    ⚠️ secrets/ 는 gitignore — 절대 커밋/출력 금지.
EOF
fi

# 3) 파이프라인 진단으로 마무리
echo "[3] 전체 연결 진단:"
python3 -m pipeline check 2>/dev/null | grep -iE "드라이브|유튜브|일레븐|인덱스" || echo "    (pipeline check 생략/실패 — 수동으로 python3 -m pipeline check)"
echo "== 끝. 대부분의 코덱스 작업(코드·문서·기획·대본)은 Drive 없이도 바로 된다. =="
