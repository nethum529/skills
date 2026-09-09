#!/usr/bin/env python3
import fcntl
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

CHECK_INTERVAL = 45
WARN_INTERVAL = 300
def threshold_percent():
    try:
        value = float(os.environ.get("CONTEXT_RELAY_PERCENT", "20"))
    except ValueError:
        return 20.0
    return value if math.isfinite(value) else 20.0
def state_path(session_id):
    if not session_id:
        return None
    safe_id = "".join(
        char if char.isalnum() or char in "._-" else "_" for char in str(session_id)
    )[:160]
    if not safe_id:
        return None
    return Path.home() / ".local/state/context-relay" / f"{safe_id}.json"
def load_state(handle):
    try:
        handle.seek(0)
        state = json.load(handle)
        return state if isinstance(state, dict) else {}
    except (OSError, ValueError):
        return {}
def save_state(handle, state):
    handle.seek(0)
    handle.truncate()
    json.dump(state, handle)
    handle.flush()

def context_percent(payload):
    transcript = payload.get("transcript_path")
    cwd = payload.get("cwd")
    command = ["context-axi"]
    if transcript:
        command += ["--transcript", str(transcript)]
    elif cwd:
        command += ["--cwd", str(cwd)]
    else:
        return None
    command.append("--json")
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=8, check=False
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
        data = json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    percent = data.get("percentUsed") if isinstance(data, dict) else None
    if isinstance(percent, bool) or not isinstance(percent, (int, float)):
        return None
    return float(percent) if math.isfinite(percent) else None

def display_number(value):
    return f"{value:g}"

def run():
    if os.environ.get("CONTEXT_RELAY_DISABLE") == "1":
        return
    try:
        payload = json.load(sys.stdin)
    except (OSError, ValueError):
        return
    if not isinstance(payload, dict):
        return
    path = state_path(payload.get("session_id"))
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        state = load_state(handle)
        now = time.time()
        last_check = state.get("last_check_time", 0)
        if isinstance(last_check, (int, float)) and now - last_check < CHECK_INTERVAL:
            return
        state.setdefault("last_warn_time", 0)
        state.setdefault("warn_count", 0)
        state["last_check_time"] = now
        save_state(handle, state)
        percent = context_percent(payload)
        threshold = threshold_percent()
        if percent is None or percent < threshold:
            return
        last_warn = state.get("last_warn_time", 0)
        if isinstance(last_warn, (int, float)) and now - last_warn < WARN_INTERVAL:
            return
        state["last_warn_time"] = now
        count = state.get("warn_count", 0)
        state["warn_count"] = count + 1 if isinstance(count, int) else 1
        save_state(handle, state)
    message = (
        f"CONTEXT RELAY: context is at {display_number(percent)} percent "
        f"(threshold {display_number(threshold)}). Finish the current step, do not "
        "start a new task, then run the relay skill (/relay) to hand this session "
        "to a fresh agent. Carry every agent, pane and watcher you manage in the handoff."
    )
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUse", "additionalContext": message
    }}))

if __name__ == "__main__":
    try:
        run()
    except Exception:
        pass
