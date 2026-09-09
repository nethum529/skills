---
name: relay
description: "Hand this session off to a fresh Claude agent in a new Herdr pane. Splits a pane next to you, runs danger with your model, writes a handoff doc that carries the work state plus every agent or pane you are managing, and asks the successor to close your pane. Use when the user invokes /relay or asks to hand off, relay, pass the baton, or free up context by moving to a fresh agent. Requires HERDR_ENV=1."
argument-hint: "[optional: model to use, and what the successor should focus on]"
---

# Relay

This is a context management handoff. You are the outgoing agent. You start a fresh
agent beside you, give it everything it needs to continue without asking the user to
repeat anything, transfer ownership of the panes and agents you manage, and then let it
close you down.

Do the steps in order. Do not skip step 1.

## 1. Check you are inside Herdr

```bash
test "${HERDR_ENV:-}" = 1
```

If this fails, tell the user you are not running inside a Herdr pane, so you cannot
create the successor pane. Offer to write the handoff document only. Stop.

Read `~/.claude/skills/herdr/SKILL.md` if you have not already loaded the Herdr rules in
this session. Those rules apply to every command below.

## 2. Collect the facts

Run these and read the JSON. Do not guess IDs.

```bash
printf '%s\n' "$HERDR_WORKSPACE_ID" "$HERDR_TAB_ID" "$HERDR_PANE_ID"
herdr pane current --current
herdr pane layout --pane "$HERDR_PANE_ID"
herdr agent list
herdr pane list --workspace "$HERDR_WORKSPACE_ID"
```

From `herdr agent list`, work out which agents you started or are steering in this
session. Those are your fleet. An agent someone else owns is not yours to hand over;
leave it out, or list it as "not mine, do not touch".

Also collect, for each fleet member: agent name, kind, pane ID, working directory, what
you asked it to do, its current state, and what the successor must do with it next
(wait, read output, re-prompt, close).

## 3. Pick the model

Default: the successor runs the same model you are running. Use the exact model ID from
your environment description.

If the user named a model in the skill arguments, use that instead. Accept plain family
names too and map them to the CLI value: `opus`, `sonnet`, `haiku`.

Build the command:

```
danger --model <model>
```

`danger` is the user's fish function for `claude --dangerously-skip-permissions`, with
folder trust pre-accepted for the current directory. Always use `danger`, never plain
`claude`.

## 4. Write the handoff document

Path:

```bash
~/.claude/handoffs/$(date +%Y-%m-%d-%H%M%S)-<short-slug>.md
```

Use the structure in `references/handoff-template.md`. Rules for the content:

- Write for an agent that has never seen this conversation. No "as discussed", no
  pronouns without an antecedent.
- Carry the state, not the transcript. What is done, what is half done, what is next,
  what was decided and why, what was tried and rejected.
- Reference specs, plans, tickets, diffs, and commits by path or URL. Do not paste them.
- Include exact file paths with line numbers for anything the successor must open.
- Include the branch name and whether there is uncommitted work.
- Include verbatim any user instruction that would be lost otherwise, especially
  constraints, preferences, and things the user said not to do.
- Do not repeat what CLAUDE.md, GIT.md, or project memory already say. The successor
  loads those itself.
- Redact secrets, tokens, keys, and personal data.
- The fleet table and the shutdown block are mandatory. They are the parts only you can
  write.

If the user passed a focus in the arguments, tailor the "next steps" section to it.

## 5. Create the successor pane

Split from your own pane, keep the user's focus where it is, and keep the working
directory:

```bash
herdr pane split --current --direction right --cwd "$PWD" --no-focus
```

Use `--direction down` instead when `herdr pane layout` shows your pane is wide but
short, or when a right split would make either column too narrow. Honor a direction the
user asked for.

Read the new pane ID from `.result.pane.pane_id`.

## 6. Start the agent

```bash
herdr pane run <new-pane-id> "danger --model <model>"
```

Then wait for Herdr to recognize the agent. Poll, do not sleep blindly:

```bash
herdr agent get <new-pane-id>
```

Retry every few seconds for up to about 60 seconds. When it resolves, give it a name so
the fleet and the user can address it:

```bash
herdr agent rename <new-pane-id> <successor-name>
```

Pick a short, unique, meaningful name. `[a-z][a-z0-9_-]{0,31}`.

If the agent never appears, read the pane and report what went wrong:

```bash
herdr pane read <new-pane-id> --source recent-unwrapped --lines 60
```

A model ID the CLI rejects is the usual cause. Fall back to the family alias
(`opus`, `sonnet`, `haiku`) and try once more before giving up.

## 7. Hand over

Send one short prompt. The document carries the detail.

```bash
herdr agent prompt <successor-name> "You are taking over this session. Read <handoff-path> now and follow it exactly, including the shutdown instructions at the end." --wait --timeout 180000
```

Then confirm it actually read the doc:

```bash
herdr agent read <successor-name> --source recent-unwrapped --lines 80
```

If the read is truncated because the agent draws on the alternate screen, ask it to
write a one line confirmation to a temp file and read that file instead.

## 8. Report and stand by

Tell the user, in a few lines:

- the handoff document path
- the successor's agent name and pane ID
- the model it is running
- which fleet members it now owns
- that it has been asked to run `/exit` in your pane and close it

Then stop. Do not start new work. Do not close your own pane yourself. The successor
closes you, which proves it is alive and has the context. If the user then asks you to
keep going instead, say the successor is already running and ask which one they want to
keep.

## Safety

- Never close a pane, tab, or workspace you did not create.
- Never run `herdr server stop`.
- Always use `--no-focus`, unless the user asked to be moved to the successor.
- Never pass secrets on the command line or into the handoff document.
