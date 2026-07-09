#!/usr/bin/env python3
"""Backup Hermes config + skills to /root/hermes-backup/"""
import subprocess, os, shutil
from datetime import datetime

DEST = "/root/hermes-backup"
ts = datetime.now().strftime("%Y%m%d")

subprocess.run(["mkdir", "-p", DEST], timeout=5)
archive = f"{DEST}/hermes-backup-{ts}.tar.gz"

result = subprocess.run(
    ["tar", "czf", archive, "--exclude=__pycache__",
     "--exclude=*.pyc", "--exclude=node_modules",
     "-C", "/root", ".hermes"],
    capture_output=True, text=True, timeout=120
)

if result.returncode == 0:
    size = os.path.getsize(archive) / 1024
    print(f"✅ Backup: {archive} ({size:.0f} KB)")
else:
    print(f"❌ Backup gagal: {result.stderr[:200]}")
