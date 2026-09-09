# relay

Hands a session off to a fresh agent in a new Herdr pane, with a handoff doc that
carries the work state and every agent or pane the outgoing agent manages.

Needs Herdr (`HERDR_ENV=1`).

## Files

- `SKILL.md` - the skill itself.
- `references/handoff-template.md` - the shape of the handoff document.
- `hooks/` - the context watcher that makes relay start on its own. See its README.

## Launch command

`SKILL.md` defaults to the written commands:

```
claude --dangerously-skip-permissions --model <model>
codex  --dangerously-bypass-approvals-and-sandbox --model <model>
```

These work everywhere. Read the next section before you decide that is enough.

## Note for agents: the folder-trust pre-accept

Read this before you start a successor on a machine you have not relayed on before.

### The problem

`--dangerously-skip-permissions` skips permission prompts. It does not skip the
folder-trust dialog. Claude Code shows that dialog the first time it runs in a
directory it has not seen.

Relay is meant to run with nobody watching. A successor that stops on a trust
dialog never starts, and the outgoing agent has already written the handoff doc
and opened the pane. The failure is silent and late.

### The fix

Mark the directory as trusted before you launch. In `~/.claude.json`:

```
projects -> <absolute cwd> -> hasTrustDialogAccepted = true
```

Write it safely. Load the JSON, set the key, write a temp file in the same
directory, then rename over the original. Do not truncate `~/.claude.json` in
place. It holds all project state, and a partial write loses it.

### Do it the way this machine already does it

Do not add your own copy of this if the user already solved it. Check first:

```bash
type -q danger        # fish
command -v danger     # bash, zsh
```

If a wrapper exists, use it and stop. It probably does the pre-accept already,
and a second mechanism is one more thing to keep in sync.

Match what you find:

| What the machine has | What you do |
| --- | --- |
| A wrapper like `danger` or `cdanger` | Use it. Change nothing. |
| No wrapper, and the cwd is already trusted | Launch the written command. |
| No wrapper, and the cwd is not trusted | Pre-accept, then launch. Offer to make it a wrapper so the next relay is clean. |

Ask the user before you add a shell function or edit their config. A launch
shortcut is their environment, not yours.

### If you skip the pre-accept

Read the pane after launching:

```bash
herdr pane read <pane-id> --source recent-unwrapped --lines 60
```

A trust dialog is answerable with `herdr pane send-keys`. Do not leave the
successor sitting on it.

## Note for humans

The author's own copy of this skill hard codes `danger` and `cdanger`, because
those exist on that machine and handle the pre-accept. The copy in this repo
stays generic on purpose.
