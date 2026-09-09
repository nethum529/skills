# Handoff template

Copy this structure. Delete sections that are genuinely empty. Never delete the fleet
table or the shutdown block.

---

# Handoff: <one line, what this work is>

Written by: <your agent name or pane ID>, <model>
Date: <YYYY-MM-DD HH:MM>
Working directory: <abs path>
Branch: <branch name> (<clean | N uncommitted files>)

## Mission

Two or three sentences. What the user is trying to achieve, in their terms.

## State

### Done
- <thing>, landed in <commit or path>

### In progress
- <thing> — <exact file:line>, <what is half written and what is missing>

### Next steps
1. <first action the successor should take>
2. ...

## Decisions and constraints

- <decision> — because <reason>
- <thing the user told you not to do, verbatim>
- <approach already tried and rejected, and why, so it is not retried>

## Key files

- `path/to/file.py:120` — <why it matters>

## References

Do not paste these, open them.

- Spec / plan / ticket: <path or URL>
- Related PR or issue: <URL>

## Open questions for the user

- <question that is still unanswered>

## Fleet: agents and panes you now own

| Name | Kind | Pane | Working dir | Task given | State when handed over | What you must do next |
|------|------|------|-------------|-----------|------------------------|-----------------------|
| reviewer | codex | w1:p4 | /path | Review the diff on branch X | idle | Read its output with `herdr agent read reviewer --source recent-unwrapped --lines 120` and apply the findings |

Not mine, do not touch: <names or pane IDs owned by the user or another agent>

Commands you will need:

```bash
herdr agent list
herdr agent get <name>
herdr agent read <name> --source recent-unwrapped --lines 120
herdr agent prompt <name> "<text>" --wait --timeout 120000
```

## Suggested skills

- `/<skill>` — <when to invoke it in this work>

## Shutdown: close the outgoing agent

The agent that wrote this document is still running and is holding context you do not
need. Close it once you have read this whole file and understand the work.

- Outgoing agent name: `<name>`
- Outgoing pane ID: `<w1:pN>`
- Outgoing tab ID: `<w1:tN>`
- Outgoing workspace ID: `<wN>`

Run, in this order:

```bash
herdr agent prompt <outgoing-name> "/exit"
herdr pane close <outgoing-pane-id>
```

If `agent prompt` fails because the agent already exited, close the pane anyway. If
`pane close` fails, report it to the user instead of retrying with force.

Then tell the user you have taken over, name the outgoing pane you closed, and state
the first next step you are about to do.
