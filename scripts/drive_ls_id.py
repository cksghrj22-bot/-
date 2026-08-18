#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""폴더 ID로 드라이브 목록(하위폴더 포함). 샌드박스 밖 실행기 전용.
사용: {"cmd":"python_script","args":["drive_ls_id.py","<폴더ID>"]}"""
import json, sys, urllib.request, urllib.parse
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
def token():
    c = json.loads((ROOT/"secrets/gdrive.json").read_text())
    d = urllib.parse.urlencode({"client_id":c["client_id"],"client_secret":c["client_secret"],
        "refresh_token":c["refresh_token"],"grant_type":"refresh_token"}).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(
        "https://oauth2.googleapis.com/token",data=d,method="POST"),timeout=60).read())["access_token"]
def q(query,tok):
    out,pt=[],None
    while True:
        p={"q":query,"fields":"nextPageToken,files(id,name,mimeType,size,modifiedTime)","pageSize":"1000",
           "orderBy":"name","supportsAllDrives":"true","includeItemsFromAllDrives":"true"}
        if pt: p["pageToken"]=pt
        r=json.loads(urllib.request.urlopen(urllib.request.Request(
            "https://www.googleapis.com/drive/v3/files?"+urllib.parse.urlencode(p),
            headers={"Authorization":"Bearer "+tok}),timeout=120).read())
        out+=r.get("files",[]); pt=r.get("nextPageToken")
        if not pt: return out
def walk(fid,tok,pre="",depth=0):
    tot_n=tot_b=0
    for f in q("'%s' in parents and trashed=false"%fid,tok):
        if f["mimeType"].endswith("folder"):
            print("%s📁 %s"%("  "*depth,f["name"]),flush=True)
            if depth<2:
                n,b=walk(f["id"],tok,pre,depth+1); tot_n+=n; tot_b+=b
        elif f["name"].lower().endswith((".mov",".mp4",".m4v")):
            mb=int(f.get("size",0))/1048576
            print("%s   %-46s %8.1fMB  %s"%("  "*depth,f["name"][:44],mb,f["id"]),flush=True)
            tot_n+=1; tot_b+=int(f.get("size",0))
    return tot_n,tot_b
tok=token()
n,b=walk(sys.argv[1],tok)
print("\n영상 %d개 · %.1fGB"%(n,b/1073741824))
