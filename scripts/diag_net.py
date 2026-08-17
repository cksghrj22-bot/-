#!/usr/bin/env python3
"""본진의 집안 네트워크 주소 확인 — 맥북에서 Tailscale 없이 붙기 위해"""
import subprocess
def sh(c):
    r=subprocess.run(["bash","-lc",c],capture_output=True,text=True,timeout=30)
    return (r.stdout or r.stderr).strip()
print("=== 호스트 이름 ===")
print(sh("scutil --get LocalHostName 2>/dev/null; hostname"))
print("\n=== 집안 IP (LAN) ===")
print(sh("ipconfig getifaddr en0 2>/dev/null || true"))
print(sh("ipconfig getifaddr en1 2>/dev/null || true"))
print(sh("ifconfig | grep 'inet ' | grep -v 127.0.0.1 | grep -v ' 100\\.' | awk '{print $2}'"))
print("\n=== SSH 열려있나 ===")
print(sh("sudo -n launchctl print system/com.openssh.sshd >/dev/null 2>&1 && echo 'sshd 확인불가(권한)'; lsof -nP -iTCP:22 -sTCP:LISTEN 2>/dev/null | head -3 || echo '(조회 실패)'"))
print("\n=== 잠자기 설정 ===")
print(sh("pmset -g | grep -E 'sleep|womp' | head -6"))
