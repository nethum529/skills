# context-relay hook

The relay skill needs this hook to run without a human. The hook watches how much
context the session has used. When it goes over the limit, the hook tells the agent
to stop and run `/relay`. Without the hook, nothing starts the handoff.

## Needs

- `context-axi` on your PATH. The hook calls it to read context use.
- Python 3.

## Install

1. Copy the file:

```
cp context-relay.py ~/.claude/hooks/context-relay.py
```

2. Add a PostToolUse hook in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/context-relay.py",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

Put it in `~/.claude/settings.json`, not a project file. Then it runs in every
session, not only the one you set it up in.

## Settings

- `CONTEXT_RELAY_TOKENS` sets the limit in tokens used. Default is 200000.
- `CONTEXT_RELAY_PERCENT` sets a percent-used limit instead. It wins if you set it.
- `CONTEXT_RELAY_DISABLE=1` turns the hook off.

### Use tokens, not percent

Set the limit in tokens. Do not use percent.

Context windows are not the same size. A 200000 window and a 1000000 window are
both "20 percent" at very different amounts of real work. A percent limit means
the agent relays too early on a big window and too late on a small one. A token
limit is the same amount of work every time.

This is why 200000 tokens is the default.

## One session, one counter

The hook keeps state per session in `~/.local/state/context-relay/`, one file per
session ID. Two sessions never share a timer or a warning count.

The hook also pins `context-axi` to the current session. It passes `--transcript`,
or `--session` if there is no transcript path. It never uses `--cwd`. See issue
about cross-session reads: `--cwd` mode picks the newest transcript in the folder,
so a quiet session can read a busy session's number and relay for no reason.

## How it works

- Checks at most one time every 45 seconds.
- Warns at most one time every 300 seconds.
- Fails quiet. If `context-axi` is missing or slow, the hook says nothing.
