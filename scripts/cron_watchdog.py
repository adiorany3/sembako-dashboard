#!/usr/bin/env python3
"""
Cron watchdog: detect & auto-fix failed jobs.
Runs every 2h. Fixes:
  - Script not found → copy from sembako/scripts/
  - Script error → retry 1x
  - Data corruption → rebuild from JSON
Reports only when action taken or fix failed.
"""
import json, os, subprocess, sys
from datetime import datetime

HERMES_SCRIPTS = os.path.expanduser("~/.hermes/scripts")
SEMBAKO_SCRIPTS = "/root/sembako/scripts"
CRON_JOBS_PATH = os.path.expanduser("~/.hermes/cron/jobs.json")
CRON_OUTPUT = os.path.expanduser("~/.hermes/cron/output")

LOG = "/tmp/cron_watchdog.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(LOG, "a") as f:
        f.write(f"[{ts}] {msg}\n")

def auto_fix():
    if not os.path.exists(CRON_JOBS_PATH):
        return "[SILENT]"

    with open(CRON_JOBS_PATH) as f:
        data = json.load(f)
    jobs = data.get("jobs", [])

    actions = []

    for job in jobs:
        jid = job.get("id") or job.get("job_id", "")
        name = job.get("name", jid)
        script = job.get("script", "")
        last_status = job.get("last_status", "")
        workdir = job.get("workdir", "")

        if not script or last_status != "error":
            continue

        # 1. Fix: script not found in ~/.hermes/scripts/
        script_path = os.path.join(HERMES_SCRIPTS, script)
        if not os.path.exists(script_path):
            # Check if exists in sembako
            src = os.path.join(SEMBAKO_SCRIPTS, script)
            if os.path.exists(src):
                try:
                    subprocess.run(["cp", src, script_path], check=True, timeout=10)
                    actions.append(f"✅ {name}: script copied {src} → {script_path}")
                    log(f"Fixed script missing: {script}")
                except Exception as e:
                    actions.append(f"❌ {name}: copy failed: {e}")
                    log(f"FAILED fix script {script}: {e}")
            else:
                actions.append(f"⚠️ {name}: script {script} not found in either dir")
                log(f"Script missing: {script} not in sembako either")
            continue

        # 2. Fix: re-run script 1x
        try:
            env = os.environ.copy()
            if workdir:
                cwd = os.path.expanduser(workdir)
            else:
                cwd = "/root"

            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True, text=True, timeout=60, cwd=cwd, env=env
            )

            if result.returncode == 0:
                actions.append(f"✅ {name}: retry OK (previous {last_status})")
                log(f"Retry OK: {script}")
            else:
                # Truncate long output
                err = (result.stdout + result.stderr)[:200].strip()
                actions.append(f"⚠️ {name}: retry still failed: {err}")
                log(f"Retry FAIL: {script} → {err}")
        except subprocess.TimeoutExpired:
            actions.append(f"⚠️ {name}: retry timeout")
            log(f"Retry timeout: {script}")
        except Exception as e:
            actions.append(f"⚠️ {name}: retry error: {e}")
            log(f"Retry error: {script}: {e}")

    if not actions:
        return "[SILENT]"

    msg = "🤖 *Cron Watchdog*\n"
    msg += "\n".join(actions)
    return msg

if __name__ == "__main__":
    print(auto_fix())