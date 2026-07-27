"""모션그래픽 설명 클립 생성기 (2026-07-27 이찬호 박제 — "설명이 말로 어려우면 이걸 섞자").

용도: 말로 설명하기 어렵거나 남이 알아듣기 힘든 개념을 **움직이는 도식 + 키네틱 자막 +
차노 나레이션**으로 보여주는 짧은 설명 클립. 실사 쇼츠에 인서트로 섞거나 단독으로 쓴다.
외부 도구(애프터이펙트·캔바) 없이 순수 코드(HTML canvas → playwright 프레임 → ffmpeg)로 만든다.

핵심 원리: 캔버스에 `renderFrame(t)`를 시간 t의 함수로 그려 프레임을 뽑는다.
씬(scene)은 SCENES 디스패처로 확장한다. 지금 built-in:
  - face_morph : 슈퍼타원 지수 n(각짐 8 → 둥긂 2)로 얼굴형을 연속 변형. "얼굴형=특징" 계열.

스펙(dict)으로 구동:
  spec = {
    "dur": 10.0, "fps": 30,
    "scene": {"name": "face_morph", ...파라미터},
    "titles":   [[start, end, "상단 타이틀"], ...],   # 푸어스토리 노랑
    "captions": [[start, end, "하단 키네틱 자막"], ...], # 검은박스 흰글씨(브랜드 규격)
    "signature": "— 차노",   # 우하단 나눔펜(옵션)
    "narration": "나레이션 대본(06 라임 부호). 없으면 무성.",
  }

CLI:
  python3 -m shorts.motiongfx out.mp4 --spec face_demo   # 데모(각진→둥근 얼굴형)
  python3 -m shorts.motiongfx out.mp4 --json spec.json   # 커스텀 스펙

⚠️ 산출물은 '시안(발행본 아님)'. 발행은 이찬호 승인 후. 브랜드 폰트·색은 제작규격_정본 준수.
"""
from __future__ import annotations
import json, subprocess, tempfile
from pathlib import Path

W, H = 1080, 1920
FONT_DIR = "/root/.fonts"  # PoorStory / GamjaFlower / NanumPen / Kyobo

# 브랜드 색 (제작규격 계열)
COL = {
    "title": "#F4C842",   # 푸어스토리 노랑
    "gold":  "#F4C842",
    "green": "#9ff0bd",   # '특징'(긍정 전환) 색
    "red":   "#e85a4a",   # '문제/통념' 색
    "cap_fg": "#ffffff",
    "sign":  "#cfcabd",
}


def _demo_spec() -> dict:
    """각진→둥근 얼굴형 = 특징 (10초 데모). CLAUDE.md 얼굴형 재정의와 연결."""
    return {
        "dur": 10.0, "fps": 30,
        "scene": {"name": "face_morph", "n_from": 8.0, "n_to": 2.0,
                   "morph": [3.8, 6.3], "problem": [2.0, 3.6], "wrap": [3.8, 6.2]},
        "titles": [[0.3, 3.7, "각진 얼굴형?"], [3.9, 8.9, "곡선으로 감싸면"]],
        "captions": [
            [0.4, 2.0, "각진 얼굴, 고민이세요?"],
            [2.1, 3.6, "각진 건 '문제'가 아니에요"],
            [3.9, 6.2, "곡선으로 감싸면"],
            [6.4, 8.3, "'특징'이 드러나요"],
            [8.5, 10.0, "안 어울리는 게 아니라, 특징이 드러나는 것"],
        ],
        "signature": "— 차노",
        "narration": ("각진 얼굴, 고민이세요? 각진 건 문제가 아니에요. "
                       "곡선으로 감싸면, 특징이 드러나요. "
                       "안 어울리는 게 아니라, 특징이 드러나는 것."),
    }


def _build_html(spec: dict) -> str:
    """스펙을 canvas 렌더러가 읽도록 window.SPEC로 주입한 HTML."""
    spec_js = json.dumps(spec, ensure_ascii=False)
    col_js = json.dumps(COL)
    return (
        "<!doctype html><html><head><meta charset=utf-8><style>"
        f"@font-face{{font-family:Poor;src:url('file://{FONT_DIR}/PoorStory-Regular.ttf');}}"
        f"@font-face{{font-family:Gamja;src:url('file://{FONT_DIR}/GamjaFlower-Regular.ttf');}}"
        f"@font-face{{font-family:Pen;src:url('file://{FONT_DIR}/NanumPenScript-Regular.ttf');}}"
        f"@font-face{{font-family:Kyobo;src:url('file://{FONT_DIR}/KyoboHandwriting2019.ttf');}}"
        "html,body{margin:0;background:#000}canvas{display:block}</style></head><body>"
        f"<canvas id=c width={W} height={H}></canvas><script>"
        f"const SPEC={spec_js},COL={col_js},W={W},H={H};"
        r"""
const cv=document.getElementById('c'),x=cv.getContext('2d');
const clamp=(a,b,v)=>Math.max(a,Math.min(b,v)), lerp=(a,b,t)=>a+(b-a)*t;
const ease=t=>t<.5?2*t*t:1-Math.pow(-2*t+2,2)/2;
const seg=(t,a,b)=>clamp(0,1,(t-a)/(b-a));
function bg(){const g=x.createLinearGradient(0,0,0,H);g.addColorStop(0,'#0e1417');g.addColorStop(.55,'#131b1f');g.addColorStop(1,'#0b0f11');x.fillStyle=g;x.fillRect(0,0,W,H);}
function superPath(cx,cy,a,b,n){x.beginPath();const S=160;for(let i=0;i<=S;i++){const th=i/S*2*Math.PI,ct=Math.cos(th),st=Math.sin(th);const px=cx+a*Math.sign(ct)*Math.pow(Math.abs(ct),2/n),py=cy+b*Math.sign(st)*Math.pow(Math.abs(st),2/n);i?x.lineTo(px,py):x.moveTo(px,py);}x.closePath();}
// ---- 씬: face_morph ----
function sceneFaceMorph(t,p){
  const cx=540,cy=830,a=250,b=330;
  const morph=ease(seg(t,p.morph[0],p.morph[1])), n=lerp(p.n_from,p.n_to,morph);
  const intro=ease(seg(t,0.15,1.6));
  const red=seg(t,p.problem[0],p.problem[0]+0.4)*(1-seg(t,p.problem[1]-0.4,p.problem[1]));
  const feat=ease(seg(t,p.morph[1],p.morph[1]+0.7));
  x.save();x.translate(cx,cy);x.scale(lerp(.86,1,intro),lerp(.86,1,intro));x.translate(-cx,-cy);x.globalAlpha=intro;
  if(feat>0){const q=0.5+0.5*Math.sin(t*4);x.shadowColor="rgba(120,230,170,"+(.55*feat*(0.6+0.4*q))+")";x.shadowBlur=60;}
  superPath(cx,cy,a,b,n);
  x.fillStyle=feat>0?"rgba(120,230,170,"+(0.10+0.05*feat)+")":"rgba(244,200,66,0.08)";x.fill();
  x.lineWidth=10;x.lineJoin="round";
  x.strokeStyle=red>0?"rgba(232,90,74,"+red+")":(feat>0?"rgb("+Math.round(lerp(244,120,feat))+","+Math.round(lerp(200,230,feat))+","+Math.round(lerp(66,170,feat))+")":COL.gold);
  x.stroke();x.shadowBlur=0;
  x.fillStyle=x.strokeStyle;x.beginPath();x.arc(cx-90,cy-30,15,0,7);x.arc(cx+90,cy-30,15,0,7);x.fill();
  x.beginPath();x.lineWidth=9;x.moveTo(cx-70,cy+110);x.quadraticCurveTo(cx,cy+140,cx+70,cy+110);x.stroke();
  x.restore();
  // 곡선 감싸기
  if(t>p.wrap[0]-0.1&&t<p.wrap[1]+0.4){const w=seg(t,p.wrap[0],p.wrap[1]);x.save();x.globalAlpha=0.9*(1-seg(t,p.wrap[1],p.wrap[1]+0.4));x.strokeStyle=COL.green;x.lineWidth=7;x.lineCap="round";for(const s of[-1,1]){x.beginPath();const st=Math.PI*0.15,en=st+Math.PI*0.95*w;for(let i=0;i<=60;i++){const th=st+(en-st)*i/60;const px=cx+s*(a+58)*Math.cos(th),py=cy+(b+40)*Math.sin(th)-10;i?x.lineTo(px,py):x.moveTo(px,py);}x.stroke();}x.restore();}
  // 문제 ✕
  const stamp=seg(t,p.problem[0],p.problem[0]+0.25)*(1-seg(t,p.problem[1]-0.4,p.problem[1]));
  if(stamp>0){x.save();x.globalAlpha=stamp;x.translate(cx+150,cy-210);x.rotate(-.18);x.strokeStyle=COL.red;x.lineWidth=16;x.lineCap="round";const s=70;x.beginPath();x.moveTo(-s,-s);x.lineTo(s,s);x.moveTo(s,-s);x.lineTo(-s,s);x.stroke();x.restore();}
  // '특징' 라벨
  if(feat>0){x.save();x.globalAlpha=feat;x.font="96px Kyobo";x.textAlign="center";x.fillStyle=COL.green;x.fillText("특징",cx+330,cy-260);x.restore();}
}
const SCENES={face_morph:sceneFaceMorph};
function title(t){for(const[s,e,txt]of(SPEC.titles||[])){if(t>=s&&t<e){const a=ease(seg(t,s,s+0.9))*(1-seg(t,e-0.4,e));if(a<=0)continue;x.save();x.globalAlpha=a;x.font="88px Poor";x.textAlign="center";x.textBaseline="middle";x.fillStyle=COL.title;x.fillText(txt,W/2,300);x.restore();}}}
function caption(t){for(const[s,e,txt]of(SPEC.captions||[])){if(t>=s&&t<e){const inn=seg(t,s,s+0.3),out=1-seg(t,e-0.35,e),a=Math.min(inn,out);if(a<=0)continue;const rise=(1-inn)*24;x.save();x.globalAlpha=a;x.font="64px Gamja";x.textAlign="center";x.textBaseline="middle";const m=x.measureText(txt).width,pad=44,bw=m+pad*2,bh=110,cyy=1560-rise;x.fillStyle="rgba(0,0,0,.82)";x.beginPath();x.roundRect((W-bw)/2,cyy-bh/2,bw,bh,18);x.fill();x.fillStyle=COL.cap_fg;x.fillText(txt,W/2,cyy+4);x.restore();}}}
function signature(t){if(!SPEC.signature)return;const s=(SPEC.dur||10)-1.2;if(t>s){x.save();x.globalAlpha=ease(seg(t,s,s+0.5));x.font="66px Pen";x.textAlign="right";x.fillStyle=COL.sign;x.fillText(SPEC.signature,W-70,1700);x.restore();}}
window.renderFrame=function(t){bg();const sc=SCENES[SPEC.scene.name];if(sc)sc(t,SPEC.scene);title(t);caption(t);signature(t);};
window.__ready=true;
</script></body></html>"""
    )


def render_frames(spec: dict, frames_dir: Path) -> int:
    """스펙대로 canvas 프레임을 PNG로 뽑는다. 프레임 수 반환."""
    from playwright.sync_api import sync_playwright
    fps = int(spec.get("fps", 30)); dur = float(spec.get("dur", 10.0))
    n = int(fps * dur)
    frames_dir.mkdir(parents=True, exist_ok=True)
    hp = frames_dir / "_scene.html"
    hp.write_text(_build_html(spec), encoding="utf-8")
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        pg.goto(hp.resolve().as_uri())
        pg.wait_for_function("window.__ready===true", timeout=8000)
        try:
            pg.evaluate("document.fonts.ready")
        except Exception:
            pass
        pg.wait_for_timeout(700)
        for i in range(n):
            pg.evaluate(f"renderFrame({i/fps})")
            pg.screenshot(path=str(frames_dir / f"f{i:04d}.png"),
                          clip={"x": 0, "y": 0, "width": W, "height": H})
        b.close()
    return n


def render(spec: dict, out_mp4: str, creds: dict | None = None) -> str:
    """스펙 → 완성 mp4 (나레이션 있으면 합성). 산출 경로 반환.

    creds: 일레븐랩스 자격(없으면 spec['narration'] 있어도 무성으로 폴백).
    """
    out = Path(out_mp4)
    fps = int(spec.get("fps", 30))
    with tempfile.TemporaryDirectory() as td:
        fdir = Path(td) / "frames"
        render_frames(spec, fdir)
        silent = Path(td) / "silent.mp4"
        subprocess.run(["ffmpeg", "-y", "-framerate", str(fps), "-i", str(fdir / "f%04d.png"),
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                        "-movflags", "+faststart", str(silent)], check=True, capture_output=True)
        narr_text = spec.get("narration")
        if narr_text and creds:
            from shorts import tts
            narr = Path(td) / "narr.mp3"
            tts.synthesize(narr_text, creds, narr)
            subprocess.run(["ffmpeg", "-y", "-i", str(silent), "-i", str(narr),
                            "-filter_complex",
                            "[0:v]tpad=stop_mode=clone:stop_duration=0.6[v];"
                            "[1:a]adelay=320|320,loudnorm=I=-16:TP=-1.5:LRA=11[a]",
                            "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                            "-crf", "18", "-c:a", "aac", "-b:a", "192k",
                            "-movflags", "+faststart", str(out)], check=True, capture_output=True)
        else:
            subprocess.run(["ffmpeg", "-y", "-i", str(silent), "-c", "copy", str(out)],
                           check=True, capture_output=True)
    return str(out)


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="모션그래픽 설명 클립 생성기")
    ap.add_argument("out", help="산출 mp4 경로")
    ap.add_argument("--spec", choices=["face_demo"], help="내장 데모 스펙")
    ap.add_argument("--json", help="커스텀 스펙 JSON 파일")
    ap.add_argument("--elevenlabs", default="secrets/elevenlabs.json", help="TTS 자격(나레이션용)")
    ap.add_argument("--silent", action="store_true", help="나레이션 없이 무성으로")
    a = ap.parse_args(argv)
    if a.json:
        spec = json.loads(Path(a.json).read_text(encoding="utf-8"))
    else:
        spec = _demo_spec()
    creds = None
    if not a.silent and spec.get("narration"):
        try:
            from shorts import tts
            creds = tts.load_credentials(a.elevenlabs)
        except Exception as e:
            print(f"[나레이션 생략] TTS 자격 로드 실패: {e}")
    out = render(spec, a.out, creds)
    print("VIDEO", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
