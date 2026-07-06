---
name: rsess
description: Run commands on a REMOTE server through a persistent shell that survives disconnects, by driving a tmux session that lives ON THE REMOTE. Use when you need shell state (cwd, env vars, activated venvs, a running REPL/daemon) to persist across multiple commands on an SSH-reachable host — instead of `ssh host cmd`, which starts a fresh shell every time and loses all state. Do NOT use rsess when the agent is already running on the target machine — run commands directly with the native shell.
---

# rsess

**rsess is for driving a *remote* machine.** If the agent is already running on the target machine (e.g. on the cluster itself), do not use rsess — run commands directly with the native shell; there's no connection to persist and the scheduler handles durability.

The tmux server and the shell run on the **remote**; your machine only sends stateless `ssh <target> "tmux …"` control calls. Two consequences that matter:

- **State persists.** `cd`, `export`, `source venv/bin/activate`, a running REPL — all survive across separate `rsess run` calls (and across your SSH drops), because the shell lives in the remote tmux, not in each ssh.
- **It fails closed.** If the connection drops, a call just errors — it can **never run your command on the local machine instead**. A wrong or unreachable target produces a clean error, not a misfire.

## Required inputs

- An SSH-reachable host (`Host` alias from `~/.ssh/config`, or `user@host`).
- tmux on the remote, or user approval to upload the bundled static binary (`scripts/tmux`, linux x86-64 musl).

## Where to find what

| Situation | Go to |
|---|---|
| open/close sessions, run commands, send keys, peek, file transfer, configurable defaults, tmux upload | `references/running.md` |
| connection fails, tmux missing, session dead, timeout, empty output, disk quota | `references/errors.md` |
| first-use preflight: probe remote, verify tmux, validate a session before HPC work | `references/validation.md` |
| external docs: tmux manual, ssh_config, static build guide | `references/resources.md` |

## Commands (quick reference)

```
rsess probe  <target>                      report remote tmux availability/version
rsess open   [--upload-tmux] <topic> <target>
                                           open a per-topic session; prints its NAME
rsess run    <session> <cmd...>            run cmd; returns stdout+stderr and the real exit code
rsess send   <session> <keys...>           raw keys + Enter — for REPLs, daemons, Ctrl-C (C-c)
rsess peek   <session> [lines]             capture last N lines of the live pane (default 120)
rsess list                                 list sessions with alive/dead status
rsess close  <session> [--purge-logs]      kill session + remove run files (keeps transcript log)
rsess gc                                   prune locally-tracked sessions that are dead remotely
```

`open` prints a session name (`rsess-<topic>-<hash>`); use that exact name as `<session>` for every later call.

## Hard guardrails

- Never `run` a command that calls `exit`, or `set -e` followed by a failing line — it kills the pane's shell. To end a session, use `rsess close`.
- `run` output is captured in clean per-command files on the remote, not through the tmux pane — so large/binary output is faithful, but `peek` won't show it. Read `run` output from its return value.
- Avoid embedding secrets in `run` commands — they land in the remote transcript log (`~/.rsess/runs/<session>/`).
- Confirm destructive remote actions (`rm -rf`, package/service changes, `/etc` edits) before running them.
- Installing the bundled tmux binary on a remote requires explicit user approval. Never install software on a remote unasked.
