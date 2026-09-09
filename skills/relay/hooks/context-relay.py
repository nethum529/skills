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
DEFAULT_TOKENS = 200000


def _positive_float(raw):
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value) or value <= 0:
        return None
    return value


def threshold():
    """Return (kind, value).

    Tokens are the default. A token budget means the same amount of work on
    every window size, so a 200k window and a 1M window warn at the same
    point. Percent stays available as an override for anyone who wants it.
    """
    percent = os.environ.get("CONTEXT_RELAY_PERCENT")
    if percent is not None:
        value = _positive_float(percent)
        if value is not None:
            return "percent", value
    value = _positive_float(os.environ.get("CONTEXT_RELAY_TOKENS"))
    return "tokens", value if value is not None else float(DEFAULT_TOKENS)
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

def context_usage(payload):
    # Always pin context-axi to THIS session. Never fall back to --cwd:
    # cwd mode picks the newest transcript in the directory, which can be a
    # different session, so one session reads another session's usage and
    # relays at the wrong time.
    transcript = payload.get("transcript_path")
    session_id = payload.get("session_id")
    command = ["context-axi"]
    if transcript:
        command += ["--transcript", str(transcript)]
    elif session_id:
        command += ["--session", str(session_id)]
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
    if not isinstance(data, dict):
        return None
    return {
        "percent": _number(data.get("percentUsed")),
        "tokens": _number(data.get("tokensUsed")),
        "window": _number(data.get("window")),
    }


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) else None

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
        usage = context_usage(payload)
        kind, limit = threshold()
        used = None if usage is None else usage.get(kind)
        if used is None or used < limit:
            return
        last_warn = state.get("last_warn_time", 0)
        if isinstance(last_warn, (int, float)) and now - last_warn < WARN_INTERVAL:
            return
        state["last_warn_time"] = now
        count = state.get("warn_count", 0)
        state["warn_count"] = count + 1 if isinstance(count, int) else 1
        save_state(handle, state)
    if kind == "tokens":
        window = usage.get("window")
        room = "" if window is None else f" of a {display_number(window)} token window"
        state_text = (
            f"context has used {display_number(used)} tokens{room} "
            f"(threshold {display_number(limit)} tokens)"
        )
    else:
        state_text = (
            f"context is at {display_number(used)} percent "
            f"(threshold {display_number(limit)} percent)"
        )
    message = (
        f"CONTEXT RELAY: {state_text}. Finish the current step, do not "
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
