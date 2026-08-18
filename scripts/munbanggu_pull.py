#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""영상문방구(1S2Kqny...) 재고 목록 + 중소형 파일 수거 → _clips_pool/문방구/

⚠️ 박제 규칙(차노 2026-08-06): 문방구 소스는 **촬영 시기가 달라 톤이 어긋난다.**
   렌더에 넣기 전에 **쓸 클립 스샷을 형한테 띄우고 yes/no** 를 받는다. 자동 톤보정 금지.
사용: {"cmd":"python_script","args":["munbanggu_pull.py","<최대MB>"]}
"""
import json, sys, urllib.request, urllib.parse
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
FID  = "1S2KqnyOUqjxxqsLeJ5_feZKcYQsOcaV8"
OUT  = ROOT / "_clips_pool/문방구"
IDX  = ROOT / "_out/shorts/_문방구_재고.json"
MAXMB = float(sys.argv[1]) if len(sys.argv) > 1 else 150.0

def token():
    c = json.loads((ROOT/"secrets/gdrive.json").read_text())
    d = urllib.parse.urlencode({"client_id":c["client_id"],"client_secret":c["client_secret"],
        "refresh_token":c["refresh_token"],"grant_type":"refresh_token"}).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(
        "https://oauth2.googleapis.com/token",data=d,method="POST"),timeout=60).read())["access_token"]

def q(query,tok):
    out,pt=[],None
    while True:
        p={"q":query,"fields":"nextPageToken,files(id,name,mimeType,size)","pageSize":"1000",
           "supportsAllDrives":"true","includeItemsFromAllDrives":"true"}
        if pt: p["pageToken"]=pt
        r=json.loads(urllib.request.urlopen(urllib.request.Request(
            "https://www.googleapis.com/drive/v3/files?"+urllib.parse.urlencode(p),
            headers={"Authorization":"Bearer "+tok}),timeout=120).read())
        out+=r.get("files",[]); pt=r.get("nextPageToken")
        if not pt: return out

def walk(fid,tok,path="",depth=0):
    items=[]
    for f in q("'%s' in parents and trashed=false"%fid,tok):
        if f["mimeType"].endswith("folder"):
            if depth<3: items+=walk(f["id"],tok,path+"/"+f["name"],depth+1)
        elif f["name"].lower().endswith((".mov",".mp4",".m4v")):
            f["path"]=path; items.append(f)
    return items

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tok=token()
    items=walk(FID,tok)
    items.sort(key=lambda f:int(f.get("size",0)))
    IDX.write_text(json.dumps([{k:f.get(k) for k in ("id","name","size","path")} for f in items],
                              ensure_ascii=False,indent=1))
    tot=sum(int(f.get("size",0)) for f in items)
    print("문방구 영상 %d개 · %.1fGB"%(len(items),tot/1073741824),flush=True)
    small=[f for f in items if int(f.get("size",0))<=MAXMB*1048576]
    print("%.0fMB 이하 %d개 수거 시작"%(MAXMB,len(small)),flush=True)
    ok=0
    for f in small:
        dest=OUT/f["name"].replace("/","_")
        want=int(f.get("size",0))
        if dest.exists() and dest.stat().st_size==want: ok+=1; continue
        try:
            url="https://www.googleapis.com/drive/v3/files/%s?alt=media&supportsAllDrives=true"%f["id"]
            tmp=dest.with_suffix(dest.suffix+".part"); got=0
            with urllib.request.urlopen(urllib.request.Request(url,
                    headers={"Authorization":"Bearer "+tok}),timeout=600) as r, open(tmp,"wb") as fh:
                while True:
                    b=r.read(1<<20)
                    if not b: break
                    fh.write(b); got+=len(b)
            tmp.rename(dest); ok+=1
            print("✅ %-46s %7.1fMB  %s"%(f["name"][:44],got/1048576,f["path"]),flush=True)
        except Exception as e:
            print("⛔ %s — %s"%(f["name"],e),flush=True)
    print("\n수거 완료 %d개 · 풀 %d개"%(ok,len(list(OUT.iterdir()))),flush=True)
    return 0
sys.exit(main())
