#!/usr/bin/env python3
"""Cron watchdog: copy missing scripts only. <2s."""
import json, os, shutil

HERMES_SCRIPTS = os.path.expanduser("~/.hermes/scripts")
SEMBAKO_SCRIPTS = "/root/sembako/scripts"
CRON_JOBS_PATH = os.path.expanduser("~/.hermes/cron/jobs.json")

def auto_fix():
    if not os.path.exists(CRON_JOBS_PATH):
        return "[SILENT]"
    with open(CRON_JOBS_PATH) as f:
        jobs = json.load(f).get("jobs", [])
    actions = []
    for job in jobs:
        script = job.get("script", "")
        if not script:
            continue
        script_path = os.path.join(HERMES_SCRIPTS, script)
        if os.path.exists(script_path):
            continue
        src = os.path.join(SEMBAKO_SCRIPTS, script)
        if os.path.exists(src):
            shutil.copy2(src, script_path)
            actions.append(f"✅ {script}")
        else:
            actions.append(f"⚠️ {script} not found")
    return "[SILENT]" if not actions else "🤖 *Watchdog*\n" + "\n".join(actions)

if __name__ == "__main__":
    print(auto_fix())