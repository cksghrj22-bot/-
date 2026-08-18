#!/usr/bin/env python3
"""성희룩북 — 드라이브 API로 직접 내려받기
   로컬 드라이브 마운트가 이 폴더 열람을 거부(Resource deadlock avoided)해서 API 경로로 간다."""
import json, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DST = ROOT / "_intray_무드보드_보이드태그" / "성희룩북"
DST.mkdir(parents=True, exist_ok=True)
EXT = {".jpg",".jpeg",".png",".heic",".webp",".gif",".tif",".tiff"}

def token():
    s = json.loads((ROOT/"secrets"/"gdrive.json").read_text())
    data = urllib.parse.urlencode({
        "client_id": s["client_id"], "client_secret": s["client_secret"],
        "refresh_token": s["refresh_token"], "grant_type": "refresh_token"}).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    return json.loads(urllib.request.urlopen(req, timeout=30).read())["access_token"]

def api(url, tk):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tk}"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())

tk = token()
q = urllib.parse.quote("name='성희룩북' and mimeType='application/vnd.google-apps.folder' and trashed=false")
res = api(f"https://www.googleapis.com/drive/v3/files?q={q}&fields=files(id,name)&pageSize=10", tk)
folders = res.get("files", [])
print("폴더 후보:", folders)
if not folders:
    raise SystemExit("⛔ 성희룩북 폴더를 API로 못 찾음")
fid = folders[0]["id"]

files, page = [], None
while True:
    q2 = urllib.parse.quote(f"'{fid}' in parents and trashed=false")
    u = (f"https://www.googleapis.com/drive/v3/files?q={q2}"
         f"&fields=nextPageToken,files(id,name,mimeType,size)&pageSize=200")
    if page: u += f"&pageToken={page}"
    r = api(u, tk)
    files += r.get("files", [])
    page = r.get("nextPageToken")
    if not page: break
print(f"폴더 내 파일 {len(files)}개")

ok = 0
for f in files:
    name, mt = f["name"], f.get("mimeType","")
    if mt.endswith(".folder"):
        print("  [하위폴더]", name); continue
    if Path(name).suffix.lower() not in EXT and not mt.startswith("image/"):
        print("  [건너뜀]", name, mt); continue
    out = DST / name
    try:
        req = urllib.request.Request(
            f"https://www.googleapis.com/drive/v3/files/{f['id']}?alt=media",
            headers={"Authorization": f"Bearer {tk}"})
        out.write_bytes(urllib.request.urlopen(req, timeout=180).read())
        ok += 1
        print(f"  ✅ {name}  ({out.stat().st_size//1024}KB)")
    except Exception as e:
        print(f"  ⛔ {name}  {e}")
print(f"\n내려받음 {ok}개  →  {DST}")
