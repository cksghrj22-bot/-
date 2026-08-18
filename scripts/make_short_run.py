#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""remote_cmd_watch 화이트리스트용 얇은 호출기 (scripts/ 안에 있어야 실행된다).
사용: {"cmd":"python_script","args":["make_short_run.py","<매니페스트>","<출력>"]}"""
import subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
r = subprocess.run([sys.executable, str(ROOT/"rooms/유튜브쇼츠방/make_short.py")] + sys.argv[1:],
                   cwd=str(ROOT))
sys.exit(r.returncode)
