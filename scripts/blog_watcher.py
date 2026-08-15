#!/usr/bin/env python3
"""블로그 자동 임시저장 감시 데몬

_publish_jobs/blog_parsed/ 에 잡 폴더가 들어오면 자동으로 naver_blog_save.mjs 실행.
형 개입 없이 완전 자동.

사용법:
    python3 scripts/blog_watcher.py

launchd 등록:
    이 스크립트를 com.atnown.blogwatch.plist 로 등록
"""
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
PARSED = ROOT / "_publish_jobs/blog_parsed"
DONE = ROOT / "_publish_jobs/blog_done"
LOG = ROOT / "data/blog_watcher.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def get_pending_jobs():
    """처리 대기 중인 잡 목록"""
    if not PARSED.exists():
        return []
    jobs = []
    for d in PARSED.iterdir():
        if d.is_dir() and not d.name.startswith("_"):
            blocks = d / "blocks.json"
            if blocks.exists():
                jobs.append(d.name)
    return sorted(jobs)

def run_blog_save(job_name):
    """naver_blog_save.mjs 실행"""
    log(f"📝 블로그 저장 시작: {job_name}")

    env = {"JOB": job_name}
    result = subprocess.run(
        ["node", str(ROOT / "scripts/naver_blog_save.mjs")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=300,
        env={**dict(__import__('os').environ), **env}
    )

    if result.returncode == 0:
        log(f"✅ 완료: {job_name}")
        # 완료된 잡 이동
        DONE.mkdir(exist_ok=True)
        src = PARSED / job_name
        dst = DONE / f"{job_name}_{datetime.now().strftime('%H%M')}"
        src.rename(dst)
        return True
    else:
        log(f"❌ 실패: {job_name}")
        log(f"   {result.stderr[:500]}")
        return False

def watch():
    """감시 루프"""
    log("🚀 블로그 감시 데몬 시작")

    while True:
        try:
            jobs = get_pending_jobs()

            for job in jobs:
                try:
                    run_blog_save(job)
                except subprocess.TimeoutExpired:
                    log(f"⏰ 타임아웃: {job}")
                except Exception as e:
                    log(f"❌ 에러: {job} - {e}")

                time.sleep(5)  # 잡 간 간격

        except Exception as e:
            log(f"❌ 감시 에러: {e}")

        time.sleep(30)  # 30초마다 체크

if __name__ == "__main__":
    import sys
    if "--once" in sys.argv:
        jobs = get_pending_jobs()
        log(f"📋 {len(jobs)}개 잡 발견")
        for job in jobs:
            run_blog_save(job)
    else:
        watch()
