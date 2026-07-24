import subprocess, json
from pathlib import Path

SP = Path("/tmp/claude-0/-home-user--/0fb0e5b8-eaea-542a-a0d3-be17b390f310/scratchpad")
D = SP/"miyong3"
FONT = "NanumSquareRound"
T = 0.30  # 크로스페이드

def alloc(pool, n, fixed=None, gap=None):
    """pool=[(key,[offsets]),...] → n개 세그에 배정. 최근 gap개 안에서 같은 클립 재등장 방지 + 등장마다 다른 offset(다른 순간). fixed={idx:(key,off)}."""
    fixed = fixed or {}
    oi = {k: 0 for k, _ in pool}
    keys = [k for k, _ in pool]
    offs = {k: o for k, o in pool}
    if gap is None:
        gap = min(len(keys) - 1, 4)
    seq = []
    pi = 0
    for i in range(n):
        if i in fixed:
            seq.append(fixed[i]); continue
        recent = {s[0] for s in seq[-gap:]} if gap > 0 else set()
        chosen = None
        for _ in range(len(keys) * 3):
            k = keys[pi % len(keys)]; pi += 1
            if k not in recent:
                chosen = k; break
        if chosen is None:  # 클립 부족 → 가장 오래전 것
            chosen = keys[pi % len(keys)]; pi += 1
        o = offs[chosen][oi[chosen] % len(offs[chosen])]; oi[chosen] += 1
        seq.append((chosen, o))
    return seq

def wrap(t):
    if len(t) <= 15 or " " not in t:
        return t
    mid = len(t)//2; best = None
    for i, ch in enumerate(t):
        if ch == " " and (best is None or abs(i-mid) < abs(best-mid)):
            best = i
    return t[:best]+"\\N"+t[best+1:] if best else t

def ts(x):
    h = int(x//3600); m = int((x % 3600)//60); s = x % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def textcard(text, dur, out):
    """검정 배경 + 대형 중앙 텍스트 = 자막-싱크 새 장면(중간 훅). 클립 부족/반복 회피용. (2026-07-24 이찬호 지시)"""
    head = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
            "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: big,Pretendard,76,&H00FFFFFF,&H00101010,&H00000000,1,1,3,0,5,110,110,0,1\n\n"
            "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    ev = f"Dialogue: 0,{ts(0)},{ts(dur)},big,,0,0,0,,{{\\fad(150,120)}}{text}"
    af = D/f"_tc_{abs(hash(text))%99999}.ass"; af.write_text(head+ev+"\n", encoding="utf-8")
    subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi","-i",f"color=c=black:s=1080x1920:r=30:d={dur:.3f}",
        "-vf",f"noise=alls=6:allf=t,ass={af}:fontsdir=/root/.fonts,format=yuv420p","-an",
        "-c:v","libx264","-preset","fast","-crf","20",str(out)],check=True)

def render(name, clips, plan, bgm, out_name, outro_png=None, bgm_lufs=-24, mono=False, en=None):
    """clips={key:path}, plan=[(key,offset),...] 세그별, len(plan)==len(lines). mono=True → 흑백(마인드편).
    en=[영어줄,...] 주면 한글자막 아래 영어자막 동반(해외 시청자·저장률↑, 2026-07-24 이찬호 "영어자막 왜 안해"). len(en)==len(lines)."""
    meta = json.loads((D/"tts_meta.json").read_text(encoding="utf-8"))[name]
    lines = meta["lines"]; spans = meta["spans"]; total = meta["total"]; nar = meta["nar"]
    assert len(plan) == len(lines), f"{name}: plan {len(plan)} != lines {len(lines)}"
    starts = [s[0] for s in spans]
    durs = [(starts[i+1]-starts[i]) if i < len(lines)-1 else (total-starts[i]) for i in range(len(lines))]
    durs = [max(d, 0.5) for d in durs]
    SEG = D/f"{name}_seg"; SEG.mkdir(exist_ok=True)
    segfiles = []
    for i, item in enumerate(plan):
        sf = SEG/f"s{i:02d}.mp4"
        if item[0] == "TXT":   # 텍스트 카드 세그(검정+대형 중앙). item=("TXT", 표시문구 or None)
            big = item[1] if len(item) > 1 and item[1] else lines[i]
            textcard(big, durs[i]+T, sf)
            segfiles.append(str(sf)); continue
        k, o = item[0], item[1]
        xf = item[2] if len(item) > 2 else ""   # 세그별 미세변형: "h"=좌우반전, "z"=줌 (같은 클립 재등장 차별화)
        pre = "scale=-2:1920,crop=1080:1920,fps=30"
        if "z" in xf: pre = "scale=-2:2110,crop=1080:1920,fps=30"  # 줌인(≈10%)
        if "h" in xf: pre += ",hflip"
        eq = "eq=saturation=0:contrast=1.05" if mono else "eq=saturation=1.06:contrast=1.02"  # mono=흑백(마인드편)
        vf = pre + "," + eq + ",format=yuv420p"
        # -stream_loop -1: 짧은 클립도 세그 길이(dur+T)를 꽉 채우게 루프 → xfade truncate/프리즈 방지 (2026-07-24 펌 7.5초 잘림 사고)
        subprocess.run(["ffmpeg","-v","error","-y","-stream_loop","-1","-ss",str(o),"-i",clips[k],"-t",f"{durs[i]+T:.3f}",
            "-vf",vf,"-an",
            "-c:v","libx264","-preset","fast","-crf","20",str(sf)],check=True)
        segfiles.append(str(sf))
    outro_png = outro_png or str(SP/"outro_sns.png")
    outro = SEG/"outro.mp4"
    subprocess.run(["ffmpeg","-v","error","-y","-loop","1","-i",outro_png,"-t","2.6",
        "-vf","fps=30,format=yuv420p,fade=t=in:st=0:d=0.3,fade=t=out:st=2.2:d=0.4","-an",
        "-c:v","libx264","-preset","fast","-crf","20",str(outro)],check=True)
    inputs = []
    for s in segfiles:
        inputs += ["-i", s]
    inputs += ["-i", str(outro)]
    fc = []; prev = "[0:v]"; acc = 0.0
    for i in range(1, len(segfiles)):
        acc += durs[i-1]
        fc.append(f"{prev}[{i}:v]xfade=transition=fade:duration={T}:offset={acc:.3f}[x{i}]"); prev = f"[x{i}]"
    acc += durs[-1]
    oidx = len(segfiles)
    fc.append(f"{prev}[{oidx}:v]xfade=transition=fade:duration={T}:offset={acc:.3f}[vbody]")
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: cap,{FONT},58,&H00FFFFFF,&H00101010,&H00000000,1,1,5,1,2,70,70,210,1
Style: eng,Pretendard,36,&H00D8D8D8,&H00101010,&H00000000,0,1,3,1,2,80,80,150,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    is_txt = [(plan[i][0] == "TXT") for i in range(len(lines))]
    # TXT 세그는 가운데 대형 한글카드가 이미 있음 → 하단 한글자막 생략(중복 방지). 영어는 카드 아래 유지(해외시청자).
    ev = [f"Dialogue: 0,{ts(starts[i])},{ts(starts[i+1] if i<len(lines)-1 else total)},cap,,0,0,0,,{wrap(t)}"
          for i, t in enumerate(lines) if not is_txt[i]]
    if en:
        assert len(en) == len(lines), f"{name}: en {len(en)} != lines {len(lines)}"
        ev += [f"Dialogue: 0,{ts(starts[i])},{ts(starts[i+1] if i<len(lines)-1 else total)},eng,,0,0,0,,{t}"
               for i, t in enumerate(en)]
    sb = D/f"{name}_subs.ass"; sb.write_text(head+"\n".join(ev)+"\n", encoding="utf-8")
    fc.append(f"[vbody]ass={sb}[v]")
    VTOT = total + 2.6 - T
    naidx = len(segfiles)+1; bgidx = len(segfiles)+2
    inputs += ["-i", str(nar), "-stream_loop","-1","-i", bgm]
    # 나레이션·BGM 따로 정규화 후 믹스 → BGM이 확실히 들리게. (2026-07-24 "BGM 안 나옴" 사고: 최종 loudnorm이 나레이션에 맞춰 BGM을 깔아뭉갬 → 제거)
    # 나레이션 speechnorm(라우드), BGM loudnorm -24(나레이션 밑 ~9dB, 또렷이 들림), amix normalize=0(반토막 방지), alimiter로 클립 방지.
    # duration=longest + BGM stream_loop(무한) → BGM이 -t(VTOT) 컷까지 끝까지 깔림. 나레이션 끝 여백 유무와 무관.
    # (2026-07-24 피쉬 나레이션은 끝 여백이 없어 amix=first가 나레이션 콘텐츠 끝에서 잘림 → 아웃트로 무음 사고)
    # ⚠️ BGM 파일은 앞뒤 무음이 없어야 함(루프 경계 침묵 방지) — 무음 있으면 미리 트림해서 넘길 것.
    fc.append(f"[{naidx}:a]apad,speechnorm=e=12.5:r=0.0006[na];[{bgidx}:a]loudnorm=I={bgm_lufs}:TP=-3[bg];[na][bg]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0,alimiter=limit=0.97[a]")
    out = D/out_name
    cmd = ["ffmpeg","-y","-loglevel","error"]+inputs+["-filter_complex",";".join(fc),
           "-map","[v]","-map","[a]","-t",f"{VTOT:.3f}","-c:v","libx264","-preset","medium","-crf","20","-c:a","aac","-b:a","192k",str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    dur = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(out)],capture_output=True,text=True).stdout.strip()
    print(f"[{name}] rc={r.returncode} {out.name} {dur}s (나레이션 {total:.1f}+아웃트로)")
    if r.returncode:
        print(r.stderr[-800:])
    return out
