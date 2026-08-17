#!/usr/bin/env python3
"""원격 실행기 자기 자신 재기동 (KeepAlive 가 새 코드로 되살림)"""
import subprocess, os
uid = os.getuid()
subprocess.Popen(["bash","-lc",
  f"sleep 2; launchctl kickstart -k gui/{uid}/com.atnown.remote-cmd"],
  start_new_session=True)
print("2초 뒤 실행기 재기동 예약됨 — 새 코드로 올라옵니다")
