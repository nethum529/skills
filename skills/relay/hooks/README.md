# context-relay hook

The relay skill needs this hook to run without a human. The hook watches how full
the context window is. When it goes over the limit, the hook tells the agent to
stop and run `/relay`. Without the hook, nothing starts the handoff.

## Needs

- `context-axi` on your PATH. The hook calls it to read the context percent.
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

## Settings

- `CONTEXT_RELAY_PERCENT` sets the limit. Default is 20 percent left.
- `CONTEXT_RELAY_DISABLE=1` turns the hook off.

## How it works

- Checks at most one time every 45 seconds.
- Warns at most one time every 300 seconds.
- Keeps state per session in `~/.local/state/context-relay/`.
- Fails quiet. If `context-axi` is missing or slow, the hook says nothing.
