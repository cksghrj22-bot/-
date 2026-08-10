#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""그림 중복 검사 — 파일 이름이 달라도 '똑같이 생겼으면' 중복이다.
왜(2026-08-09 형 지적: "영상 중복이 좀 있고"):
기존 repeat/dup 게이트는 파일명만 비교했다. 같은 촬영분에서 연달아 자른 컷들은
파일명이 달라도 앵글·구도·색이 거의 같아서, 보는 사람에겐 같은 화면이 반복되는 것으로 보인다.
여기서는 실제 픽셀로 지문을 떠서 비교한다.
"""
import subprocess, os, sys, json, glob, itertools

MAC="/Users/chanho/atnown-content-pipeline"
HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def real(p): return p.replace(MAC,HERE) if p else p
W,H=24,42                      # 지문 해상도 (구도만 남기고 디테일은 버린다)
SIM_LIMIT=0.86                 # 이 이상 닮았으면 같은 그림으로 본다

def fp(path, n=5):
    """클립 전체에서 n장을 뽑아 평균낸 저해상 흑백 지문."""
    out=subprocess.run(["ffmpeg","-v","error","-i",path,"-vf",
        "fps=%.3f,scale=%d:%d,format=gray"%(n/max(1.0,dur(path)),W,H),
        "-f","rawvideo","-"],capture_output=True).stdout
    N=W*H; cnt=len(out)//N
    if cnt==0: return None
    acc=[0]*N
    for i in range(cnt):
        c=out[i*N:(i+1)*N]
        for k in range(N): acc[k]+=c[k]
    return [v/cnt for v in acc]

def dur(p):
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p],
                     capture_output=True,text=True).stdout.strip()
    try: return float(r)
    except: return 6.0

def cos(a,b):
    if not a or not b: return 0.0
    ma=sum(a)/len(a); mb=sum(b)/len(b)
    da=[x-ma for x in a]; db=[x-mb for x in b]
    num=sum(x*y for x,y in zip(da,db))
    den=(sum(x*x for x in da)**0.5)*(sum(y*y for y in db)**0.5)
    return num/den if den else 0.0

def check(job_path, suggest=True):
    j=json.load(open(job_path,encoding="utf-8"))
    d=real(j.get("clips_dir",""))
    beats=j.get("beats",[])
    # 연속 구간은 한 장면으로 접는다 (이어보기는 중복이 아니다)
    scenes=[]
    for i,b in enumerate(beats):
        c=b.get("clip")
        if not c: continue
        if scenes and scenes[-1][1]==c: continue
        scenes.append((i,c))
    prints={}
    for _,c in scenes:
        p=os.path.join(d,c)
        if os.path.exists(p) and c not in prints: prints[c]=fp(p)
    hits=[]
    for (i1,c1),(i2,c2) in itertools.combinations(scenes,2):
        s=cos(prints.get(c1),prints.get(c2))
        if s>=SIM_LIMIT: hits.append((i1,c1,i2,c2,round(s,3)))
    out={"job":os.path.basename(job_path),"scenes":len(scenes),"hits":hits,"swap":{}}
    if hits and suggest:
        pool=[os.path.basename(x) for x in sorted(glob.glob(d+"/*.mov"))]
        used={c for _,c in scenes}
        cand={}
        for c in pool:
            if c in used: continue
            f=fp(os.path.join(d,c))
            if f: cand[c]=f
        for (i1,c1,i2,c2,s) in hits:
            best=None;bs=2.0
            for c,f in cand.items():
                worst=max(cos(f,prints[u]) for u in used if prints.get(u))
                if worst<bs: bs=worst;best=c
            if best and bs<SIM_LIMIT:
                out["swap"][str(i2)]={"from":c2,"to":best,"maxsim":round(bs,3)}
    return out

if __name__=="__main__":
    pats=sys.argv[1:] or [HERE+"/_jobs/_processing/JOB-*OK.json"]
    for pat in pats:
        for p in sorted(glob.glob(pat)):
            r=check(p)
            print("\n[%s] 장면 %d개"%(r["job"],r["scenes"]))
            if not r["hits"]: print("   그림 중복 없음"); continue
            for i1,c1,i2,c2,s in r["hits"]:
                print("   ✗ 비트%d %s ≈ 비트%d %s  닮음 %.3f"%(i1,c1,i2,c2,s))
            for k,v in r["swap"].items():
                print("   → 비트%s %s 를 %s 로 교체 권장 (최대닮음 %.3f)"%(k,v["from"],v["to"],v["maxsim"]))
