#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""톤 정합 — 여러 소재를 한 게시물 안에서 같은 톤으로 맞춘다 (이 방 전용).

그레이딩(film_grade.py)은 '룩'을 건다. 이건 그 위에서 **장별 편차를 없앤다.**
맞추는 값 3개: 블랙포인트 · 밝기 · 따뜻함(R-B). 채도는 장면이 정하므로 건드리지 않는다.
  python3 rooms/낙타방/tone_match.py <입력들...> --out <폴더> [--black 23 --rb 7 --bright 105]
"""
import sys, pathlib, argparse
import numpy as np
from PIL import Image

def stats(a):
    r,g,b=a[...,0],a[...,1],a[...,2]
    lum=0.299*r+0.587*g+0.114*b
    mx,mn=a.max(2),a.min(2)
    sat=(np.where(mx>0,(mx-mn)/np.maximum(mx,1),0)*100).mean()
    return dict(black=np.percentile(lum,5), bright=lum.mean(),
                rb=(r-b).mean(), sat=sat, p95=np.percentile(lum,95))

def match(path, out, tb, trb, tbr):
    a=np.asarray(Image.open(path).convert("RGB")).astype(float)
    s=stats(a)
    # 1) 블랙포인트/밝기 — 선형 (lift, gain)
    gain=(tbr-tb)/max(s["bright"]-s["black"],1e-6)
    a=(a-s["black"])*gain+tb
    # 2) 따뜻함 — R/B 를 반대로 밀어 R-B 만 조정 (밝기 보존)
    d=(trb-stats(a)["rb"])/2.0
    a[...,0]+=d; a[...,2]-=d
    a=np.clip(a,0,255).astype(np.uint8)
    Image.fromarray(a).save(out, quality=95)
    return s, stats(a.astype(float))

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("src",nargs="+"); ap.add_argument("--out",required=True)
    ap.add_argument("--black",type=float,default=23.0); ap.add_argument("--rb",type=float,default=7.0)
    ap.add_argument("--bright",type=float,default=105.0)
    x=ap.parse_args(); od=pathlib.Path(x.out); od.mkdir(parents=True,exist_ok=True)
    for p in x.src:
        p=pathlib.Path(p); o=od/p.name
        b,a=match(p,o,x.black,x.rb,x.bright)
        print(f"{p.name:34s} 블랙 {b['black']:5.1f}->{a['black']:5.1f} · 밝기 {b['bright']:5.1f}->{a['bright']:5.1f} · RB {b['rb']:+5.1f}->{a['rb']:+5.1f} · 채도 {b['sat']:.1f}->{a['sat']:.1f}")
