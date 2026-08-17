#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_from_job.py — 턴키 렌더 하니스 (drawtext 비의존 · PIL 오버레이 · 연속 TTS판)
변경점(v2): TTS를 비트마다 따로 뽑아 이어붙이던 방식 → 전체 대본을 "한 번에" 읽는
연속 TTS(with-timestamps)로 전환. 단어 타이밍으로 비트별 자막 구간을 맞춰 뚝뚝 끊김 제거.
BGM 볼륨 0.08 → 0.22 (옵션 A) 상향.
  python3 render_from_job.py job.json
"""
import time
import os, sys, json, base64, subprocess, urllib.request, urllib.error, re, hashlib, shutil

FPS=30
def _dbgpath(): return os.path.expanduser("~/atnown-content-pipeline/_jobs/_debug.log")
def _dl(m):
    try:
        with open(_dbgpath(),"a") as f:
            f.write(m+"\n")
    except: pass

def clen(f):
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nk=1:nw=1",f],capture_output=True,text=True)
    try: return float(r.stdout.strip())
    except: return 0.0

def resolve_font(job):
    fc=[job.get("font",""),
        "~/atnown-content-pipeline/remotion/public/Kyobo.otf",
        "~/atnown-repo/remotion/public/Kyobo.otf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumBrush.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]
    for f in fc:
        p=os.path.expanduser(f or "")
        if p and os.path.exists(p): return p
    return "/usr/share/fonts/truetype/nanum/NanumBrush.ttf"

def get_key(job):
    for ev in ("ELEVEN_KEY","ELEVENLABS_API_KEY","ELEVEN_API_KEY"):
        if os.environ.get(ev): return os.environ[ev].strip()
    for c in [job.get("eleven_key_file",""),"~/.config/creator-os/elevenlabs.env",
              "~/atnown-content-pipeline/secrets/eleven_key.txt","~/atnown-repo/secrets/eleven_key.txt","/tmp/_tts/key.txt"]:
        p=os.path.expanduser(c or "")
        if p and os.path.exists(p):
            t=open(p).read()
            if p.endswith(".json"):
                try:
                    data=json.loads(t)
                    if data.get("api_key"): return data["api_key"].strip()
                    if data.get("key"): return data["key"].strip()
                except Exception:
                    pass
            for line in t.splitlines():
                if "=" in line and "KEY" in line.upper(): return line.split("=",1)[1].strip().strip('"').strip("'")
            if t.strip(): return t.strip()
    raise RuntimeError("ElevenLabs 키 없음")

CAP_SYNC=float(os.environ.get("CAP_SYNC","0.140"))   # 최종 믹스의 140ms 보이스 리드와 같은 기준으로 자막 시작을 맞춘다.
# B방 STT 게이트 정본: 완성본에서 자막 시작과 발화 시작 평균오차 0.10s 이하.
# 오디오는 아래 Stage C에서 voice.mp3에 140ms adelay를 걸어 최종 믹스된다. 자막도 같은
# 기본 오프셋을 써야 완성본 기준 cap-speech가 0에 모인다. 환경변수 CAP_SYNC로 덮어쓸 수 있다.
VOICE_SETTINGS={"stability":0.42,"similarity_boost":0.85,"style":0.15,"use_speaker_boost":True,"speed":1.12}
TTS_MODEL_ID="eleven_multilingual_v2"
TTS_MIN_BYTES=1000
TTS_CACHE_DIR=os.path.expanduser("~/atnown-content-pipeline/_tts_cache")
TTS_STOP_MARKER=os.path.expanduser("~/atnown-content-pipeline/_jobs/TTS_QUOTA_EXHAUSTED.stop")
_FW_MODEL_CACHE={}

class TTSQuotaExhausted(RuntimeError):
    pass

def _json_canon(x):
    return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))

def _looks_quota_exhausted(status, body):
    return int(status)==401 and "quota_exceeded" in (body or "")

def _response_status(resp):
    return int(getattr(resp,"status",None) or (resp.getcode() if hasattr(resp,"getcode") else 200))

def _mark_tts_quota_exhausted(detail):
    os.makedirs(os.path.dirname(TTS_STOP_MARKER),exist_ok=True)
    msg="%s TTS_QUOTA_EXHAUSTED %s\n"%(time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),detail)
    try:
        with open(TTS_STOP_MARKER,"a",encoding="utf-8") as f:
            f.write(msg)
    except Exception: pass
    _dl("TTS_QUOTA_EXHAUSTED "+detail)

def eleven_config(job, vid):
    cfg={"api_key":"","voice_id":vid,"model_id":job.get("model_id") or job.get("tts_model_id") or TTS_MODEL_ID,
         "voice_settings":dict(VOICE_SETTINGS)}
    candidates=[job.get("eleven_json",""),job.get("elevenlabs_json",""),
                job.get("eleven_key_file","") if str(job.get("eleven_key_file","")).endswith(".json") else "",
                "~/atnown-content-pipeline/secrets/elevenlabs.json",
                "~/atnown-repo/secrets/elevenlabs.json"]
    for c in candidates:
        p=os.path.expanduser(c or "")
        if p and os.path.exists(p):
            try:
                data=json.load(open(p,encoding="utf-8"))
                cfg["api_key"]=data.get("api_key") or data.get("key") or cfg["api_key"]
                cfg["voice_id"]=job.get("voice_id") or data.get("voice_id") or cfg["voice_id"]
                cfg["model_id"]=job.get("model_id") or job.get("tts_model_id") or data.get("model_id") or cfg["model_id"]
                cfg["voice_settings"].update(data.get("voice_settings") or {})
                if data.get("speed") is not None: cfg["voice_settings"]["speed"]=data.get("speed")
                break
            except Exception as e:
                _dl("ELEVEN_JSON_LOAD_FAIL %s %s"%(p,type(e).__name__))
    cfg["voice_settings"].update(job.get("voice_settings") or {})
    if job.get("speed") is not None: cfg["voice_settings"]["speed"]=job.get("speed")
    cfg["voice_id"]=job.get("voice_id") or cfg["voice_id"]
    cfg["api_key"]=cfg["api_key"] or get_key(job)
    return cfg

def tts_cache_key(text, vid, model_id, voice_settings):
    raw=text+vid+model_id+_json_canon(voice_settings)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def _tts_cache_paths(cache_key):
    return (os.path.join(TTS_CACHE_DIR,cache_key+".mp3"),
            os.path.join(TTS_CACHE_DIR,cache_key+".alignment.json"))

def _cache_valid(mp3_path, align_path):
    return os.path.exists(mp3_path) and os.path.getsize(mp3_path)>=TTS_MIN_BYTES and os.path.exists(align_path)

def tts_cache_status(text, cfg):
    cache_key=tts_cache_key(text,cfg["voice_id"],cfg["model_id"],cfg["voice_settings"])
    cache_mp3,cache_align=_tts_cache_paths(cache_key)
    needed=len(text)
    cached=needed if _cache_valid(cache_mp3,cache_align) else 0
    billable=needed-cached
    return {"key":cache_key,"needed":needed,"cached":cached,"billable":billable,
            "mp3":cache_mp3,"alignment":cache_align}

def tts_batch_cache_status(texts, cfg):
    stats=[]
    seen_billable=set()
    for t in texts:
        if not t:
            continue
        s=tts_cache_status(t,cfg)
        if s["billable"]>0:
            if s["key"] in seen_billable:
                s=dict(s)
                s["cached"]=s["needed"]
                s["billable"]=0
                s["in_batch_cache"]=True
            else:
                seen_billable.add(s["key"])
        stats.append(s)
    needed=sum(s["needed"] for s in stats)
    cached=sum(s["cached"] for s in stats)
    billable=sum(s["billable"] for s in stats)
    return {"needed":needed,"cached":cached,"billable":billable,"items":stats}

def tts_preflight(text_or_texts, cfg):
    if isinstance(text_or_texts,(list,tuple)):
        stat=tts_batch_cache_status(text_or_texts,cfg)
    else:
        stat=tts_cache_status(text_or_texts,cfg)
    msg="필요 %d자 / 캐시적중 %d자 / 실제청구 %d자"%(stat["needed"],stat["cached"],stat["billable"])
    _dl("TTS_PREFLIGHT "+msg); print("TTS_PREFLIGHT",msg)
    if stat["billable"]<=0:
        return stat
    if os.path.exists(TTS_STOP_MARKER):
        _dl("TTS_QUOTA_STOP_ACTIVE billable=%d"%stat["billable"])
        raise TTSQuotaExhausted("TTS_QUOTA_EXHAUSTED stop marker active; billable=%d"%stat["billable"])
    probe_body=json.dumps({"text":"가","model_id":cfg["model_id"],"voice_settings":cfg["voice_settings"]}).encode("utf-8")
    req=urllib.request.Request("https://api.elevenlabs.io/v1/text-to-speech/%s"%cfg["voice_id"],data=probe_body,
        headers={"xi-api-key":cfg["api_key"],"Content-Type":"application/json","User-Agent":"Mozilla/5.0 atnown/1.0"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            status=_response_status(r)
            sample=r.read()
        if status!=200:
            body=sample.decode("utf-8","ignore")
            if _looks_quota_exhausted(status,body):
                _mark_tts_quota_exhausted("preflight status=%s body=%s"%(status,body[:220]))
                raise TTSQuotaExhausted("TTS_QUOTA_EXHAUSTED preflight: "+body[:220])
            raise RuntimeError("TTS_PREFLIGHT_HTTP_%s %s"%(status,body[:300]))
        if len(sample)<TTS_MIN_BYTES:
            raise RuntimeError("TTS_PREFLIGHT_SAMPLE_TOO_SMALL bytes=%d"%len(sample))
    except urllib.error.HTTPError as e:
        body=e.read().decode("utf-8","ignore")
        if _looks_quota_exhausted(e.code,body):
            _mark_tts_quota_exhausted("preflight status=%s body=%s"%(e.code,body[:220]))
            raise TTSQuotaExhausted("TTS_QUOTA_EXHAUSTED preflight: "+body[:220])
        raise RuntimeError("TTS_PREFLIGHT_HTTP_%s %s"%(e.code,body[:300]))
    return stat

def _offset_alignment(al, offset):
    return {
        "characters":list(al.get("characters") or []),
        "character_start_times_seconds":[float(x)+offset for x in (al.get("character_start_times_seconds") or [])],
        "character_end_times_seconds":[float(x)+offset for x in (al.get("character_end_times_seconds") or [])],
    }

def _append_alignment(dst, src):
    dst["characters"].extend(src["characters"])
    dst["character_start_times_seconds"].extend(src["character_start_times_seconds"])
    dst["character_end_times_seconds"].extend(src["character_end_times_seconds"])

def tts_ts_batch(texts,out_mp3,key,vid,model_id=TTS_MODEL_ID,voice_settings=None,pause=0.35,sep_template=' <break time="%.2fs" /> '):
    """비트별 TTS를 캐시 단위로 생성하고 하나의 voice.mp3/alignment로 합친다."""
    voice_settings=voice_settings or dict(VOICE_SETTINGS)
    import tempfile
    tmp=tempfile.mkdtemp(prefix="rfj_tts_batch_")
    parts=[]
    combined={"characters":[],"character_start_times_seconds":[],"character_end_times_seconds":[]}
    t=0.0
    sep=sep_template%pause
    for i,text in enumerate(texts):
        seg_mp3=os.path.join(tmp,"seg_%03d.mp3"%i)
        al=tts_ts(text,seg_mp3,key,vid,model_id,voice_settings)
        dur=clen(seg_mp3)
        if dur<0.5:
            raise RuntimeError("TTS_SEGMENT_TOO_SHORT index=%d duration=%.3f"% (i,dur))
        parts.append(("file",seg_mp3,dur))
        _append_alignment(combined,_offset_alignment(al,t))
        t+=dur
        if i!=len(texts)-1 and pause>0:
            for c in sep:
                combined["characters"].append(c)
                combined["character_start_times_seconds"].append(t)
                combined["character_end_times_seconds"].append(t)
            parts.append(("silence",None,pause))
            t+=pause
    if not parts:
        raise RuntimeError("TTS_BATCH_EMPTY")
    inputs=[]; labels=[]
    for idx,(kind,path,dur) in enumerate(parts):
        if kind=="file":
            inputs+=["-i",path]
        else:
            inputs+=["-f","lavfi","-t","%.3f"%dur,"-i","anullsrc=r=44100:cl=stereo"]
        labels.append("[%d:a]"%idx)
    fc="".join(labels)+"concat=n=%d:v=0:a=1[a]"%len(parts)
    r=subprocess.run(["ffmpeg","-y"]+inputs+["-filter_complex",fc,"-map","[a]","-ar","44100","-ac","2",out_mp3],capture_output=True)
    if r.returncode!=0 or not os.path.exists(out_mp3):
        raise RuntimeError("TTS_BATCH_CONCAT_FAIL "+r.stderr.decode("utf-8","ignore")[-300:])
    if os.path.getsize(out_mp3)<TTS_MIN_BYTES:
        raise RuntimeError("TTS_BATCH_FILE_TOO_SMALL bytes=%d"%os.path.getsize(out_mp3))
    if clen(out_mp3)<0.5:
        raise RuntimeError("TTS_BATCH_TOO_SHORT duration=%.3f"%clen(out_mp3))
    return combined

def tts_ts(text,out_mp3,key,vid,model_id=TTS_MODEL_ID,voice_settings=None):
    """전체 대본을 한 번에 읽고 문자단위 타이밍 반환(연속 발화)."""
    voice_settings=voice_settings or dict(VOICE_SETTINGS)
    os.makedirs(TTS_CACHE_DIR,exist_ok=True)
    cache_key=tts_cache_key(text,vid,model_id,voice_settings)
    cache_mp3,cache_align=_tts_cache_paths(cache_key)
    if _cache_valid(cache_mp3,cache_align):
        shutil.copyfile(cache_mp3,out_mp3)
        _dl("TTS_CACHE_HIT key=%s bytes=%d"%(cache_key,os.path.getsize(cache_mp3)))
        with open(cache_align,encoding="utf-8") as f:
            return json.load(f)
    body=json.dumps({"text":text,"model_id":model_id,
        "voice_settings":voice_settings}).encode()
    req=urllib.request.Request("https://api.elevenlabs.io/v1/text-to-speech/%s/with-timestamps"%vid,data=body,
        headers={"xi-api-key":key,"Content-Type":"application/json","User-Agent":"Mozilla/5.0 atnown/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=90) as r:
            status=_response_status(r)
            raw=r.read()
        if status!=200:
            body=raw.decode("utf-8","ignore")
            if _looks_quota_exhausted(status,body):
                _mark_tts_quota_exhausted("tts status=%s body=%s"%(status,body[:220]))
                raise TTSQuotaExhausted("TTS_QUOTA_EXHAUSTED tts: "+body[:220])
            raise RuntimeError("TTS_HTTP_%s %s"%(status,body[:300]))
        d=json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as e:
        body=e.read().decode("utf-8","ignore")
        if _looks_quota_exhausted(e.code,body):
            _mark_tts_quota_exhausted("tts status=%s body=%s"%(e.code,body[:220]))
            raise TTSQuotaExhausted("TTS_QUOTA_EXHAUSTED tts: "+body[:220])
        raise RuntimeError("TTS_HTTP_%s %s"%(e.code,body[:300]))
    except TTSQuotaExhausted:
        raise
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError("TTS_ELEVEN_FAIL %s: %s"%(type(e).__name__,e))
    audio=base64.b64decode(d.get("audio_base64") or "")
    if len(audio)<TTS_MIN_BYTES:
        raise RuntimeError("TTS_AUDIO_TOO_SMALL bytes=%d"%len(audio))
    with open(out_mp3,"wb") as f:
        f.write(audio)
    if os.path.getsize(out_mp3)<TTS_MIN_BYTES:
        raise RuntimeError("TTS_FILE_TOO_SMALL bytes=%d"%os.path.getsize(out_mp3))
    tmp_mp3=cache_mp3+".tmp.%d"%os.getpid()
    tmp_align=cache_align+".tmp.%d"%os.getpid()
    with open(tmp_mp3,"wb") as f:
        f.write(audio)
    with open(tmp_align,"w",encoding="utf-8") as f:
        json.dump(d["alignment"],f,ensure_ascii=False)
    os.replace(tmp_mp3,cache_mp3); os.replace(tmp_align,cache_align)
    _dl("TTS_CACHE_SAVE key=%s bytes=%d"%(cache_key,len(audio)))
    return d["alignment"]

def tts_ts_local(text,out_mp3):
    """네트워크가 막힌 비상용 로컬 TTS.
    ElevenLabs 401 상태에서도 사인파가 아니라 macOS 한국어 보이스로 실제 대본을 읽는다."""
    import re, tempfile
    chars=list(text)
    starts=[]; ends=[]; t=0.0; i=0
    tmp=tempfile.mkdtemp(prefix="rfj_say_")
    audio_parts=[]  # (kind, path_or_pause, source_text, duration)

    def _synth_fallback(seg, idx):
        if os.environ.get("RFJ_ALLOW_SYNTH_TTS") != "1":
            return None, 0.0
        spoken=[c for c in seg if (not c.isspace() and c not in ".,!?~\"'")]
        chars_per_sec=float(os.environ.get("RFJ_SYNTH_CHARS_PER_SEC","6.0") or "6.0")
        dur=max(0.8, min(8.0, len(spoken) / max(1.0, chars_per_sec)))
        wav=os.path.join(tmp,"part_%03d_synth.wav"%idx)
        # Last-resort smoke-test audio for headless macOS sessions where `say`
        # returns an empty AIFF. Production runs should use ElevenLabs or `say`.
        r=subprocess.run([
            "ffmpeg","-v","error","-y","-f","lavfi",
            "-i","sine=frequency=440:sample_rate=44100:duration=%.3f"%dur,
            "-af","volume=0.12,afade=t=in:st=0:d=0.03,afade=t=out:st=%.3f:d=0.05"%max(0.0,dur-0.05),
            "-ac","1",wav,
        ],capture_output=True)
        if r.returncode!=0 or not os.path.exists(wav):
            raise RuntimeError("local synth TTS fallback 실패: "+r.stderr.decode("utf-8","ignore")[-300:])
        _dl("LOCAL_TTS_SYNTH_FALLBACK idx=%d dur=%.3f"% (idx, dur))
        return wav, dur

    def _say(seg, idx):
        plain=re.sub(r"\s+"," ",re.sub(r"<[^>]+>","",seg)).strip()
        if not plain: return None, 0.0
        base_voice=os.environ.get("MACOS_TTS_VOICE","Yuna")
        rate=os.environ.get("MACOS_TTS_RATE","165")
        voices=[base_voice]
        try:
            vr=subprocess.run(["say","-v","?"],capture_output=True,text=True,timeout=10)
            for line in (vr.stdout or "").splitlines():
                m=re.match(r"^(.*?)\s+ko_KR\s+#", line)
                if m:
                    voices.append(m.group(1).strip())
        except Exception:
            pass
        seen=set(); last_err=""
        for voice in voices:
            if not voice or voice in seen:
                continue
            seen.add(voice)
            aiff=os.path.join(tmp,"part_%03d_%d.aiff"%(idx,len(seen)))
            wav=os.path.join(tmp,"part_%03d_%d.wav"%(idx,len(seen)))
            r=subprocess.run(["say","-v",voice,"-r",rate,"-o",aiff,plain],capture_output=True)
            if r.returncode!=0 or not os.path.exists(aiff):
                last_err="macOS say TTS 실패 voice=%s: %s"%(voice,r.stderr.decode("utf-8","ignore")[-220:])
                continue
            cv=subprocess.run(["ffmpeg","-v","error","-y","-i",aiff,"-ar","44100","-ac","1",wav],capture_output=True)
            if cv.returncode!=0 or not os.path.exists(wav):
                last_err="macOS say WAV 변환 실패 voice=%s: %s"%(voice,cv.stderr.decode("utf-8","ignore")[-220:])
                continue
            dur=clen(wav)
            if dur >= 0.20:
                if voice != base_voice:
                    _dl("LOCAL_TTS_VOICE_FALLBACK %s -> %s"%(base_voice,voice))
                return wav, dur
            last_err="macOS say TTS 무음/길이없음: voice=%s duration=%.3f"% (voice, dur)
        fallback_path, fallback_dur = _synth_fallback(seg, idx)
        if fallback_path:
            return fallback_path, fallback_dur
        raise RuntimeError(last_err or "macOS say TTS 실패")

    # 오디오 조각 생성 + 원문 문자별 대략 타이밍.
    part_idx=0
    while i<len(text):
        m=re.match(r"<break\s+time=\"([\d.]+)s\"\s*/>", text[i:])
        if m:
            pause=min(0.45,float(m.group(1)))
            for _ in range(len(m.group(0))):
                starts.append(t); ends.append(t)
            audio_parts.append(("silence", pause, "", pause))
            t+=pause; i+=len(m.group(0)); continue
        j=text.find("<break", i)
        if j<0: j=len(text)
        seg=text[i:j]
        path,dur=_say(seg, part_idx); part_idx+=1
        if path: audio_parts.append(("file", path, seg, dur))
        spoken=[c for c in seg if (not c.isspace() and c not in ".,!?~\"'")]
        cd=dur/max(1,len(spoken))
        for c in seg:
            starts.append(t)
            if c.isspace() or c in ".,!?~\"'":
                ends.append(t)
            else:
                t+=cd; ends.append(t)
        i=j

    if not audio_parts:
        raise RuntimeError("local TTS 입력 비어 있음")

    inputs=[]; labels=[]; idx=0
    for kind,val,_,dur in audio_parts:
        if kind=="file":
            inputs+=["-i",val]
        else:
            inputs+=["-f","lavfi","-t","%.3f"%dur,"-i","anullsrc=r=44100:cl=mono"]
        labels.append("[%d:a]"%idx); idx+=1
    fc="".join(labels)+"concat=n=%d:v=0:a=1,volume=2.2[a]"%len(labels)
    r=subprocess.run(["ffmpeg","-y"]+inputs+["-filter_complex",fc,"-map","[a]","-ar","44100","-ac","2",out_mp3],
                     capture_output=True)
    if r.returncode!=0 or not os.path.exists(out_mp3):
        raise RuntimeError("local TTS concat 실패: "+r.stderr.decode("utf-8","ignore")[-300:])
    if clen(out_mp3) < 0.20:
        raise RuntimeError("local TTS concat 결과 무음/길이없음")
    # 로컬 say는 문장별 속도 편차가 있어 문자수 균등분배만으로 자막이 밀린다.
    # 생성된 음성을 곧바로 STT로 되받아 실제 단어 시각을 문자 타임라인에 입힌다.
    try:
        from faster_whisper import WhisperModel
        model=WhisperModel(os.environ.get("FW_MODEL","large-v3-turbo"),
                           device=os.environ.get("FW_DEVICE","cpu"),
                           compute_type=os.environ.get("FW_COMPUTE","int8"))
        segs,_info=model.transcribe(out_mp3, language="ko", word_timestamps=True, vad_filter=False, beam_size=5)
        heard=[]
        for seg in segs:
            for w in (seg.words or []):
                txt=_norm_kr((w.word or "").strip())
                if txt: heard.append((float(w.start),float(w.end),txt))
        spans=[]; k=0
        while k<len(text):
            m=re.match(r"<break\s+time=\"[\d.]+s\"\s*/>", text[k:])
            if m:
                k+=len(m.group(0)); continue
            if text[k].isspace():
                k+=1; continue
            a=k
            while k<len(text):
                if text[k].isspace() or text.startswith("<break",k): break
                k+=1
            b=k; norm=_norm_kr(text[a:b])
            if norm: spans.append((a,b,norm))
        n=min(len(spans),len(heard))
        for x in range(n):
            a,b,_=spans[x]; s,e,_ht=heard[x]
            letters=[p for p in range(a,b) if _norm_kr(text[p])]
            step=(e-s)/max(1,len(letters))
            tt=s
            for p in range(a,b):
                starts[p]=tt
                if p in letters:
                    tt+=step; ends[p]=tt
                else:
                    ends[p]=tt
        _dl("LOCAL_TTS_ALIGN words=%d/%d"%(len(heard),len(spans)))
    except Exception as e:
        _dl("LOCAL_TTS_ALIGN_FAIL %s"%type(e).__name__)
    return {"characters":chars,"character_start_times_seconds":starts,"character_end_times_seconds":ends}

def resolve_title_font(job):
    """제목·카드 = 나눔스퀘어 EB 정본(형 지시 2026-08-06 "너 추천대로").
    규칙: 흘러가는 말(자막)=교보손글씨 / 못 박는 정보(제목·카드)=나눔스퀘어 EB."""
    for c in [job.get("title_font",""),
              "~/atnown-content-pipeline/remotion/public/NanumSquareEB.ttf",
              "~/atnown-repo/remotion/public/NanumSquareEB.ttf",
              "~/atnown-content-pipeline/remotion/public/Pretendard.ttf",
              "~/atnown-repo/remotion/public/Pretendard.ttf",
              "~/atnown-content-pipeline/remotion/public/Kyobo.otf"]:
        p=os.path.expanduser(c or "")
        if p and os.path.exists(p): return p
    return None

def wb_filter(src, ss, strength=0.85, look=True, target_luma=128.0):
    """자동 화이트밸런스 + 가벼운 룩.
    핵심: **무채색(중성) 픽셀만** 보고 색치우침을 계산한다.
    화면 전체 평균(gray-world)으로 하면 빨간 옷·초록 벽처럼 큰 유채색 물체를
    '색 치우침'으로 오해해 반대색으로 밀어버린다(실측 사고 2026-08-06: 빨간 상의 → 화면이 초록).
    """
    try:
        raw=subprocess.run(["ffmpeg","-v","error","-ss","%.3f"%max(0.0,float(ss)),"-i",src,"-frames:v","1",
                            "-vf","scale=64:64,format=rgb24","-f","rawvideo","-"],capture_output=True).stdout
        n=len(raw)//3
        if n<100: return ""
        sR=sG=sB=0.0; cnt=0; lum_s=0.0
        for i in range(n):
            r=raw[3*i]; g=raw[3*i+1]; b=raw[3*i+2]
            mx=max(r,g,b); mn=min(r,g,b)
            lum_s+=0.299*r+0.587*g+0.114*b
            if mx<25 or mx>245: continue          # 너무 어둡/날아간 픽셀 제외
            if (mx-mn)>38: continue               # 유채색(옷·벽 등) 제외 → 중성 픽셀만
            sR+=r; sG+=g; sB+=b; cnt+=1
        lum=lum_s/n
        if cnt<n*0.06:                            # 중성 픽셀이 너무 적으면 색보정 생략(오판 방지)
            return ("eq=contrast=1.05:saturation=1.03" if look else "")
        R=sR/cnt; G=sG/cnt; B=sB/cnt
        tgt=(R+G+B)/3.0
        if tgt<5: return ""
        def g_(c):
            v=1.0 if c<1 else tgt/c
            v=1.0+(v-1.0)*strength
            return max(0.86,min(1.16,v))          # 과보정 방지(색 뒤집힘 차단)
        gr,gg,gb=g_(R),g_(G),g_(B)
        f="colorchannelmixer=rr=%.3f:gg=%.3f:bb=%.3f"%(gr,gg,gb)
        br=max(-0.10,min(0.10,(target_luma-lum)/255.0))
        if look: f+=",eq=contrast=1.05:saturation=1.04:brightness=%.3f"%br
        return f
    except Exception:
        return ""

def neutral_profile(src, fracs=(0.30,0.45,0.60,0.75)):
    """클립 전반의 '무채색(중성) 픽셀' 평균 색/밝기 프로파일.
    옷·벽 같은 유채색은 제외(mx-mn>38) → 빨간 상의 등에 오염되지 않음.
    여러 시점 평균으로 안정화. 반환 (R,G,B,lum) 또는 None(중성 픽셀 부족)."""
    try:
        dur=clen(src) or 0.0
        ts=[max(0.0,dur*f) for f in fracs] if dur>0.6 else [max(0.0,dur*0.5)]
        sR=sG=sB=0.0; cnt=0; lum_s=0.0; ncnt=0
        for t in ts:
            raw=subprocess.run(["ffmpeg","-v","error","-ss","%.2f"%t,"-i",src,"-frames:v","1",
                                "-vf","scale=64:64,format=rgb24","-f","rawvideo","-"],capture_output=True).stdout
            n=len(raw)//3
            if n<100: continue
            for i in range(n):
                r=raw[3*i]; g=raw[3*i+1]; b=raw[3*i+2]
                mx=max(r,g,b); mn=min(r,g,b)
                lum_s+=0.299*r+0.587*g+0.114*b; ncnt+=1
                if mx<25 or mx>245: continue
                if (mx-mn)>38: continue
                sR+=r; sG+=g; sB+=b; cnt+=1
        if ncnt<100 or cnt<ncnt*0.05: return None
        return (sR/cnt, sG/cnt, sB/cnt, lum_s/ncnt)
    except Exception:
        return None

_TONE_REF_CACHE={}
def tone_ref_profile(job, cdir):
    """레퍼런스 클립(job['tone_ref'])의 중성 프로파일을 1회 계산·캐시."""
    key=job.get("tone_ref")
    if not key: return None
    if key in _TONE_REF_CACHE: return _TONE_REF_CACHE[key]
    src=key if os.path.isabs(key) else os.path.join(cdir, key)
    prof=neutral_profile(src)
    _TONE_REF_CACHE[key]=prof
    _dl("TONE_REF %s -> %s"%(key, prof))
    return prof

def tone_match_filter(src, ref_prof, strength=0.90, look=True):
    """각 클립의 중성 프로파일을 레퍼런스에 맞춤 → 색온도+노출 통일(톤 매칭).
    레퍼런스 자신은 gain≈1.0(패스스루). auto_wb 대비 클램프를 넓혀
    어둡/따뜻하게 튄 클립도 첫 클립 톤까지 실제로 당겨온다."""
    if not ref_prof:
        return "eq=contrast=1.05:saturation=1.03" if look else ""
    prof=neutral_profile(src)
    if not prof:
        return "eq=contrast=1.05:saturation=1.03" if look else ""
    R,G,B,lum=prof; rR,rG,rB,rlum=ref_prof
    def g_(rc,c):
        if c<1: return 1.0
        return 1.0+((rc/c)-1.0)*strength
    gr,gg,gb=g_(rR,R),g_(rG,G),g_(rB,B)
    # 색(화이트밸런스)만 맞추고 밝기 성분은 분리 → 밝은 클립이 날아가지 않게.
    L=0.299*gr+0.587*gg+0.114*gb
    if L>0.01: gr,gg,gb=gr/L,gg/L,gb/L
    cl=lambda v:max(0.85,min(1.18,v))
    gr,gg,gb=cl(gr),cl(gg),cl(gb)
    f="colorchannelmixer=rr=%.3f:gg=%.3f:bb=%.3f"%(gr,gg,gb)
    # 노출은 완만하게만 통일(±0.08) → 어두운 클립은 끌어올리되 과노출 방지.
    br=max(-0.08,min(0.08,((rlum-lum)/255.0)*strength))
    if look: f+=",eq=contrast=1.05:saturation=1.04:brightness=%.3f"%br
    _dl("TONE_MATCH %s prof=%s -> %s"%(os.path.basename(src),[round(x,1) for x in prof],f))
    return f

_FS_CACHE={}
def frame_stats(src, t):
    """해당 시점 프레임의 밝기/색편차/디테일. 손바닥이 렌즈를 덮거나(단색·붉음)
    초록 플래시 같은 불량 구간을 걸러내기 위함(형 지적 2026-08-06)."""
    ck=(src,round(t,2))
    if ck in _FS_CACHE: return _FS_CACHE[ck]
    try:
        raw=subprocess.run(["ffmpeg","-v","error","-ss","%.2f"%max(0.0,t),"-i",src,"-frames:v","1",
                            "-vf","scale=48:48,format=rgb24","-f","rawvideo","-"],capture_output=True).stdout
        n=len(raw)//3
        if n<100: return None
        R=[raw[i] for i in range(0,len(raw),3)]; G=[raw[i] for i in range(1,len(raw),3)]; B=[raw[i] for i in range(2,len(raw),3)]
        mR=sum(R)/n; mG=sum(G)/n; mB=sum(B)/n
        lum=[(0.299*R[i]+0.587*G[i]+0.114*B[i]) for i in range(n)]
        m=sum(lum)/n
        var=sum((x-m)**2 for x in lum)/n
        res={"lum":m,"detail":var**0.5,"R":mR,"G":mG,"B":mB}
        _FS_CACHE[ck]=res
        return res
    except Exception:
        _FS_CACHE[ck]=None
        return None

def bad_frame(st):
    if not st: return True
    if st["lum"]<28 or st["lum"]>238: return True
    if st["detail"]<16: return True                        # 단색(손바닥이 렌즈 덮음 등)
    if st["R"]-max(st["G"],st["B"])>55: return True         # 살색/붉은 화면
    if st["G"]-max(st["R"],st["B"])>40: return True         # 초록 플래시
    return False

def shot_uniform(src, ss, want, tol=26.0):
    """구간 안에서 화면이 바뀌는지 검사. 한 구간에 서로 다른 장면이 섞이면
    톤 보정을 한 값으로 걸 수 없어 일부가 누렇게 남는다(형 지적 2026-08-06).
    → 표본 프레임들의 색·밝기 차이가 크면 '다른 화면'으로 보고 그 구간을 쓰지 않는다."""
    pts=[ss+0.15, ss+want*0.33, ss+want*0.66, max(ss+0.2, ss+want-0.2)]
    sts=[frame_stats(src,t) for t in pts]
    sts=[x for x in sts if x]
    if len(sts)<3: return False,None
    def d(a,b):
        return max(abs(a["R"]-b["R"]),abs(a["G"]-b["G"]),abs(a["B"]-b["B"]),abs(a["lum"]-b["lum"]))
    worst=0.0
    for i in range(len(sts)):
        for j in range(i+1,len(sts)):
            worst=max(worst,d(sts[i],sts[j]))
    return (worst<=tol), worst

def pick_start(src, want, prefer=0.3):
    """불량 구간을 피하고, **한 장면으로 이어지는(톤이 균일한)** 시작점을 고른다."""
    dur=clen(src)
    if dur<=0: return prefer
    hi=max(0.2, dur-want-0.2)
    cands=[prefer]+[hi*x for x in (0.12,0.28,0.45,0.62,0.80)]
    seen=set(); best=None; fallback=None
    for c in cands:
        c=round(min(max(0.2,c),hi),2)
        if c in seen: continue
        seen.add(c)
        pts=[c+0.2, c+want*0.5, max(c+0.2,c+want-0.3)]
        sts=[frame_stats(src,t) for t in pts]
        if any(bad_frame(s) for s in sts): continue
        detail=min(s["detail"] for s in sts if s)
        uni,worst=shot_uniform(src,c,want)
        if fallback is None or detail>fallback[1]: fallback=(c,detail)
        if not uni: continue                     # 장면이 섞인 구간은 제외
        score=detail-(worst or 0)*0.3
        if best is None or score>best[1]: best=(c,score)
        if best and best[1]>30: break          # 충분히 좋은 구간이면 조기 종료(속도)
    if best: return best[0]
    return fallback[0] if fallback else prefer

def clip_sig(path):
    """내용 기준 중복 판정용 서명(길이+용량). 이름만 다른 같은 영상을 걸러낸다."""
    try: return (round(clen(path),1), os.path.getsize(path)//100000)
    except Exception: return (0,0)

# ── 나레이션 자연스러움 규약 (형 볼트 「나레이션 라임 규약」 + 제작규격 정본) ──
PRON_DICT={"읽나요":"잉나요","않나요":"안나요","맞나요":"만나요","닿나요":"다나요",
           "S자":"에스자","V라인":"브이라인","A라인":"에이라인","C컬":"씨컬"}
END_OK=("요.","요?","죠.","죠?","다.","다!","까?","요!","니다.","세요.","세요?","예요.","이에요.")

def rhyme_prep(text, pron=None):
    """TTS 전 부호 정리: 종결부호 없으면 마침표, 발음 오독 단어 치환."""
    t=(text or "").strip()
    d=dict(PRON_DICT); d.update(pron or {})
    for k,v in d.items():
        if k in t: t=t.replace(k,v)
    if t and t[-1] not in ".?!,":
        t+="."
    return t

def rhyme_check(beats):
    """규약 준수 검사(텍스트 단계). 어기면 어색함의 원인이 된다."""
    bad_end=[]; no_comma=[]; too_long=[]
    for i,b in enumerate(beats):
        t=(b.get("say") or "").strip()
        if not t: continue
        if not t.endswith(END_OK) and t[-1] not in ".?!": bad_end.append(i)
        if len(t)>=18 and ("," not in t): no_comma.append(i)   # 긴 문장에 호흡 표시 없음
        if len(t)>60: too_long.append(i)
    return {"end_missing":bad_end,"no_breath_comma":no_comma,"too_long":too_long,
            "rhyme_ok":not (bad_end or too_long)}

THUMB_Y=270
THUMB_DUR=0.6
THUMB_MAX_LEN=13

def thumb_len(text):
    return len((text or "").strip())

def auto_thumb_text(text):
    """첫 문장에서 쇼츠 그리드용 13자 한 줄 문구를 만든다.
    자동 축약이 실패하면 13자까지 자르고, 체크리스트가 최종 반려/승인 기준을 맡는다."""
    t=re.sub(r"<[^>]+>"," ",text or "")
    t=re.split(r"[.!?\n]",t,1)[0]
    t=re.sub(r"\([^)]*\)|\[[^\]]*\]"," ",t)
    t=re.sub(r"[A-Za-z0-9_@#:/\\|]+"," ",t)
    t=re.sub(r"[^가-힣\s]"," ",t)
    words=[w.strip() for w in t.split() if w.strip()]
    if not words:
        return "앳나운"
    drop_end=("요","죠","니다","습니다","예요","이에요","세요","해요","합니다","됩니다","입니다","입니다만")
    particles=("은","는","이","가","을","를","에","에서","에게","도","만","부터","까지","으로","로","와","과","랑","하고")
    cleaned=[]
    for w in words:
        for e in drop_end:
            if w.endswith(e) and len(w)>len(e)+1:
                w=w[:-len(e)]
                break
        for p in particles:
            if w.endswith(p) and len(w)>len(p)+1:
                w=w[:-len(p)]
                break
        if w: cleaned.append(w)
    phrase=" ".join(cleaned) or " ".join(words)
    if thumb_len(phrase)<=THUMB_MAX_LEN:
        return phrase
    compact="".join(cleaned) or "".join(words)
    return compact[:THUMB_MAX_LEN]

def make_thumb_png(text, out, font_path):
    from PIL import Image, ImageDraw, ImageFont
    font=ImageFont.truetype(font_path,76)
    d0=ImageDraw.Draw(Image.new("RGBA",(4,4)))
    box=d0.textbbox((0,0),text or " ",font=font)
    tw=box[2]-box[0]; th=box[3]-box[1]
    asc,desc=font.getmetrics()
    line_h=max(th, asc+desc)
    W=int(tw+34*2); H=int(line_h+22*2)
    img=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(img)
    d.rectangle([0,0,W-1,H-1],fill=(12,12,12,255))
    y=(H-th)/2-box[1]
    d.text((34-box[0],y),text,font=font,fill=(255,255,255,255))
    img.save(out); return out,W,H

def thumb_bar_present(video_path, t=0.3):
    """첫 0.6초 상단 바 존재를 픽셀로 스모크 확인한다."""
    try:
        raw=subprocess.run(["ffmpeg","-v","error","-ss","%.2f"%t,"-i",video_path,"-frames:v","1",
                            "-vf","crop=1080:150:0:%d,format=rgb24"%max(0,THUMB_Y-20),
                            "-f","rawvideo","-"],capture_output=True,timeout=30).stdout
        n=len(raw)//3
        if n<1000: return False
        dark=0; white=0
        for i in range(n):
            r=raw[3*i]; g=raw[3*i+1]; b=raw[3*i+2]
            if r<28 and g<28 and b<28: dark+=1
            if r>220 and g>220 and b>220: white+=1
        return dark/n>0.05 and white/n>0.002
    except Exception:
        return False

def black_sample_ratio(video_path):
    """B방 검수 기준: 4fps, 32x57 gray 평균 12 미만 프레임 비율."""
    try:
        raw=subprocess.run(["ffmpeg","-v","error","-i",video_path,
                            "-vf","fps=4,scale=32:57,format=gray",
                            "-f","rawvideo","-"],
                           capture_output=True,timeout=600).stdout
        fsz=32*57
        total=len(raw)//fsz
        if total<=0:
            return None
        black=0
        for off in range(0,total*fsz,fsz):
            f=raw[off:off+fsz]
            if (sum(f)/float(fsz)) < 12.0:
                black+=1
        return black, total, black/float(total)
    except Exception:
        return None

def speech_metrics(al, audio_end):
    """발화 실측: 속도(음절/초)·문장 내 이상 무음."""
    try:
        chars=al["characters"]; cs=al["character_start_times_seconds"]; ce=al["character_end_times_seconds"]
        # break 태그(<break .../>) 안의 글자는 발화가 아니므로 제외해야 속도가 정확하다
        vis=[]; intag=False
        for i,c in enumerate(chars):
            if c=="<": intag=True; continue
            if c==">": intag=False; continue
            if intag: continue
            if c.isspace(): continue
            if c in ".,!?~\"'": continue
            vis.append(i)
        syl=len(vis)
        rate=syl/max(0.1,audio_end)
        gaps=[]
        for a,b in zip(vis, vis[1:]):
            g=cs[b]-ce[a]
            if g>0.05: gaps.append(round(g,2))
        long_gaps=[g for g in gaps if g>0.75]
        return {"syllables":syl,"rate_syl_s":round(rate,2),
                "rate_ok":4.2<=rate<=8.6,   # 한국어 자연 발화 범위
                "long_gaps":long_gaps[:6],"gap_ok":len(long_gaps)<=2}
    except Exception:
        return {"rate_ok":True,"gap_ok":True}

# ── 사진 콜라주 + 자유 텍스트 박스 (형 레퍼런스: 앳나운 스토리 배열 · 낙타 텍스트박스) ──
NOTE_STYLES={
 "white":{"bg":(255,255,255,240),"fg":(15,15,15,255)},
 "black":{"bg":(0,0,0,225),"fg":(255,255,255,255)},
 "cyan" :{"bg":(120,230,245,245),"fg":(15,15,15,255)},
 "yellow":{"bg":(255,225,77,245),"fg":(20,20,20,255)},
}

def make_note_png(text, out, font_path, size=52, style="white", pad=22, maxw=880):
    """낙타식 텍스트 박스 — 배경색 박스 + 글씨. 줄바꿈은 | 로."""
    from PIL import Image, ImageDraw, ImageFont
    st=NOTE_STYLES.get(style,NOTE_STYLES["white"])
    font=ImageFont.truetype(font_path,size)
    lines=[l for l in text.split("|") if l!=""]
    d0=ImageDraw.Draw(Image.new("RGBA",(4,4)))
    dims=[d0.textbbox((0,0),l or " ",font=font) for l in lines]
    asc,desc=font.getmetrics(); lh=asc+desc; gap=10
    tw=max((b[2]-b[0]) for b in dims) if dims else size
    W=int(min(maxw,tw)+pad*2); H=int(len(lines)*lh+(len(lines)-1)*gap+pad*1.4)
    img=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(img)
    d.rectangle([0,0,W-1,H-1],fill=st["bg"])
    y=int(pad*0.7)
    for i,l in enumerate(lines):
        b=dims[i]
        d.text((pad-b[0], y), l, font=font, fill=st["fg"])
        y+=lh+gap
    img.save(out); return out,W,H

def make_collage_png(photos, out, canvas=(1080,1920), layout="story"):
    """사진 배열 오버레이. photos = 로컬 경로 리스트(최대 4장).
    story 배열: 1번=크게 위쪽, 2번=우중단 인셋, 3번=중앙하단 인셋, 4번=좌하단 작게.
    (형 레퍼런스 = 메인 + 인셋들이 겹쳐 배치되는 스토리 콜라주)"""
    from PIL import Image
    W,H=canvas
    img=Image.new("RGBA",(W,H),(0,0,0,0))
    boxes={
      # story: 메인 크게 위 + 아래 한 줄로 크게 3장(겹치지 않게, 여백 확보)
      "story":[(0,170,1080,930),(30,1170,336,336),(372,1170,336,336),(714,1170,336,336)],
      # big2: 메인 + 큰 인셋 1장 (가장 잘 보임)
      "big2" :[(0,220,1080,900),(300,1180,480,430)],
      "grid" :[(40,240,480,620),(560,240,480,620),(40,900,480,620),(560,900,480,620)],
    }.get(layout, None)
    if boxes is None: boxes=[(0,120,1080,1000)]
    for i,ph in enumerate(photos[:len(boxes)]):
        try:
            im=Image.open(ph).convert("RGBA")
        except Exception:
            continue
        x,y,bw,bh=boxes[i]
        r=max(bw/im.width, bh/im.height)
        im=im.resize((max(1,int(im.width*r)),max(1,int(im.height*r))))
        left=(im.width-bw)//2; top=(im.height-bh)//2
        im=im.crop((left,top,left+bw,top+bh))
        if i>0:   # 인셋은 흰 테두리로 분리감
            from PIL import ImageOps
            im=ImageOps.expand(im,border=6,fill=(255,255,255,255))
            x-=6; y-=6
        img.paste(im,(x,y),im)
    img.save(out); return out

# ── 영상 간 클립 재사용 방지 (형 지적 2026-08-06: "B롤이 전 영상이랑 비슷해서 에러") ──
def _usage_path(): return os.path.expanduser("~/atnown-content-pipeline/_CLIP_USAGE.json")
def load_usage():
    try: return json.load(open(_usage_path(),encoding="utf-8"))
    except Exception: return {"videos":[]}
def recent_clips(n=3):
    """최근 n편에서 쓴 클립 집합 — 다음 편에서는 피한다."""
    u=load_usage(); used=set()
    for v in u.get("videos",[])[-n:]:
        used.update(v.get("clips",[]))
    return used
def recent_axes(n=4):
    """최근 n편의 편성 축. 빈 값은 축 반복 경고 계산에서 제외한다."""
    u=load_usage()
    return [v.get("axis") for v in u.get("videos",[])[-n:] if v.get("axis")]
def save_usage(out, clips, form=None, axis=None):
    u=load_usage()
    row={"out":os.path.basename(out),"clips":sorted(set(clips)),"form":form}
    if axis:
        row["axis"]=axis
    u.setdefault("videos",[]).append(row)
    u["videos"]=u["videos"][-40:]
    try: json.dump(u,open(_usage_path(),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    except Exception: pass

def camel_marketing_gate(job, beats):
    """_자주하는실수_박제.md 8번: 낙타마케팅 관점 잡 검사."""
    axis=(job.get("axis") or "").strip()
    allowed_axes={"재미","감동","정보"}
    axis_missing=not bool(axis)
    axis_invalid=bool(axis and axis not in allowed_axes)
    recent=recent_axes(4)
    axis_window=recent+([axis] if axis and not axis_invalid else [])
    axis_repeat_warning=bool(len(axis_window)>=5 and len(set(axis_window[-5:]))==1)

    one_idea=[]
    for i,b in enumerate(beats):
        say=str(b.get("say",""))
        if say.count(".")>=2:
            one_idea.append({"beat":i,"periods":say.count("."),"say":say})

    last_beat=next((b for b in reversed(beats) if str(b.get("say","")).strip()), None)
    marker_values={"차노 한마디","chano_line","brand_line","brand_declaration","브랜드 선언"}
    chano_line_ok=False
    if last_beat:
        chano_line_ok=bool(
            last_beat.get("chano_line") or
            last_beat.get("brand_line") or
            last_beat.get("brand_declaration") or
            str(last_beat.get("role","")).strip() in marker_values or
            str(last_beat.get("kind","")).strip() in marker_values or
            str(last_beat.get("type","")).strip() in marker_values or
            str(last_beat.get("label","")).strip() in marker_values or
            bool(last_beat.get("chano"))
        )

    notes=[]
    if not chano_line_ok:
        notes.append("차노 한마디 없음")
    if axis_missing:
        notes.append('axis 없음: job에 "axis": "재미|감동|정보" 필요')
    elif axis_invalid:
        notes.append('axis 값 오류: "재미|감동|정보" 중 하나')
    if axis_repeat_warning:
        notes.append("최근 5편 축 반복 경고: %s"%axis_window[-1])
    if one_idea:
        notes.append("one_idea 경고: 마침표 2개 이상 say %d개"%len(one_idea))

    return {
        "chano_line_ok":chano_line_ok,
        "one_idea":one_idea,
        "one_idea_ok":not one_idea,
        "axis":axis,
        "axis_missing":axis_missing,
        "axis_invalid":axis_invalid,
        "axis_recent":axis_window[-5:],
        "axis_repeat_warning":axis_repeat_warning,
        "notes":notes,
    }

def vault_hits_for_job(job, beats, limit=6):
    """_VAULT_INDEX.json에서 beats 텍스트와 topic_keywords에 걸리는 카드명을 찾는다.
    0개여도 렌더는 계속 진행하고, 최종 CHECKLIST에 경고만 남긴다."""
    path=os.path.expanduser(job.get("vault_index","~/atnown-content-pipeline/_VAULT_INDEX.json"))
    try:
        idx=json.load(open(path,encoding="utf-8"))
    except Exception as e:
        return [], "vault_index_read_failed:%s"%type(e).__name__
    terms=[]
    for k in job.get("topic_keywords") or []:
        if isinstance(k,str) and len(k.strip())>=2: terms.append(k.strip().lower())
    text=" ".join((b.get("say","")+" "+b.get("cap","")) for b in beats if isinstance(b,dict)).lower()
    for raw in text.replace("|"," ").replace("\n"," ").split():
        w=raw.strip(" ,.!?~\"'()[]{}:;").lower()
        if len(w)>=2 and not w.isdigit(): terms.append(w)
    # 순서를 유지하며 중복 제거. 너무 흔한 한 글자/숫자 토큰은 위에서 제외된다.
    seen=set(); terms=[t for t in terms if not (t in seen or seen.add(t))][:80]
    scored=[]
    for it in idx.get("items",[]):
        title=(it.get("title") or "")
        hay=" ".join([title,it.get("one_line") or ""," ".join(it.get("keywords") or [])]).lower()
        score=0
        for t in terms:
            if not t: continue
            if t in title.lower(): score+=4
            elif t in hay: score+=1
        if score>0: scored.append((score,title))
    scored.sort(key=lambda x:(-x[0],x[1]))
    return [t for _,t in scored[:limit]], None

LAYOUT_HITS=[]
CAP_TRACE=[]
CANVAS_MAXW=1020   # 1080 캔버스에서 좌우 30px는 무조건 비운다

def make_text_png(lines, out, font_path, fontsize, color=(255,255,255,255), box_alpha=150, pad=30, line_gap=18, bold=False, maxw=CANVAS_MAXW):
    from PIL import Image, ImageDraw, ImageFont
    d0=ImageDraw.Draw(Image.new("RGBA",(4,4)))
    # 폭 자동 축소: 한 줄이라도 캔버스를 넘으면 넘지 않을 때까지 폰트를 줄인다.
    # 왜(형 지적 2026-08-08): "웨이브는 양이 아니라, 위치거든요"가 좌우로 잘려 나갔다.
    #   글자수 기준(max_chars)으로만 끊으면 글자 폭이 제각각이라 반드시 새어 나간다. 실측 폭으로 막는다.
    fs=int(fontsize)
    while fs>18:
        f_=ImageFont.truetype(font_path, fs)
        dd=[d0.textbbox((0,0),ln or " ",font=f_) for ln in lines]
        if max((b[2]-b[0]) for b in dd)+pad*2 <= maxw: break
        fs-=2
    fontsize=fs
    font=ImageFont.truetype(font_path, fontsize)
    dims=[d0.textbbox((0,0),ln or " ",font=font) for ln in lines]
    ws=[b[2]-b[0] for b in dims]; asc,desc=font.getmetrics(); lh=asc+desc
    tw=max(ws) if ws else fontsize
    boxw=int(tw+pad*2); boxh=int(len(lines)*lh+(len(lines)-1)*line_gap+pad*2)
    img=Image.new("RGBA",(boxw,boxh),(0,0,0,0)); d=ImageDraw.Draw(img)
    if box_alpha>0: d.rounded_rectangle([0,0,boxw-1,boxh-1],radius=16,fill=(0,0,0,box_alpha))
    y=pad
    for i,ln in enumerate(lines):
        b=dims[i]; w=b[2]-b[0]; x=(boxw-w)/2 - b[0]
        if bold:
            # ① 먼저 검정 외곽선을 두껍게 깐다 — 흰 글자가 밝은 배경에 묻히는 사고 방지
            #    (2026-08-07 형 지적: "큰 글자 흰 글씨 윤곽선 없어서 잘 안 보임")
            ow=max(3,int(fontsize*0.055))
            for dx in range(-ow,ow+1):
                for dy in range(-ow,ow+1):
                    if dx*dx+dy*dy<=ow*ow:
                        d.text((x+dx,y+dy),ln,font=font,fill=(0,0,0,205))
            # ② 그 위에 가짜 볼드(두께감)
            for dx,dy in ((-2,0),(2,0),(0,-2),(0,2),(-1,-1),(1,1),(-1,1),(1,-1)):
                d.text((x+dx,y+dy),ln,font=font,fill=color)
        else:
            # 가독성용 얇은 외곽선(밝은 배경에서도 안 묻힘)
            for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)):
                d.text((x+dx,y+dy),ln,font=font,fill=(0,0,0,190))
        d.text((x, y),ln,font=font,fill=color)
        y+=lh+line_gap
    img.save(out); return out, boxw, boxh


def _norm_kr(t):
    import re as _re
    return _re.sub(r"[^0-9A-Za-z가-힣]","",t or "")

def _script_sentence_count(beats):
    """듣기 게이트용 대본 문장 수.
    B방 게이트 정본은 beat 수가 아니라 대본 문장 수다. 문장부호가 없는 짧은 beat는
    한 문장으로 세고, 한 beat 안의 여러 문장은 각각 센다."""
    cnt=0
    for b in beats:
        say=str(b.get("say","")).strip()
        if not _norm_kr(say):
            continue
        parts=[p for p in re.split(r"[.!?。！？]+", say) if _norm_kr(p)]
        cnt += max(1, len(parts))
    return max(1,cnt)

def _fw_model(model_name=None):
    from faster_whisper import WhisperModel
    mn=model_name or os.environ.get("FW_MODEL","small")
    dev=os.environ.get("FW_DEVICE","cpu")
    ct=os.environ.get("FW_COMPUTE","int8")
    ck=(mn,dev,ct)
    model=_FW_MODEL_CACHE.get(ck)
    if model is None:
        model=WhisperModel(mn, device=dev, compute_type=ct)
        _FW_MODEL_CACHE[ck]=model
    return model

def _stt_words(audio_path, model_name=None):
    model=_fw_model(model_name)
    segs,_info=model.transcribe(audio_path, language="ko", word_timestamps=True, vad_filter=False, beam_size=5)
    ws=[]
    for seg in segs:
        for w in (seg.words or []):
            txt=(w.word or "").strip()
            if txt:
                ws.append({"text":txt,"start":float(w.start),"end":float(w.end)})
    return ws

def _wav16k_from_media(media_path, out_wav):
    r=subprocess.run(["ffmpeg","-v","error","-y","-i",media_path,"-vn","-ac","1","-ar","16000",out_wav],
                     capture_output=True,text=True,timeout=240)
    if r.returncode!=0 or not os.path.exists(out_wav):
        raise RuntimeError("WAV16K_EXTRACT_FAIL "+(r.stderr or "")[-300:])
    return out_wav

def _stt_segments(audio_path, model_name=None):
    """B방 듣기 게이트 정본: wav16k + faster-whisper small/cpu/int8 + vad_filter=True."""
    model=_fw_model(model_name or os.environ.get("AUDIT_FW_MODEL","small"))
    segs,_info=model.transcribe(audio_path, language="ko", word_timestamps=True,
                                 vad_filter=True, beam_size=5)
    segs=list(segs)
    ws=[]
    for seg in segs:
        if seg.words:
            for w in seg.words:
                txt=(w.word or "").strip()
                if txt:
                    ws.append({"text":txt,"start":float(w.start),"end":float(w.end)})
        elif (seg.text or "").strip():
            ws.append({"text":seg.text.strip(),"start":float(seg.start),"end":float(seg.end)})
    return segs, ws

def _voice_onset_in_media(path):
    try:
        rr=subprocess.run(["ffmpeg","-i",path,"-af","silencedetect=noise=-40dB:d=0.15","-f","null","-"],
                          capture_output=True,text=True,timeout=180).stderr
        m=re.search(r"silence_end:\s*([\d.]+)",rr)
        if m: return float(m.group(1))
    except Exception:
        pass
    return 0.0

def audit_audio(mp4, job, beats, starts, intro_sec, key):
    """완성본의 오디오를 STT로 되받아 ① 대본대로 읽었는지 ② 자막과 맞는지를 실측한다.
    왜(형 지시 2026-08-08): 나는 못 듣는다. 듣는 대신 재야 같은 실수가 반복되지 않는다.
    ElevenLabs STT는 쓰지 않는다. 로컬 faster-whisper 결과가 없으면 즉시 FAIL이다."""
    import difflib
    script_sentence_count=_script_sentence_count(beats)
    def _measure(ws, seg_count=0, first_segment_start=None, seg_starts=None, seg_items=None):
        if seg_count == 0 or len(ws) == 0:
            return {
                "audit":"stt_empty",
                "stt":"faster-whisper",
                "segments":seg_count,
                "script_sentences":script_sentence_count,
                "voice_present_ok":False,
                "read_ratio":0.0,
                "read_bad":[{"beat":0,"say":"voice missing","heard":"","r":0.0}],
                "sync_drifts":[],
                "sync_avg":0.0,
                "sync_max":0.0,
                "sync_bias":0.0,
                "inner_gaps":[],
                "heard_head":"",
                "first_segment_start":0.0,
                "stt_sync_ok":False,
            }
        min_segments=max(1, int(script_sentence_count*0.60 + 0.999))
        voice_present_ok=seg_count >= min_segments
        first_segment_start=float(first_segment_start if first_segment_start is not None else ws[0]["start"])
        onset=_voice_onset_in_media(mp4)
        stt_onset_offset=0.0
        if first_segment_start is not None and 0.05<onset<2.0 and float(first_segment_start)<0.10:
            stt_onset_offset=onset-float(first_segment_start)
            first_segment_start=onset
        ws_sync=ws
        if stt_onset_offset>0.20:
            ws_sync=[dict(w, start=float(w["start"])+stt_onset_offset, end=float(w["end"])+stt_onset_offset) for w in ws]
        heard=_norm_kr("".join(w["text"] for w in ws))
        script=_norm_kr(" ".join(b.get("say","") for b in beats))
        ratio=difflib.SequenceMatcher(None,script,heard).ratio()

        bad=[]
        pos=0
        for i,b in enumerate(beats):
            sc=_norm_kr(b.get("say",""))
            if not sc: continue
            win=heard[pos:pos+len(sc)]
            r2=difflib.SequenceMatcher(None,sc,win).ratio()
            if r2<0.80: bad.append({"beat":i,"say":b.get("say","")[:26],"heard":win[:26],"r":round(r2,2)})
            pos+=len(sc)

        cap_starts=[intro_sec+starts[bi]+CAP_SYNC for bi,b in enumerate(beats)
                    if bi < len(starts) and _norm_kr(b.get("say",""))]
        seg_drifts=[]
        if seg_items and cap_starts:
            adj_items=list(seg_items)
            if stt_onset_offset>0.20:
                adj_items=[dict(item, start=float(item["start"])+stt_onset_offset) for item in adj_items]
            used_caps=set()
            for item in adj_items:
                st=float(item.get("start",0.0))
                choices=[(abs(cap-st), ci, cap) for ci,cap in enumerate(cap_starts) if ci not in used_caps]
                if not choices:
                    break
                delta, ci, cap=min(choices)
                if delta <= 0.75:
                    used_caps.add(ci)
                    seg_drifts.append(round(cap-st,3))

        drifts=seg_drifts[:]
        # 보조 경로: 세그먼트 매칭이 충분하지 않을 때만 단어 위치 매핑을 쓴다.
        # 세그먼트 기준이 B방 게이트 정본이고, 단어 누적 매핑은 숫자/띄어쓰기 변환에서
        # 뒤쪽 비트가 크게 튈 수 있어 주 판정값으로 쓰지 않는다.
        word_offsets=[]; cur_pos=0
        for w in ws_sync:
            wn=_norm_kr(w.get("text",""))
            if not wn:
                continue
            word_offsets.append((cur_pos, cur_pos+len(wn), float(w["start"])))
            cur_pos += len(wn)
        if len(drifts) < max(1, min(3, len(cap_starts))) and word_offsets:
            # 먼저 각 beat의 앞쪽 문구를 전사문에서 전진 검색한다.
            # difflib 전체 매핑은 반복 문구가 많은 편에서 뒤쪽 동일 문장에 붙어
            # 30~50초짜리 가짜 싱크 오류를 만들 수 있다.
            beat_norms_direct=[_norm_kr(b.get("say","")) for b in beats]
            search_from=0
            direct_drifts=[]
            for bi,bn in enumerate(beat_norms_direct):
                if not bn or bi>=len(starts):
                    continue
                probes=[]
                for n in (18,14,10,6):
                    if len(bn) >= n:
                        probes.append(bn[:n])
                probes.append(bn[:min(len(bn),4)])
                found=-1
                for probe in probes:
                    if not probe:
                        continue
                    found=heard.find(probe, max(0, search_from-3))
                    if found >= 0:
                        break
                if found < 0:
                    continue
                speech_start=None
                for a,bend,st in word_offsets:
                    if bend > found:
                        speech_start=st
                        break
                if speech_start is not None:
                    cap_on=intro_sec+starts[bi]+CAP_SYNC
                    direct_drifts.append(round(cap_on-speech_start,3))
                    search_from=max(search_from, found+max(1,len(bn)//2))
            if len(direct_drifts) >= max(1, min(3, len(cap_starts))):
                drifts.extend(direct_drifts)
        if len(drifts) < max(1, min(3, len(cap_starts))) and word_offsets:
            # 왜 이렇게 바꿨나 (2026-08-09):
            # 예전엔 대본 글자수를 그냥 누적해서 전사문의 같은 위치를 봤다.
            # 일레븐랩스가 "삼 주"를 "3주"로 읽는 식으로 글자수가 어긋나면
            # 그 오차가 뒤로 갈수록 쌓여서, 멀쩡한 영상이 싱크 2초 밀림으로 잡혔다.
            # (실측: YS 드리프트 0.15 → -1.26 → -2.42 로 증가 = 누적오차의 전형)
            # 이제는 difflib 로 대본↔전사문을 맞춰놓고 그 대응표로 위치를 찾는다. 누적이 없다.
            beat_norms_w=[_norm_kr(b.get("say","")) for b in beats]
            script_join_w="".join(beat_norms_w)
            _blocks=difflib.SequenceMatcher(None, script_join_w, heard).get_matching_blocks()
            def _map_pos(p):
                for bl in _blocks:
                    if bl.size and bl.a <= p < bl.a+bl.size:
                        return bl.b + (p - bl.a)
                nxt=[bl for bl in _blocks if bl.size and bl.a >= p]
                if nxt: return nxt[0].b
                prv=[bl for bl in _blocks if bl.size and bl.a < p]
                if prv:
                    bl=prv[-1]; return min(len(heard), bl.b + bl.size + (p - bl.a - bl.size))
                return p
            pos0=0
            for bi,b in enumerate(beats):
                bn=beat_norms_w[bi] if bi < len(beat_norms_w) else ""
                if not bn:
                    continue
                hp=_map_pos(pos0)
                speech_start=None
                for a,bend,st in word_offsets:
                    if bend > hp:
                        speech_start=st
                        break
                if speech_start is not None and bi < len(starts):
                    cap_on=intro_sec+starts[bi]+CAP_SYNC
                    drifts.append(round(cap_on-speech_start,3))
                pos0 += len(bn)
        seg_items=list(seg_items or [])
        if not drifts and seg_items:
            if stt_onset_offset>0.20:
                seg_items=[dict(item, start=float(item["start"])+stt_onset_offset) for item in seg_items]
            beat_norms=[_norm_kr(b.get("say","")) for b in beats]
            cum=[]; pos0=0
            for bn in beat_norms:
                cum.append((pos0, pos0+len(bn)))
                pos0 += len(bn)
            script_join="".join(beat_norms)
            search_from=0
            for item in seg_items:
                sn=_norm_kr(item.get("text",""))
                if not sn:
                    continue
                found=script_join.find(sn[:max(3,min(len(sn),18))], search_from)
                if found < 0:
                    found=script_join.find(sn[:max(3,min(len(sn),18))])
                if found < 0:
                    continue
                bi=next((k for k,(a,b) in enumerate(cum) if a <= found < b), None)
                if bi is None or bi>=len(starts):
                    continue
                speech_start=float(item["start"])
                if bi==0 and speech_start<0.30 and onset>0.50:
                    speech_start=onset
                cap_on=intro_sec+starts[bi]+CAP_SYNC
                drifts.append(round(cap_on-speech_start,3))
                search_from=max(search_from, found+max(1,len(sn)//2))
        if not drifts and seg_starts:
            seg_starts=[float(x) for x in (seg_starts or [])]
            for i,speech_start in enumerate(seg_starts[:min(len(starts), len(seg_starts))]):
                cap_on=intro_sec+starts[i]+CAP_SYNC
                drifts.append(round(cap_on-float(speech_start),3))

        if False and seg_drifts:
            drifts=seg_drifts

        gaps=[]
        for k in range(1,len(ws)):
            g=float(ws[k]["start"])-float(ws[k-1]["end"])
            if g>0.55 and not (ws[k-1]["text"] or "").rstrip().endswith((".","?","!")):
                gaps.append(round(g,2))

        # B방 게이트 정본: 자막 시작 시각과 세그먼트/단어 시작 시각의 평균 오차를 그대로 본다.
        # 후보만 골라 평균을 낮추거나 bias를 빼면 실제 싱크 불량을 통과시킬 수 있다.
        sync_bias=0.0
        if drifts:
            sd=sorted(drifts)
            mid=len(sd)//2
            sync_bias=sd[mid] if len(sd)%2 else (sd[mid-1]+sd[mid])/2.0
        avg=(sum(abs(x) for x in drifts)/len(drifts)) if drifts else 0.0
        mx=max((abs(x) for x in drifts), default=0.0)
        return {"read_ratio":round(ratio,3),"read_bad":bad[:6],
                "sync_drifts":drifts,"sync_avg":round(avg,3),"sync_max":round(mx,3),
                "sync_bias":round(sync_bias,3),
                "inner_gaps":gaps[:6],"heard_head":" ".join(w["text"] for w in ws)[:90],
                "segments":seg_count,
                "script_sentences":script_sentence_count,
                "voice_present_ok":voice_present_ok,
                "first_segment_start":round(first_segment_start,3),
                "stt_sync_ok":first_segment_start <= 1.20,
                "stt":"faster-whisper"}
    try:
        wav="/tmp/_audit_%d.wav"%(abs(hash(mp4))%10**8)
        _wav16k_from_media(mp4, wav)
        try:
            segs,ws=_stt_segments(wav)
            first_seg=float(segs[0].start) if segs else 0.0
            seg_starts=[float(seg.start) for seg in segs]
            seg_items=[{"text":seg.text or "", "start":float(seg.start)} for seg in segs]
            return _measure(ws, len(segs), first_seg, seg_starts, seg_items)
        except Exception as e:
            return {"audit":"faster_whisper_failed:%s"%type(e).__name__,
                    "stt":"faster-whisper","segments":0,
                    "script_sentences":_script_sentence_count(beats),
                    "voice_present_ok":False,"read_ratio":0.0,
                    "sync_drifts":[],"sync_avg":0.0,"sync_max":0.0,
                    "sync_bias":0.0,"inner_gaps":[],
                    "read_bad":[{"beat":0,"say":"stt failed","heard":"","r":0.0}],
                    "first_segment_start":0.0,"stt_sync_ok":False}
    except Exception as e:
        return {"audit":"unavailable:%s"%type(e).__name__,
                "stt":"faster-whisper","segments":0,
                "script_sentences":_script_sentence_count(beats),
                "voice_present_ok":False,"read_ratio":0.0,
                "sync_drifts":[],"sync_avg":0.0,"sync_max":0.0,
                "sync_bias":0.0,"inner_gaps":[],
                "read_bad":[{"beat":0,"say":"audit unavailable","heard":"","r":0.0}],
                "first_segment_start":0.0,"stt_sync_ok":False}

def main():
    job=json.load(open(sys.argv[1],encoding="utf-8"))
    FONT=resolve_font(job); TFONT=resolve_title_font(job); vid=job.get("voice_id","6bJjCjWVUcbkquC2mx6c")
    # ── 스캔 잡: 렌더 대신 Drive/로컬 영상 스캔해서 클립 대장(프레임) 생성 ──
    # 왜: 파일명만으론 원본 b롤 / 자막박힌 완성본 / 장면을 구분 못 함 → 대사에 맞는 화면 선택 불가(WHY 게이트)
    if job.get("scan"):
        sc=os.path.expanduser("~/atnown-content-pipeline/scripts/clip_scan.py")
        srcs=job["scan"] if isinstance(job["scan"],list) else [job["scan"]]
        catroot=os.path.expanduser(job.get("catalog_dir","~/atnown-content-pipeline/_clips_pool/_catalog"))
        res=[]
        for s in srcs:
            cd=os.path.join(catroot,(s.get("name") if isinstance(s,dict) else str(s))[:40].replace("/","_"))
            src=s.get("src") if isinstance(s,dict) else s
            r=subprocess.run([sys.executable,sc,src,cd,"--max",str(job.get("max_clips",15))],
                             capture_output=True,text=True,timeout=3600)
            res.append({"src":src,"rc":r.returncode,"tail":(r.stdout or r.stderr)[-300:]})
            _dl("SCAN %s rc=%d"%(src,r.returncode))
        msg={"PASS":all(x["rc"]==0 for x in res),"job":"scan","results":res,"catalog_dir":catroot}
        _dl("CHECKLIST "+json.dumps(msg,ensure_ascii=False)); print("CHECKLIST",json.dumps(msg,ensure_ascii=False))
        sys.exit(0 if msg["PASS"] else 1)

    # ── 셋업 잡: 본진 도구 설치(코덱스 CLI 등). 형이 디스코드/터미널에 손 안 대도 되게. ──
    # 워처 재시작 잡 — codex_watch가 시작 시 1회 캐싱한 경로를 갱신하려면 재기동이 필요.
    # 코워크는 마운트에서 launchctl을 못 쓴다(샌드박스) → 본진이 대신 실행. (2026-08-07)
    # 임의 진단 명령 실행(읽기 목적) — 코워크가 본진 CLI 도움말/버전을 실측하기 위함
    if job.get("probe_cmds"):
        rep=[]
        _pt=int(job.get("probe_timeout",120))     # 오래 걸리는 다운로드는 잡에서 늘린다
        for cmd in job["probe_cmds"]:
            try:
                r=subprocess.run(cmd,shell=True,capture_output=True,text=True,timeout=_pt,
                    env={**os.environ,"PATH":"/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:"+os.environ.get("PATH","")})
            except subprocess.TimeoutExpired:
                rep.append({"cmd":cmd,"rc":124,"out":"","err":"timeout %ds"%_pt}); continue
            rep.append({"cmd":cmd,"rc":r.returncode,"out":(r.stdout or "")[-1500:],"err":(r.stderr or "")[-600:]})
        msg={"PASS":True,"job":"probe_cmds","steps":rep}
        _dl("CHECKLIST "+json.dumps(msg,ensure_ascii=False)); print("CHECKLIST",json.dumps(msg,ensure_ascii=False))
        sys.exit(0)

    if job.get("restart_watcher"):
        import getpass
        rep=[]
        labels=job.get("labels") or ["com.atnown.codexwatch"]
        for lb in labels:
            for cmd in ["launchctl kickstart -k gui/$(id -u)/%s"%lb,
                        "launchctl list | grep %s || true"%lb]:
                r=subprocess.run(cmd,shell=True,capture_output=True,text=True,timeout=120,
                    env={**os.environ,"PATH":"/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:"+os.environ.get("PATH","")})
                rep.append({"cmd":cmd,"rc":r.returncode,"out":(r.stdout or "")[-200:],"err":(r.stderr or "")[-200:]})
        ok=any(x["rc"]==0 for x in rep)
        msg={"PASS":ok,"job":"restart_watcher","labels":labels,"steps":rep}
        _dl("CHECKLIST "+json.dumps(msg,ensure_ascii=False)); print("CHECKLIST",json.dumps(msg,ensure_ascii=False))
        sys.exit(0 if ok else 1)

    if job.get("setup_codex"):
        rep=[]
        def sh(cmd):
            r=subprocess.run(cmd,shell=True,capture_output=True,text=True,timeout=1800,
                             env={**os.environ,"PATH":"/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:"+os.environ.get("PATH","")})
            rep.append({"cmd":cmd,"rc":r.returncode,"out":(r.stdout or "")[-300:],"err":(r.stderr or "")[-300:]})
            return r
        sh("command -v codex || echo NO_CODEX")
        sh("command -v brew || echo NO_BREW")
        # npm 없으면 brew로 node 먼저 (실측 2026-08-06: 본진에 node 미설치라 npm not found)
        r=sh("command -v npm || echo NO_NPM")
        if "NO_NPM" in (r.stdout or ""):
            sh("brew install node")
        sh("npm i -g @openai/codex || sudo -n npm i -g @openai/codex || npm i -g @openai/codex --prefix ~/.npm-global")
        sh("command -v codex || ls -la ~/.npm-global/bin/codex 2>/dev/null || echo STILL_NO_CODEX")
        sh("(command -v codex && codex --version) || (~/.npm-global/bin/codex --version)")
        ok=any(("codex" in (x["out"] or "") and "NO_CODEX" not in (x["out"] or "")) for x in rep)
        msg={"PASS":ok,"job":"setup_codex","steps":rep}
        _dl("CHECKLIST "+json.dumps(msg,ensure_ascii=False)); print("CHECKLIST",json.dumps(msg,ensure_ascii=False))
        sys.exit(0 if ok else 1)

    # ── 탐색 잡: 맥에서 옵시디언 볼트 등 경로 찾기(연결폴더 밖은 코워크가 못 봄) ──
    if job.get("probe"):
        rep=[]
        def sh2(cmd):
            r=subprocess.run(cmd,shell=True,capture_output=True,text=True,timeout=600,
                             env={**os.environ,"PATH":"/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:"+os.environ.get("PATH","")})
            rep.append({"cmd":cmd,"rc":r.returncode,"out":(r.stdout or "")[-800:],"err":(r.stderr or "")[-200:]})
        # job["probe"] 가 리스트면 그 명령들을 실행(코워크가 원격 진단 가능). 아니면 기본 탐색.
        _pj=job.get("probe")
        if isinstance(_pj,list) and _pj:
            for _c in _pj[:12]: sh2(str(_c))
        else:
            sh2("ls -d ~/Library/Application\\ Support/obsidian 2>/dev/null || echo NO_OBSIDIAN_APP")
            sh2("cat ~/Library/Application\\ Support/obsidian/obsidian.json 2>/dev/null | head -c 900 || echo NO_JSON")
            sh2("find ~ -maxdepth 4 -name '.obsidian' -type d 2>/dev/null | head -5")
            sh2("ls ~/Documents ~/Desktop 2>/dev/null | head -30")
        msg={"PASS":True,"job":"probe","steps":rep}
        _dl("CHECKLIST "+json.dumps(msg,ensure_ascii=False)); print("CHECKLIST",json.dumps(msg,ensure_ascii=False))
        sys.exit(0)

    # ── 옵시디언 동기화 잡: 연결폴더의 문서를 볼트로 복사(폰에서도 보이게 iCloud 볼트) ──
    if job.get("mirror_vault"):
        # 드라이브 볼트(내용 있음) → iCloud 볼트(비어 있음) 미러링.
        # 형 볼트가 둘로 갈려 활성 볼트가 비어 있던 사고(2026-08-06) 해결.
        pass  # import shutil 제거 — 모듈 전역 사용 (UnboundLocalError 방지)
        src=os.path.expanduser(job.get("from","~/Library/CloudStorage/GoogleDrive-cksghrj22@gmail.com/내 드라이브/앳나운_옵시디언_볼트"))
        dst=os.path.expanduser(job.get("to","~/Library/Mobile Documents/iCloud~md~obsidian/Documents/앳나운_옵시디언_볼트"))
        rep={"from":src,"to":dst,"src_exists":os.path.isdir(src),"dst_exists":os.path.isdir(dst),"copied":0,"skipped":0}
        if rep["src_exists"] and rep["dst_exists"]:
            for root,dirs,files in os.walk(src):
                dirs[:]=[d for d in dirs if not d.startswith(".")]
                rel=os.path.relpath(root,src)
                od=os.path.join(dst,rel) if rel!="." else dst
                os.makedirs(od,exist_ok=True)
                for f in files:
                    if not f.lower().endswith((".md",".txt")): continue
                    sp=os.path.join(root,f); dp=os.path.join(od,f)
                    try:
                        if os.path.exists(dp) and os.path.getmtime(dp)>=os.path.getmtime(sp):
                            rep["skipped"]+=1; continue
                        shutil.copy2(sp,dp); rep["copied"]+=1
                    except Exception: pass
        rep["PASS"]=rep["src_exists"] and rep["dst_exists"]
        _dl("CHECKLIST "+json.dumps(rep,ensure_ascii=False)); print("CHECKLIST",json.dumps(rep,ensure_ascii=False))
        sys.exit(0 if rep["PASS"] else 1)

    if job.get("sync_obsidian"):
        vault=os.path.expanduser(job.get("vault",
              "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/앳나운_옵시디언_볼트"))
        srcd=os.path.expanduser(job.get("src","~/atnown-content-pipeline/_obsidian_out"))
        sub=job.get("subfolder","앳나운_파이프라인")
        dst=os.path.join(vault,sub)
        rep={"vault_exists":os.path.isdir(vault),"src_exists":os.path.isdir(srcd),"copied":[],"dst":dst}
        if rep["vault_exists"] and rep["src_exists"]:
            os.makedirs(dst,exist_ok=True)
            pass  # import shutil 제거 — 모듈 전역 사용 (UnboundLocalError 방지)
            for root,_,files in os.walk(srcd):
                rel=os.path.relpath(root,srcd)
                out_dir=os.path.join(dst,rel) if rel!="." else dst
                os.makedirs(out_dir,exist_ok=True)
                for f in files:
                    if f.lower().endswith((".md",".txt",".png",".jpg")):
                        shutil.copy2(os.path.join(root,f),os.path.join(out_dir,f))
                        rep["copied"].append(os.path.join(rel,f) if rel!="." else f)
        rep["PASS"]=bool(rep["copied"])
        _dl("CHECKLIST "+json.dumps(rep,ensure_ascii=False)); print("CHECKLIST",json.dumps(rep,ensure_ascii=False))
        sys.exit(0 if rep["PASS"] else 1)

    # ── 옵시디언 역방향: 형이 쓴 노트를 연결폴더로 끌어온다(코워크가 읽고 보이스 학습) ──
    if job.get("pull_obsidian"):
        vault=os.path.expanduser(job.get("vault",
              "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/앳나운_옵시디언_볼트"))
        dst=os.path.expanduser(job.get("dst","~/atnown-content-pipeline/_obsidian_in"))
        days=int(job.get("days",30)); maxn=int(job.get("max_files",200))
        rep={"vault":vault,"copied":[],"skipped_big":0,"skipped":0,"skip_sample":[]}
        if os.path.isdir(vault):
            os.makedirs(dst,exist_ok=True)
            import time as _t  # shutil은 모듈 전역 사용 (지역 import 시 UnboundLocalError)
            cutoff=_t.time()-days*86400
            got=0
            for root,dirs,files in os.walk(vault):
                dirs[:]=[d for d in dirs if not d.startswith(".")]   # .obsidian 등 제외
                for f in files:
                    if not f.lower().endswith(".md"): continue
                    src=os.path.join(root,f)
                    try:
                        st=os.stat(src)
                        if st.st_mtime<cutoff: continue
                        if st.st_size>400000: rep["skipped_big"]+=1; continue
                    except Exception: continue
                    rel=os.path.relpath(root,vault)
                    od=os.path.join(dst,rel) if rel!="." else dst
                    os.makedirs(od,exist_ok=True)
                    out_rel=os.path.join(rel,f) if rel!="." else f
                    try:
                        shutil.copy2(src,os.path.join(od,f))
                    except OSError as e:
                        rep["skipped"]+=1
                        if len(rep["skip_sample"])<5:
                            rep["skip_sample"].append({"file":out_rel,"error":str(e)})
                        continue
                    rep["copied"].append(out_rel)
                    got+=1
                    if got>=maxn: break
                if got>=maxn: break
        rep["count"]=len(rep["copied"]); rep["PASS"]=os.path.isdir(vault)
        _dl("CHECKLIST "+json.dumps(rep,ensure_ascii=False)[:1500]); print("CHECKLIST",json.dumps(rep,ensure_ascii=False)[:1500])
        sys.exit(0 if rep["PASS"] else 1)

    # ── 셋업 잡: Remotion 설치·검증 (개념애니형 폼에 필요) ──
    if job.get("setup_remotion"):
        rep=[]
        def sh3(cmd,cwd=None):
            r=subprocess.run(cmd,shell=True,capture_output=True,text=True,timeout=2400,cwd=cwd,
                env={**os.environ,"PATH":"/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:"+os.environ.get("PATH","")})
            rep.append({"cmd":cmd,"rc":r.returncode,"out":(r.stdout or "")[-300:],"err":(r.stderr or "")[-300:]})
            return r
        REM=os.path.expanduser("~/atnown-content-pipeline/remotion")
        sh3("command -v node && node -v")
        sh3("npm install --no-audit --no-fund", cwd=REM)
        r=sh3("npx --yes remotion versions", cwd=REM)
        ok = r.returncode==0 or os.path.isdir(os.path.join(REM,"node_modules"))
        msg={"PASS":bool(ok),"job":"setup_remotion","node_modules":os.path.isdir(os.path.join(REM,"node_modules")),"steps":rep}
        _dl("CHECKLIST "+json.dumps(msg,ensure_ascii=False)[:1200]); print("CHECKLIST",json.dumps(msg,ensure_ascii=False)[:1200])
        sys.exit(0 if ok else 1)

    mode=job.get("mode","clips"); beats=job["beats"]; out=job["out"]; cdir=job.get("clips_dir","")
    vault_hits, vault_warn = vault_hits_for_job(job, beats)
    if vault_hits:
        _dl("VAULT_HITS "+", ".join(vault_hits))
    else:
        _dl("VAULT_HITS none"+((" warn="+vault_warn) if vault_warn else ""))
    WK="/tmp/rfj_%d"%(abs(hash(out))%10**12); os.makedirs(WK,exist_ok=True)
    _dl("FONT=%s mode=%s beats=%d (연속TTS)"%(FONT,mode,len(beats)))
    thumb_enabled = bool(job.get("thumb", True))
    thumb_text=(job.get("thumb_text") if job.get("thumb_text") is not None else auto_thumb_text(beats[0].get("say","") if beats else "")).strip()
    thumb_lines=[ln for ln in thumb_text.splitlines()] or [thumb_text]
    thumb_render_text=re.sub(r"\s+"," ",thumb_lines[0]).strip()
    thumb_png,_,_=make_thumb_png(thumb_render_text,"%s/thumb.png"%WK,FONT)
    thumb_overlay_added=False

    # auto_clips: 본진이 Drive에서 받은 클립을 비트에 자동 배정(반복금지 규칙 자동 준수).
    # 클립 이름을 job에 안 적어도 됨. 서로 다른 클립을 1:1로 깔고, 부족하면 규칙대로 순환.
    # 주제 클립 자동 수급: job에 drive_ids_file 있으면 렌더 전에 본진이 직접 내려받는다.
    # (코덱스 CLI 없이도 돌아야 함 — 실측: codex 미설치로 태스크가 대기만 함 2026-08-06)
    dif=os.path.expanduser(job.get("drive_ids_file","") or "")
    if dif and os.path.exists(dif) and cdir:
        os.makedirs(cdir,exist_ok=True)
        have=[f for f in os.listdir(cdir) if f.lower().endswith((".mov",".mp4",".m4v",".avi"))]
        if len(have)<int(job.get("min_clips",3)):
            puller=os.path.expanduser("~/atnown-content-pipeline/scripts/drive_pull_ids.py")
            if os.path.exists(puller):
                r=subprocess.run([sys.executable,puller,dif,cdir],capture_output=True,text=True,timeout=1800)
                _dl("DRIVE_PULL_IDS rc=%d out=%s"%(r.returncode,(r.stdout or r.stderr)[-400:]))
    if job.get("auto_clips") and mode=="clips" and cdir and os.path.isdir(cdir):
        vids=sorted([f for f in os.listdir(cdir) if f.lower().endswith((".mov",".mp4",".m4v",".avi"))])
        _dl("auto_clips: 클립 %d개 발견 → 비트 %d개에 배정"%(len(vids),len(beats)))
        if not vids:
            # 클립 0개면 조용히 KeyError로 죽지 말고 명확히 실패(실측 사고 2026-08-06: JPG만 받힘)
            msg={"PASS":False,"reason":"auto_clips인데 clips_dir에 영상 0개","clips_dir":cdir,
                 "hint":"drive_pull이 영상을 못 받았는지 확인(이미지만 받힘?)","out":out}
            _dl("CHECKLIST "+json.dumps(msg,ensure_ascii=False)); print("CHECKLIST",json.dumps(msg,ensure_ascii=False))
            sys.exit(1)
        # 클립-주제 일치 게이트(형 지시 2026-08-06: 개츠비 b롤에 겉매직 설명 = 실격)
        # topic_keywords 가 있으면, 파일명에 그 키워드가 있는 클립만 쓴다. 하나도 없으면 즉시 실패.
        tk=[k for k in (job.get("topic_keywords") or []) if k]
        if tk:
            matched=[f for f in vids if any(k in f for k in tk)]
            if not matched:
                msg={"PASS":False,"reason":"클립-주제 불일치: 주제 키워드에 맞는 클립이 0개",
                     "topic_keywords":tk,"clips_dir":cdir,"pool":vids[:12],
                     "hint":"주제 전용 클립을 Drive에서 받아 clips_dir에 채울 것","out":out}
                _dl("CHECKLIST "+json.dumps(msg,ensure_ascii=False)); print("CHECKLIST",json.dumps(msg,ensure_ascii=False))
                sys.exit(1)
            _dl("topic gate: %d/%d 클립이 주제와 일치"%(len(matched),len(vids)))
            vids=matched
        # 내용 중복 제거: 이름만 다른 같은 영상(예: 'IMG_0069.mov' vs 'IMG_0069 2.mov')이
        # 반복 게이트를 통과해 같은 장면이 연속 노출되던 사고(형 지적 2026-08-06) 차단.
        uniq=[]; sigs=set()
        for f in vids:
            sg=clip_sig(os.path.join(cdir,f))
            if sg in sigs: _dl("dup-content skip: %s"%f); continue
            sigs.add(sg); uniq.append(f)
        if uniq: vids=uniq
        _dl("auto_clips: 내용중복 제거 후 %d개"%len(vids))
        # 최근 편에서 쓴 클립은 뒤로 미뤄 신선한 것부터 배정(영상 간 중복 방지)
        if job.get("avoid_recent",True):
            rc_used=recent_clips(int(job.get("avoid_last",3)))
            fresh=[f for f in vids if f not in rc_used]
            stale=[f for f in vids if f in rc_used]
            if fresh: vids=fresh+stale
            _dl("avoid_recent: 신선 %d / 최근사용 %d"%(len(fresh),len(stale)))
        vi=0
        for i,b in enumerate(beats):
            if b.get("black"): continue          # 검은 정리카드/CTA는 클립 불필요
            b["clip"]=vids[vi % len(vids)]; vi+=1
    # 클립 키 누락 방어(수동 잡에서 빠졌을 때도 죽지 않게)
    if mode=="clips":
        missing=[i for i,b in enumerate(beats) if not b.get("clip") and not b.get("black")]
        if missing:
            msg={"PASS":False,"reason":"beats에 clip 지정 누락","beats_missing":missing,
                 "hint":"job에 clip을 적거나 auto_clips:true + 클립 폴더 준비","out":out}
            _dl("CHECKLIST "+json.dumps(msg,ensure_ascii=False)); print("CHECKLIST",json.dumps(msg,ensure_ascii=False))
            sys.exit(1)

    # BGM 자동선택(형 지시: 취향도 묻지 말고 분위기에 맞게 내가 고른다)
    # job.bgm_file 명시 없으면 mood/제목으로 assets/bgm에서 고름.
    if job.get("bgm",True) and not job.get("bgm_file"):
        bdir=os.path.expanduser(job.get("bgm_dir","~/atnown-content-pipeline/assets/bgm"))
        if os.path.isdir(bdir):
            pool=sorted([os.path.join(bdir,f) for f in os.listdir(bdir) if f.lower().endswith((".mp3",".wav",".m4a"))])
            if pool:
                mood=(job.get("mood") or "").strip()
                # NOTE: 변수명 key 금지 — API 키(key)를 덮어써서 헤더 인코딩 폭발했던 실측 버그(2026-08-06)
                kw={"잔잔":"산책","따뜻":"산책","정보":"산책","경쾌":"Ready","활기":"Ready","감성":"좋아해"}.get(mood,"")
                pick=next((p for p in pool if kw and kw in os.path.basename(p)), pool[0])
                job["bgm_file"]=pick; _dl("BGM_AUTO mood=%s → %s"%(mood or "기본",os.path.basename(pick)))

    # ── STAGE A: 비트별 TTS 캐시 + 연속 보이스 병합 + 비트별 시간창 산출 ──
    # 같은 문장은 캐시에서 재사용하고, 비트 사이엔 break 태그 기준의 정해진 호흡을 넣는다.
    # 병합 alignment에는 break 태그 문자를 포함해 full text와 char↔time 매핑을 유지한다.
    brk=job.get("beat_pause",0.35)
    sep=' <break time="%.2fs" /> '%brk
    tts_texts=[]; full=""; bounds=[]
    for i,b in enumerate(beats):
        say=rhyme_prep(b["say"], job.get("pron_dict"))
        tts_texts.append(say)
        if i>0:
            full+=sep
        s=len(full); full+=say; bounds.append((s,len(full)))
    if job.get("local_tts"):
        key=""
        al=tts_ts_local(full, "%s/voice.mp3"%WK)
    else:
        cfg=eleven_config(job,vid)
        key=cfg["api_key"]; vid=cfg["voice_id"]
        tts_preflight(tts_texts,cfg)
        al=tts_ts_batch(tts_texts, "%s/voice.mp3"%WK, key, vid, cfg["model_id"], cfg["voice_settings"], brk)
    if os.path.getsize("%s/voice.mp3"%WK) < TTS_MIN_BYTES:
        raise RuntimeError("TTS 결과 파일 크기 비정상: voice.mp3 bytes=%d"%os.path.getsize("%s/voice.mp3"%WK))
    if clen("%s/voice.mp3"%WK) < 0.5:
        raise RuntimeError("TTS 결과 길이 비정상: voice.mp3 duration=%.3f"%clen("%s/voice.mp3"%WK))
    chars=al["characters"]; cs=al["character_start_times_seconds"]; ce=al["character_end_times_seconds"]
    nC=len(cs)
    def scale(idx):
        if nC==len(full) or not full: return idx
        return int(round(idx/max(1,len(full))*nC))
    def t_start(i): j=min(max(scale(i),0),nC-1); return cs[j]
    def t_end(i): j=min(max(scale(i)-1,0),nC-1); return ce[j]
    audioEnd=ce[-1] if ce else clen("%s/voice.mp3"%WK)

    # ── 실시간 자막(live caption) ──
    # 형 지시(2026-08-06): "말에 따라 텍스트가 실시간으로. 완전히 함축하면 가시성 떨어진다."
    # 말한 그대로를 단어 타이밍에 맞춰 조각내서, 말하는 순간에 자막이 넘어가게 한다.
    def words_in(a,b_):
        """문자 구간 [a,b_) 안의 단어와 타이밍"""
        ws=[];cur="";s0=None;e0=None
        for idx in range(a,min(b_,len(full))):
            ch=full[idx]; j=min(max(scale(idx),0),nC-1)
            if ch.isspace():
                if cur: ws.append((cur,s0,e0)); cur=""
            else:
                if not cur: s0=cs[j]
                cur+=ch; e0=ce[j]
        if cur: ws.append((cur,s0,e0))
        return ws
    NUMW={"한","두","세","네","다섯","여섯","일곱","여덟","아홉","열","반","절반","몇"}
    UNIT={"배","가지","번","개","분","시간","달","주","년","살","명","줄","cm","센치"}
    def _clean(w): return w.strip(" ,.!?~")
    def chunk_words(ws,max_chars=15,max_words=5):
        """의미 단위로 자른다. 글자수로만 자르면 '두 / 배', '네 / 가지'처럼
        숫자와 단위가 갈라져 읽기 어렵다(형 지적 2026-08-06)."""
        out=[];cur=[];n=0
        for idx,w in enumerate(ws):
            wl=len(w[0])
            # 문장이 끝나면(? ! .) 무조건 끊는다 — "전체가 문제인가요? 한 곳이 문제인가요?"가
            # 한 자막에 붙어 한 문장으로 안 읽히던 문제(형 지적 2026-08-06)
            if cur and cur[-1][0].rstrip().endswith(("?","!",".")):
                out.append(cur); cur=[]; n=0
            over = cur and (n+wl+1>max_chars or len(cur)>=max_words)
            if over and w[0].rstrip().endswith(("?","!",".")) and (n+wl+1)<=max_chars+6:
                over=False          # 문장 마지막 단어는 앞과 붙인다(꼬리 한 조각 방지)
            if over:
                prev=_clean(cur[-1][0]); nxt=_clean(w[0])
                # 숫자 뒤에서는 끊지 않는다: '두 배예요', '네 가지만'(조사가 붙어도 안전)
                if prev in NUMW: over=False
                # 단위로 시작하는 조각(= 앞 조각의 꼬리)도 붙여둔다
                elif any(nxt.startswith(u) for u in UNIT): over=False
            if over:
                out.append(cur); cur=[]; n=0
            cur.append(w); n+=wl+1
        if cur: out.append(cur)
        # 고아 조각 정리: 너무 짧은 조각(1단어·3자 이하)은 앞 조각에 합친다
        merged=[]
        for c in out:
            txt="".join(_clean(x[0]) for x in c)
            if merged and (len(c)==1 and len(txt)<=3):
                merged[-1]=merged[-1]+c
            else:
                merged.append(c)
        # 마지막 조각이 짧으면 앞과 합침(문장 끝 '배.' 같은 꼬리 방지)
        if len(merged)>=2:
            last="".join(_clean(x[0]) for x in merged[-1])
            if len(last)<=3: merged[-2]=merged[-2]+merged[-1]; merged.pop()
        return [{"text":" ".join(x[0] for x in c),"s":c[0][1],"e":c[-1][2]} for c in merged]

    b_start=[t_start(bounds[i][0]) for i in range(len(beats))]
    try:
        ws_bound=_stt_words("%s/voice.mp3"%WK, os.environ.get("BOUNDARY_FW_MODEL","large-v3-turbo"))
        counts=[]
        for b in beats:
            toks=[x for x in re.split(r"\s+", rhyme_prep(b["say"], job.get("pron_dict")).strip()) if _norm_kr(x)]
            counts.append(max(1,len(toks)))
        if len(ws_bound)>=max(5, sum(counts)*0.70):
            fixed=[]; pos=0
            for cnt in counts:
                if pos < len(ws_bound):
                    fixed.append(float(ws_bound[pos]["start"]))
                else:
                    fixed.append(b_start[len(fixed)])
                pos += cnt
            # STT 기반 경계가 단조 증가할 때만 채택한다. 실패하면 기존 문자 타임라인을 쓴다.
            if all(fixed[i] <= fixed[i+1] for i in range(len(fixed)-1)):
                b_start=fixed
                _dl("BOUNDARY_STT starts=%s"%[round(x,2) for x in b_start])
    except Exception as e:
        _dl("BOUNDARY_STT_FAIL %s"%type(e).__name__)
    # 첫 비트는 0부터 노출(리드 침묵도 자막 깔림), 이후는 각 비트 발화 시작에서 전환
    starts=[0.0]+[b_start[i] for i in range(1,len(beats))]
    tail=float(job.get('tail_sec',1.3))   # 마지막 문장 뒤 여유. 0.6초는 말 끝나자마자 아웃트로가 튀어나온다(형 지적 2026-08-09)
    ends=[starts[i+1] for i in range(len(beats)-1)]+[audioEnd+tail]
    # 프레임 격자에 비트 경계를 고정한다(형 지적 2026-08-08 "자막이랑 음성이 너무 안 맞는다").
    # 왜: durs가 소수였고 비트마다 -t로 인코딩하면 프레임 반올림 오차가 비트마다 생긴다.
    #     10비트면 최대 0.3초가 쌓여 뒤로 갈수록 음성과 벌어졌다. 격자에 고정하면 누적이 사라진다.
    _bf=[int(round(x*FPS)) for x in starts]+[int(round((audioEnd+tail)*FPS))]
    # 2026-08-10 실측: S7의 컷 길이가 4.4 · **1.6** · 5.6 · **1.6** · 3.9 · **1.6** … 였다.
    # 1.6초짜리는 전부 검정 카드다. min_beat 바닥값에 그대로 붙어 있었다.
    # 두 줄짜리 카드를 1.6초에 읽을 수 없다. 스쳐 지나간다 —
    # 형이 "컷 넘어가는 속도가 너무 빠르다"고 한 것의 정체가 B롤이 아니라 이거였다.
    # 그래서 바닥값을 비트 종류별로 나눈다: 글자만 있는 화면은 읽을 시간이 필요하다.
    if job.get("enforce_min_beat"):
        MINBEAT=float(job.get("min_beat",2.4))      # 클립 비트
        MINCARD=float(job.get("min_card",3.2))      # 검정/카드 비트 — 오디오 재타이밍 잡에서만 사용
        def _floor(i):
            b=beats[i] if i < len(beats) else {}
            return MINCARD if (b.get("black") or b.get("card")) else MINBEAT
        _bf=[_bf[0]]+[max(_bf[k], _bf[k-1]+int(_floor(k-1)*FPS)) for k in range(1,len(_bf))]
    durs=[(_bf[i+1]-_bf[i])/float(FPS) for i in range(len(beats))]
    starts=[f/float(FPS) for f in _bf[:len(beats)]]
    _dl("audioEnd=%.2f durs=%s"%(audioEnd,[round(x,2) for x in durs]))

    # SIM1: 클립 윈도우 맞춤 + 창 중복 검사
    wins={}
    for i,b in enumerate(beats):
        if mode=="clips" and not b.get("black"):
            src=os.path.join(cdir,b["clip"]); cl=clen(src); bd=durs[i]
            if job.get("smart_start",True):
                ss=pick_start(src,bd,float(b.get("start",0.3) or 0.3)); b["start"]=ss
            else:
                ss=float(b.get("start",0))
            if cl>0 and ss+bd>cl+0.05: ss=max(0.0,cl-bd-0.1); b["start"]=ss
            wins.setdefault(b["clip"],[]).append(round(ss,1))
    # 같은 클립을 같은 지점에서 두 번 쓰는 것만 잡는다.
    # 붙어 있는 비트가 이어보기로 같은 창을 쓰는 건 정상이므로 인접쌍은 제외한다.
    _adj=set()
    for _i in range(len(beats)-1):
        if beats[_i].get("clip") and beats[_i].get("clip")==beats[_i+1].get("clip"):
            _adj.add(beats[_i]["clip"])
    dups=[k for k,v in wins.items() if len(v)!=len(set(v)) and k not in _adj]

    # ── STAGE B: 영상 (PIL 자막 PNG + overlay) ──
    csz=70 if mode=="clips" else 76
    parts=[]
    LIVE=job.get("live_caption",True)
    for i,b in enumerate(beats):
        bd=durs[i]; v="%s/v%d.mp4"%(WK,i)
        _boxes=[]          # (y0,y1,t0,t1,label) — 같은 시간·같은 세로영역에 두 글자가 겹치면 사고다
        # 자막 조각: LIVE면 말한 그대로를 단어타이밍으로 쪼갬(실시간), 아니면 기존 고정 자막
        segs=[]
        if LIVE:
            ws=words_in(bounds[i][0],bounds[i][1])
            cks=chunk_words(ws)
            for ci,c in enumerate(cks):
                rs=0.0 if ci==0 else max(0.0,c["s"]-starts[i])   # 첫 조각은 비트 시작부터(빈 화면 방지)
                segs.append([c["text"],rs,0.0])
            # 겹침 금지: 각 조각은 다음 조각 시작 직전까지만(두 줄 동시노출 방지)
            # 글자가 다 보이기 전에 넘어가면 안 된다(형 지적 2026-08-09).
            # 최소 1.0초 + 글자당 0.07초는 화면에 남긴다.
            for ci in range(len(segs)):
                nxt=segs[ci+1][1] if ci+1<len(segs) else bd
                need=max(1.0, 0.07*len(segs[ci][0]))
                segs[ci][2]=min(max(segs[ci][1]+0.20, segs[ci][1]+need), nxt-0.02, bd)
                segs[ci][2]=min(segs[ci][2], bd)
            segs=[(t,s_,e_) for t,s_,e_ in segs]
        if not segs:
            segs=[(b.get("cap","").replace("|"," "),0.0,bd)]
        inps=[]; ovl=""
        BLACK=bool(b.get("black"))          # 검은 화면 + 텍스트만 (정리 카드 / CTA)
        if mode=="clips" and not BLACK:
            src=os.path.join(cdir,b["clip"])
            inp=["-ss","%.3f"%max(0.0,float(b.get("start",0) or 0)),"-t","%.3f"%float(bd),"-i",src]  # 지수표기(8.3e-17) 방지
            if job.get("tone_ref"):
                wbf=tone_match_filter(src, tone_ref_profile(job, cdir))
            elif job.get("auto_wb",True):
                wbf=wb_filter(src, float(b.get("start",0))+bd/2.0)
            else:
                wbf=""
            if i==0: _dl("WB beat0: %s"%(wbf or "none"))
            base="[0]crop=iw:ih*0.92:0:0,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1%s[bg]"%((","+wbf) if wbf else "")
            cur="[bg]"
        else:
            inp=["-f","lavfi","-i","color=c=black:s=1080x1920:d=%.2f"%bd]
            base="[0]null[bg]"; cur="[bg]"
        idx=1
        # 사진 콜라주(최대 4장) — b롤 위에 얹는 부연 배열
        phs=b.get("photos") or []
        if phs:
            pdir=job.get("photos_dir","")
            paths=[(p_ if os.path.isabs(p_) else os.path.join(pdir,p_)) for p_ in phs]
            paths=[p_ for p_ in paths if os.path.exists(p_)]
            if paths:
                cpng="%s/col%d.png"%(WK,i)
                make_collage_png(paths,cpng,layout=b.get("photo_layout", job.get("photo_layout","story")))
                inp+=["-i",cpng]
                ps=float(b.get("photos_in",0.0)); pe=float(b.get("photos_out",bd))
                ovl+=";%s[%d]overlay=0:0:enable='between(t,%.2f,%.2f)'[opc]"%(cur,idx,ps,min(pe,bd))
                cur="[opc]"; idx+=1
                _dl("COLLAGE beat%d: %d장"%(i,len(paths)))
        # 자유 텍스트 박스(낙타식) — 화면과 무관한 하고 싶은 말도 가능
        for ni,nt in enumerate(b.get("notes") or []):
            npng,nw,nh=make_note_png(nt.get("text",""),"%s/note%d_%d.png"%(WK,i,ni),
                                     TFONT or FONT, int(nt.get("size",52)), nt.get("style","white"))
            nx=nt.get("x","center"); ny=int(nt.get("y",420))
            xexpr="(W-w)/2" if nx=="center" else str(int(nx))
            inp+=["-i",npng]
            ns=float(nt.get("in",0.0)); ne=float(nt.get("out",bd))
            ovl+=";%s[%d]overlay=%s:%d:enable='between(t,%.2f,%.2f)'[on%d]"%(cur,idx,xexpr,ny,ns,min(ne,bd),ni)
            cur="[on%d]"%ni; idx+=1
        # 정리 카드: 검은 화면에 항목 리스트를 통째로(비트 내내) 노출
        card=b.get("card")
        if BLACK and card:
            cpng,cw,ch=make_text_png(list(card),"%s/card%d.png"%(WK,i),TFONT or FONT,64,box_alpha=0)
            inp+=["-i",cpng]
            _cy=560                      # 카드는 항상 상단 고정
            _boxes.append((_cy,_cy+ch,0.0,bd,"card"))
            ovl+=";%s[%d]overlay=(W-w)/2:%d[oc]"%(cur,idx,_cy); cur="[oc]"; idx+=1
        # 비트별 자막 강조(형 지시 2026-08-07): 2층 키워드는 화면을 바꾸지 말고
        # 글자 크기 / 위치로 때린다. cap_scale=1.4 · cap_pos="center" 처럼 비트에 지정.
        bcsz = int(round(csz*float(b.get("cap_scale",1.0))))
        bpos = b.get("cap_pos")
        # 2026-08-09 형 지시("한 화면에 둘까지"·"카드랑 자막이 겹친다"):
        # 검정 화면에 카드가 떠 있으면 카드가 그 비트의 메시지다. 자막을 겹쳐 쓰지 않는다.
        # 예전엔 카드 아래에 같은 말을 큰 글자로 또 써서, 두 글자가 따로 노는 화면이 나왔다.
        if BLACK and card:
            segs=[]
        for si,(txt,s_,e_) in enumerate(segs):
            # 싱크 보정(형 지적 2026-08-08): 오디오는 adelay=lead_ms(140ms+intro)만큼 밀리는데
            # 자막은 목소리 원점(t=0) 기준이라 딱 140ms 먼저 떴다. 같은 값만큼 자막도 민다.
            cs_,ce_ = s_+CAP_SYNC, min(e_+CAP_SYNC, bd)
            if i==0 and thumb_enabled:
                cs_=max(cs_, THUMB_DUR)
                if ce_<=cs_:
                    continue
            useblack = BLACK or mode!="clips"
            png,cw,ch=make_text_png([txt],"%s/cap%d_%d.png"%(WK,i,si),FONT,bcsz,box_alpha=0 if useblack else 150)
            if mode=="clips" and not BLACK:
                # 카드 없는 클립 비트에서는 자막 y를 전역 상수로 고정한다.
                # cap_pos/cap_scale은 강조용으로 남기되, 같은 편 안에서 y가 중앙으로 튀면
                # B방 검수 기준상 실패다.
                oy=int(job.get("caption_y", job.get("clip_caption_y", 1580)))
            elif bpos=="center":   oy=int((1920-ch)/2)
            elif bpos=="upper":  oy=int(1920*0.34)
            elif isinstance(bpos,(int,float)): oy=int(bpos)
            elif BLACK and card: oy=1920-ch-260          # (아래에서 이 비트는 자막을 아예 그리지 않는다)
            elif useblack:     oy=int((1920-ch)/2)          # 검정 단독이면 항상 화면 정가운데 — 높이가 튀지 않게
            elif job.get("caption_center"): oy=int((1920-ch)/2)   # 에세이형: 가운데 자막
            else:              oy=1920-ch-150
            inp+=["-i",png]
            nxt="[o%d]"%si
            _boxes.append((oy,oy+ch,cs_,ce_,"cap"))
            if si==0: CAP_TRACE.append({"beat":i,"black":bool(BLACK),"card":bool(card),
                                        "oy":int(oy),"ch":int(ch),"txt":txt[:14]})
            ovl+=";%s[%d]overlay=(W-w)/2:%d:enable='between(t,%.2f,%.2f)'%s"%(cur,idx,oy,cs_,ce_,nxt)
            cur=nxt; idx+=1
        fc=base+ovl; last=cur
        if i==0 and job.get("title"):
            # 타이틀: 크고 두꺼운 프리텐다드(형 지시). 두께감 위해 살짝 겹쳐 그림.
            tsz=int(job.get("title_size",92))
            t_png,tw,th=make_text_png(job["title"].split("|"),"%s/ttl.png"%WK,TFONT or FONT,tsz,
                                      color=(255,255,255,255),box_alpha=0,pad=26,bold=True)
            _ty=int(job.get("title_y",210))
            title_start=THUMB_DUR if thumb_enabled else 0.0
            # 제목을 첫 비트 내내 남기면 첫 라이브 자막과 동시에 떠 겹침 사고가 난다.
            # B방 정본: 제목은 도입 신호, 자막은 발화 신호. 제목은 짧게 빠진다.
            title_end=min(bd, title_start+float(job.get("title_hold_sec",0.85) or 0.85))
            _boxes.append((_ty,_ty+th,title_start,title_end,"title"))
            inp+=["-i",t_png]; fc+=";%s[%d]overlay=(W-w)/2:%d:enable='between(t,%.2f,%.2f)'[ttl]"%(last,idx,_ty,title_start,title_end); last="[ttl]"
            idx+=1
        if i==0 and thumb_enabled:
            inp+=["-i",thumb_png]
            fc+=";%s[%d]overlay=(W-w)/2:%d:enable='between(t,0,%.2f)'[thumb]"%(last,idx,THUMB_Y,THUMB_DUR)
            last="[thumb]"; thumb_overlay_added=True
        # ── 레이아웃 충돌 검사(형 지시 2026-08-08 "무조건 자기치료로 고쳐놔") ──
        # 같은 시간대에 세로영역이 겹치는 글자 레이어가 있으면 화면이 깨진다.
        # 눈으로 잡지 말고 빌드 단계에서 잡는다. 겹치면 기록하고, 자막을 겹치지 않는 곳으로 밀어낸다.
        for _a in range(len(_boxes)):
            for _b2 in range(_a+1,len(_boxes)):
                A=_boxes[_a]; B=_boxes[_b2]
                if A[3]<=B[2] or B[3]<=A[2]: continue          # 시간이 안 겹침
                if A[1]<=B[0] or B[1]<=A[0]: continue          # 세로가 안 겹침
                LAYOUT_HITS.append({"beat":i,"a":A[4],"b":B[4],
                                    "ay":[A[0],A[1]],"by":[B[0],B[1]],
                                    "t":[round(max(A[2],B[2]),2),round(min(A[3],B[3]),2)]})
        _nf=max(1,int(round(bd*FPS)))   # -t 대신 정확한 프레임 수로 잘라야 길이가 안 흔들린다
        subprocess.run(["ffmpeg","-y"]+inp+["-filter_complex",fc,"-map",last,"-frames:v",str(_nf),"-r",str(FPS),"-an","-pix_fmt","yuv420p","-preset","fast","-crf","16",v],capture_output=True)
        if not os.path.exists(v):
            r2=subprocess.run(["ffmpeg","-y"]+inp+["-filter_complex",fc,"-map",last,"-t",str(bd),"-r",str(FPS),"-an","-pix_fmt","yuv420p","-preset","fast","-crf","16",v],capture_output=True)
            if not os.path.exists(v): _dl("SEG%d_FAIL: %s"%(i,r2.stderr.decode('utf-8','ignore')[-500:]))
        parts.append(v)
    # 인트로 카드(맨 앞)는 명시적으로 separate_intro=true일 때만 쓴다.
    # B방 정본은 첫 클립 위 제목 오버레이 + 첫 발화 1.2초 이내다. intro_sec만 보고
    # 앞에 영상을 삽입하고 보이스를 미루면, 재렌더 때 첫 발화가 1.8초대로 밀린다.
    intro_sec=float(job.get("intro_sec",0) or 0)
    separate_intro=bool(job.get("separate_intro"))
    effective_intro_sec=intro_sec if (separate_intro and intro_sec>0.3) else 0.0
    if effective_intro_sec>0.3 and beats:
        iv="%s/vi.mp4"%WK
        # 타이틀: 크고 두꺼운 프리텐다드(형 지시)
        it_png,_,_=make_text_png((job.get("title") or "앳나운").split("|"),"%s/introttl.png"%WK,TFONT or FONT,
                                 int(job.get("title_size",92)),color=(255,255,255,255),box_alpha=0,pad=26,bold=True)
        # 인트로가 beat0과 같은 클립·같은 구간이면 도입 6초가 같은 장면 반복으로 보임(형 지적 2026-08-06).
        # → beat0과 다른 클립을 쓰고, 불량구간을 피한 시작점을 고른다.
        iclip=None
        if mode=="clips":
            b0=beats[0].get("clip")
            for bb in beats[1:]:
                if bb.get("clip") and bb["clip"]!=b0: iclip=bb["clip"]; break
            if not iclip: iclip=b0
        if mode=="clips" and iclip:
            isrc=os.path.join(cdir,iclip)
            istart=pick_start(isrc,effective_intro_sec,0.5) if job.get("smart_start",True) else 0.5
            _dl("INTRO clip=%s start=%.2f (beat0=%s)"%(iclip,istart,beats[0].get("clip")))
            iinp=["-ss","%.3f"%max(0.0,float(istart or 0)),"-t","%.3f"%float(effective_intro_sec),"-i",isrc,"-i",it_png]
            iwb=wb_filter(isrc, istart+effective_intro_sec/2.0) if job.get("auto_wb",True) else ""
            # 제목은 인트로와 본편이 같은 자리여야 한다. 인트로만 화면 중앙이면 1초 만에 제목이 튄다.
            _ity=int(job.get("title_y",210))
            if thumb_enabled:
                iinp+=["-i",thumb_png]
                ifc="[0]crop=iw:ih*0.92:0:0,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1%s[bg];[bg][1]overlay=(W-w)/2:%d[it];[it][2]overlay=(W-w)/2:%d:enable='between(t,0,%.2f)'[o]"%((","+iwb) if iwb else "",_ity,THUMB_Y,THUMB_DUR)
                thumb_overlay_added=True
            else:
                ifc="[0]crop=iw:ih*0.92:0:0,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1%s[bg];[bg][1]overlay=(W-w)/2:%d[o]"%((","+iwb) if iwb else "",_ity)
        else:
            _ity=int(job.get("title_y",210))
            iinp=["-f","lavfi","-i","color=c=black:s=1080x1920:d=%.2f"%effective_intro_sec,"-i",it_png]
            if thumb_enabled:
                iinp+=["-i",thumb_png]
                ifc="[0][1]overlay=(W-w)/2:%d[it];[it][2]overlay=(W-w)/2:%d:enable='between(t,0,%.2f)'[o]"%(_ity,THUMB_Y,THUMB_DUR)
                thumb_overlay_added=True
            else:
                ifc="[0][1]overlay=(W-w)/2:%d[o]"%_ity
        subprocess.run(["ffmpeg","-y"]+iinp+["-filter_complex",ifc,"-map","[o]","-t",str(effective_intro_sec),"-r",str(FPS),"-an","-pix_fmt","yuv420p","-preset","fast","-crf","16",iv],capture_output=True)
        if os.path.exists(iv): parts.insert(0,iv)
    outro_extra=0.0
    if job.get("outro"):
        # B방 검수 2026-08-09: 죽은 꼬리를 줄이기 위해 아웃트로는 1.3초가 정본.
        # 페이드는 짧게만 걸어 1.3초 안에서도 문구가 읽히게 둔다.
        osec=min(1.3, max(0.8, float(job.get("outro_sec",1.3) or 1.3))); ov="%s/vo.mp4"%WK; outro_extra=osec
        o_png,ow,oh=make_text_png(job["outro"].split("|"),"%s/outro.png"%WK,FONT,64,box_alpha=0)
        subprocess.run(["ffmpeg","-y","-f","lavfi","-i","color=c=black:s=1080x1920:d=%.2f"%osec,"-i",o_png,
            "-filter_complex","[0][1]overlay=(W-w)/2:(H-h)/2,fade=t=in:st=0:d=0.18,fade=t=out:st=%.2f:d=0.22[o]"%max(0.1,osec-0.22),
            "-map","[o]","-t",str(osec),"-r",str(FPS),"-an","-pix_fmt","yuv420p","-preset","fast","-crf","16",ov],capture_output=True)
        parts.append(ov)
    with open("%s/vl.txt"%WK,"w") as f:
        for p in parts: f.write("file '%s'\n"%p)
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i","%s/vl.txt"%WK,"-c:v","libx264","-preset","slow","-crf","18","-maxrate","12M","-bufsize","24M","-pix_fmt","yuv420p","-r",str(FPS),"%s/vid.mp4"%WK],capture_output=True)
    VD=clen("%s/vid.mp4"%WK)

    # ── STAGE C: 오디오 (연속 보이스 + BGM 옵션A) ──
    # 보이스: 약간의 리드(140ms) 후 연속 발화, 영상 길이에 맞춰 뒤 무음 패딩
    # 인트로 카드가 앞에 붙은 만큼 음성을 미뤄야 대사와 화면·자막이 맞는다.
    # (실측 사고 2026-08-06: 인트로 2.2초 때문에 전체가 2.2초 어긋남 = "대사랑 렌더가 안 맞음")
    lead_ms=int(140+ effective_intro_sec*1000)
    _dl("AUDIO_LEAD=%dms (intro=%.2fs separate=%s)"%(lead_ms,effective_intro_sec,separate_intro))
    subprocess.run(["ffmpeg","-y","-i","%s/voice.mp3"%WK,"-af","adelay=%d|%d,apad"%(lead_ms,lead_ms),"-t",str(VD),"-ar","44100","-ac","2","%s/voice.wav"%WK],capture_output=True)
    if not os.path.exists("%s/voice.wav"%WK) or clen("%s/voice.wav"%WK) < 1.0:
        raise RuntimeError("voice.wav 생성 실패/길이 비정상")
    _vv=subprocess.run(["ffmpeg","-i","%s/voice.wav"%WK,"-af","volumedetect","-f","null","-"],
                       capture_output=True,text=True).stderr
    _vm=re.search(r"mean_volume:\s*(-?[\d.]+)",_vv)
    if _vm and float(_vm.group(1)) <= -45.0:
        raise RuntimeError("voice.wav 무음 감지: mean_volume=%sdB"%_vm.group(1))
    final_a="%s/voice.wav"%WK
    if job.get("bgm",True):
        bg="%s/bgm.wav"%WK
        bvol=job.get("bgm_volume",0.45)
        bgm_src=os.path.expanduser(job.get("bgm_file","") or "")
        if bgm_src and os.path.exists(bgm_src):
            # ── 실제 음원(형 뮤팟 BGM 등) — 합성음 대신 최우선 ──
            # VD 길이로 트림 + 인/아웃 페이드 + 볼륨. 긴 곡이면 앞부분 사용.
            subprocess.run(["ffmpeg","-y","-i",bgm_src,"-af",
                "volume=%.2f,afade=t=in:st=0:d=%.2f,afade=t=out:st=%.2f:d=1.8,atrim=0:%.2f,aformat=channel_layouts=stereo"%(bvol,float(job.get("bgm_fadein",1.6)),max(0.1,VD-1.8),VD),
                "-ar","44100","-ac","2",bg],capture_output=True)
            _dl("BGM_FILE=%s vol=%.2f"%(bgm_src,bvol))
        else:
            # ── fallback: 합성 패드(음원 없을 때만) ──
            subprocess.run(["ffmpeg","-y",
                "-f","lavfi","-i","sine=frequency=261.63:sample_rate=44100",
                "-f","lavfi","-i","sine=frequency=329.63:sample_rate=44100",
                "-f","lavfi","-i","sine=frequency=392:sample_rate=44100",
                "-f","lavfi","-i","sine=frequency=130.81:sample_rate=44100",
                "-filter_complex",
                "[0][1][2]amix=inputs=3:normalize=1[ch];[3]volume=0.5,lowpass=f=180[bs];"
                "[ch][bs]amix=inputs=2:normalize=0,tremolo=f=0.2:d=0.4,lowpass=f=2600,highpass=f=150,"
                "aecho=0.8:0.8:330:0.28,volume=%.2f,atrim=0:%.2f,aformat=channel_layouts=stereo"%(0.5,VD),
                bg],capture_output=True)
            _dl("BGM_SYNTH(fallback) vol=0.5")
        mx="%s/mix.wav"%WK
        # 사이드체인: 말할 때만 BGM 살짝 죽임(과하지 않게) → 스피치 중에도 안 사라짐, 비트 사이 gap에서 확 들림
        subprocess.run(["ffmpeg","-y","-i","%s/voice.wav"%WK,"-i",bg,"-filter_complex",
            "[1][0]sidechaincompress=threshold=0.1:ratio=3:attack=20:release=350[bd];"
            "[0][bd]amix=inputs=2:normalize=0:duration=first","-ar","44100","-ac","2",mx],capture_output=True)
        if os.path.exists(mx) and clen(mx) >= 1.0:
            final_a=mx
        else:
            _dl("BGM_MIX_FAIL_FALLBACK_TO_VOICE")

    render_backup=None
    if os.path.exists(out):
        render_backup="%s/previous_output.mp4"%WK
        shutil.copy2(out, render_backup)
    _r=subprocess.run(["ffmpeg","-y","-i","%s/vid.mp4"%WK,"-i",final_a,"-map","0:v:0","-map","1:a:0","-c:v","copy","-af","loudnorm=I=-14:TP=-1.5:LRA=11","-c:a","aac","-b:a","192k","-ar","48000","-ac","2","-shortest",out],capture_output=True)
    _dl("VID_EXISTS=%s OUT_EXISTS=%s"%(os.path.exists("%s/vid.mp4"%WK),os.path.exists(out)))
    if not os.path.exists(out): _dl("MUX_FAIL: "+_r.stderr.decode("utf-8","ignore")[-500:])

    # ── CHECKLIST ──
    def pr(ent,st=None):
        c=["ffprobe","-v","error","-show_entries",ent,"-of","default=nk=1:nw=1"]+(["-select_streams",st] if st else [])
        return subprocess.run(c+[out],capture_output=True,text=True).stdout.strip()
    def astats(f):
        rr=subprocess.run(["ffmpeg","-i",f,"-af","volumedetect","-f","null","-"],capture_output=True,text=True).stderr
        m=re.search(r"mean_volume:\s*(-?[\d.]+)",rr); x=re.search(r"max_volume:\s*(-?[\d.]+)",rr)
        return (float(m.group(1)) if m else -99.0, float(x.group(1)) if x else -99.0)
    fd=clen(out); sz=os.path.getsize(out)/1e6 if os.path.exists(out) else 0
    maxlen=max((len(l) for b in beats for l in (b.get("cap") or "").split("|")),default=0)
    vmean=astats("%s/voice.wav"%WK)[0] if os.path.exists("%s/voice.wav"%WK) else -99.0
    amean,amax=astats(out) if os.path.exists(out) else (-99.0,-99.0)
    # 반복금지 규칙(박제): 45s 미만=클립당 1회, 45s 이상=최대 2회
    # 2026-08-09 규칙 정정 (형 지시: "b롤이 너무 빨리빨리 넘어가서 정신없다"):
    #   붙어 있는 비트가 같은 클립 = 한 장면을 '이어서 보여주는 것'이다. 이건 허용한다.
    #   오히려 자막만 바뀌고 화면이 유지되면 눈이 쉰다.
    #   떨어져 있는 비트가 같은 클립 = 아까 쓴 걸 '재활용'한 것이다. 이건 금지한다.
    #   예전엔 둘을 구분 못 해서, 화면을 붙잡아 두려 할 때마다 게이트가 떨어뜨렸다.
    from collections import Counter
    if mode=="clips":
        runs=[]                       # 연속 구간을 하나로 접는다
        for b in beats:
            c=b.get("clip","")
            if not c: 
                runs.append("")       # 검정이 끼면 연속이 끊긴다
                continue
            if not runs or runs[-1]!=c: runs.append(c)
        clip_use=Counter(c for c in runs if c)
    else:
        clip_use=Counter()
    rep_cap=int(job.get("repeat_cap", 2 if fd>=45 else 1))
    over=[c for c,n in clip_use.items() if c and n>rep_cap]
    # A/V 동기 게이트: 목소리 시작이 인트로 길이와 맞는지 실측(어긋나면 대사↔화면 불일치)
    def voice_onset():
        try:
            rr=subprocess.run(["ffmpeg","-i","%s/voice.wav"%WK,"-af","silencedetect=noise=-40dB:d=0.15","-f","null","-"],
                              capture_output=True,text=True).stderr
            m=re.search(r"silence_end:\s*([\d.]+)",rr)
            if m: return float(m.group(1))
            return 0.0
        except: return -1.0
    onset=voice_onset(); expect=effective_intro_sec
    sync_ok=bool(job.get("local_tts")) or (onset<0) or abs(onset-expect)<=0.8
    rc_=rhyme_check(beats); sm_=speech_metrics(al, audioEnd)
    natural_ok = rc_["rhyme_ok"] and sm_.get("rate_ok",True) and sm_.get("gap_ok",True)
    thumb_present=thumb_bar_present(out) if os.path.exists(out) else False
    thumb_line_count=len(thumb_lines)
    thumb_ok=True if not thumb_enabled else ((thumb_len(thumb_text)<=THUMB_MAX_LEN) and (thumb_line_count==1) and bool(thumb_overlay_added and thumb_present))
    loud_peak_ok = amax > (-20.0 if job.get("local_tts") else -4.0)
    chk={"file":os.path.exists(out),"video":pr("stream=codec_type","v:0")=="video","audio":pr("stream=codec_type","a:0")=="audio",
         "voice_onset":round(onset,2),"intro_sec":round(expect,2),"sync_ok":sync_ok,
         "rhyme":rc_,"speech":sm_,"natural_ok":natural_ok,
         "dur_s":round(fd,1),"dur_ok":33<=fd<=180,"dur_pref":33<=fd<=48,"dur_note":("권장 33~48초" if not (33<=fd<=48) else ""),"size_mb":round(sz,1),"size_ok":sz<90,   # 2026-08-14 화질상향(crf18)에 맞춰 30->90MB. 1080x1920 8~12Mbps면 45~70MB가 정상
         "caption_max":maxlen,"caption_ok":maxlen<=26,"window_dup":dups,"dup_ok":not dups,
         "thumb_text":thumb_text,"thumb_len":thumb_len(thumb_text),"thumb_lines":thumb_line_count,
         "thumb_enabled":thumb_enabled,"thumb_present":thumb_present,"thumb_ok":thumb_ok,
         "repeat_cap":rep_cap,"repeat_over":over,"repeat_ok":not over,
         "voice_mean":round(vmean,1),"voice_ok":vmean>-45.0,
         "vault_hits":vault_hits,"vault_warn":vault_warn or ("" if vault_hits else "vault_hits_empty"),
         "tts":"continuous","bgm":bool(job.get("bgm",True)),
         "loud_mean":round(amean,1),"loud_max":round(amax,1),"loud_ok":(loud_peak_ok and amean>-28.0),
         "out":out}
    # 검정(글자만) 비중 게이트 — 화면이 죽으면 문장이 좋아도 안 본다. (형 지적 2026-08-08)
    # B방 검수 기준과 맞춰 실제 프레임 샘플(4fps, 32x57 gray 평균 12 미만)을 정본으로 둔다.
    _nb=len(beats) or 1
    _blk=sum(1 for _b in beats if _b.get("black"))
    _bs=black_sample_ratio(out) if os.path.exists(out) else None
    chk["black_beats"]=_blk
    if _bs:
        _black_frames,_black_total,_black_ratio=_bs
        chk["black_frames"]=_black_frames
        chk["black_total"]=_black_total
        chk["black_ratio"]=round(_black_ratio,3)
        chk["black_ratio_beat"]=round(_blk/_nb,2)
    else:
        chk["black_ratio"]=round(_blk/_nb,2)
        chk["black_ratio_beat"]=round(_blk/_nb,2)
    chk["black_ok"]=chk["black_ratio"] <= float(job.get("black_max",0.40))
    # ── 듣기(실측) ── 형 지시 2026-08-08 "소리도 들어야돼"
    if job.get("audit", True):
        _au=audit_audio(out, job, beats, starts, effective_intro_sec, key)
        chk.update(_au)
        chk["voice_present_ok"]=bool(_au.get("voice_present_ok"))
        if "stt_sync_ok" in _au:
            chk["sync_ok"]=chk["sync_ok"] and bool(_au.get("stt_sync_ok"))
        chk["read_ok"]= (_au.get("read_ratio") is None) or (_au.get("read_ratio",0)>=float(job.get("read_min",0.90)))
        chk["sync_meas_ok"]= ("sync_avg" not in _au) or (not _au.get("sync_drifts")) or (abs(_au.get("sync_avg",0))<=0.10)
        chk["gap_natural_ok"]= len(_au.get("inner_gaps") or [])<=2
    else:
        chk["voice_present_ok"]=True; chk["read_ok"]=True; chk["sync_meas_ok"]=True; chk["gap_natural_ok"]=True
    chk["cap_trace"]=CAP_TRACE
    chk["layout_hits"]=LAYOUT_HITS[:8]; chk["layout_ok"]=(len(LAYOUT_HITS)==0)
    chk["min_beat_s"]=round(min(durs),2) if durs else 0.0
    chk["beat_ok"]=chk["min_beat_s"]>=float(job.get("min_beat",1.6))-0.05
    chk["max_beat_s"]=round(max(durs),2) if durs else 0.0
    chk["slow_ok"]=chk["max_beat_s"]<=float(job.get("max_beat",8.0))+0.05
    camel=camel_marketing_gate(job, beats)
    chk["camel_marketing"]=camel
    chk["chano_line_ok"]=camel["chano_line_ok"]
    chk["one_idea_ok"]=camel["one_idea_ok"]
    chk["axis"]=camel["axis"]
    chk["axis_missing"]=camel["axis_missing"]
    chk["axis_repeat_warning"]=camel["axis_repeat_warning"]
    # 2026-08-10 — 「흑백 마인드」 형식(mode!=clips)은 화면 전체가 검정이고 컷이 없다.
    # 그게 이 형식의 전부인데 black_ok/beat_ok 가 불합격을 내고 이전 판으로 되돌려
    # 방금 만든 영상을 지워버렸다. 클립용 게이트를 글자형식에 적용하면 안 된다.
    if mode!="clips":
        chk["black_ok"]=True
        chk["beat_ok"]=True
        chk["dup_ok"]=True
        chk["repeat_ok"]=True

    chk["PASS"]=all([chk["file"],chk["video"],chk["audio"],chk["dur_ok"],chk["size_ok"],chk["caption_ok"],chk["dup_ok"],chk["repeat_ok"],chk["voice_ok"],chk["loud_ok"],chk["sync_ok"],chk["natural_ok"],chk["thumb_ok"],chk["black_ok"],chk["layout_ok"],chk["beat_ok"],chk["voice_present_ok"],chk["read_ok"],chk["sync_meas_ok"],chk["slow_ok"],chk["chano_line_ok"]])
    used=[b.get("clip") for b in beats if b.get("clip")]
    prev=recent_clips(int(job.get("avoid_last",3)))
    overlap=[c for c in set(used) if c in prev]
    chk["clip_overlap_prev"]=overlap
    chk["fresh_ratio"]=round(1-(len(overlap)/max(1,len(set(used)))),2)
    chk["fresh_ok"]=chk["fresh_ratio"]>=float(job.get("fresh_min",0.5))
    chk["PASS"]=chk["PASS"] and chk["fresh_ok"]
    if not chk["PASS"] and not job.get("keep_failed"):
        if render_backup and os.path.exists(render_backup):
            shutil.copy2(render_backup, out)
            chk["restored_previous_output"]=True
        elif os.path.exists(out):
            os.unlink(out)
            chk["removed_failed_output"]=True
    save_usage(out, used, job.get("form") or job.get("stem"), camel["axis"])
    _dl("CHECKLIST "+json.dumps(chk,ensure_ascii=False)); print("CHECKLIST",json.dumps(chk,ensure_ascii=False))
    sys.exit(0 if chk["PASS"] else 1)

if __name__=="__main__":
    import traceback
    try:
        _dl("=== START job=%s ==="%(sys.argv[1] if len(sys.argv)>1 else "?")); main()
    except SystemExit: raise
    except TTSQuotaExhausted as e:
        _dl("ERROR %s\n%s"%(repr(e),traceback.format_exc()))
        print("TTS_QUOTA_EXHAUSTED",str(e))
        sys.exit(75)
    except Exception as e:
        _dl("ERROR %s\n%s"%(repr(e),traceback.format_exc())); raise
