# Running rsess: Setup, Commands, and Usage Patterns

> Load this when: opening a session, running commands, sending keys, peeking at output, closing sessions, or setting up rsess for a new remote.

## Setup (one-time, per environment)

`rsess` is connection-agnostic: a **target is any ssh destination** — a `Host` alias from `~/.ssh/config`, or `user@host`. Put all connection details (`HostName`, `User`, `Port`, `ProxyJump`, `IdentityFile`, `ControlMaster`) in `~/.ssh/config`. Example:

```sshconfig
Host myserver
    HostName 203.0.113.10
    User alice

# jump-host example (rsess needs no special code for this):
Host behind-jump
    HostName 10.0.0.5
    User alice
    ProxyJump bastion.example.com
```

Then `scripts/rsess open <topic> myserver`. Optional `~/.rsess/config` (sourced sh) holds preferences and short aliases — see the skill root's `config.example`.

## Command reference

```
rsess probe  <target>                      report remote tmux availability/version
rsess open   [--upload-tmux] <topic> <target>
                                           open a per-topic session; prints its NAME
rsess run    <session> <cmd...>            run cmd; returns stdout+stderr and the real exit code
rsess send   <session> <keys...>           raw keys + Enter — for REPLs, daemons, Ctrl-C (C-c)
rsess peek   <session> [lines]             capture last N lines of the live pane (default 120)
rsess list                                 list sessions with alive/dead status
rsess close  <session> [--purge-logs]      kill session + remove its run files (keeps transcript log)
rsess gc                                   prune locally-tracked sessions that are dead remotely
```

`open` prints a session name like `rsess-<topic>-<hash>`; use that exact name as `<session>` for every later call.

## Usage patterns

1. **One session per topic.** Name it for the topic. `open` adds a random hash so names never collide. A session lives on **one host** — if a topic spans hosts, open one session per host.
2. **Minimize sessions.** When you finish a topic, `rsess close` it. If a session's environment has gotten messy (stray env vars, wrong cwd, a broken venv), `close` it and `open` a fresh one.
3. **Default to `run`.** It blocks until the command finishes and returns its real exit code. Output goes to clean per-command files on the remote (`~/.rsess/runs/<session>/<id>.out`), so it's faithful even for large or binary output — no terminal-corruption issues.
4. **Use `send` + `peek` for interactive or long-lived things:** starting a `tail -F`/watch loop, driving a REPL/TUI, or sending control keys (`rsess send <s> C-c`). `send` does not wait or capture. Follow with `peek`.
5. **Long commands:** `run` times out at `RSESS_TIMEOUT` (default 120s). For a slow command, prefix with the env var: `RSESS_TIMEOUT=600 rsess run …`. On timeout the command keeps running in the pane; `peek` to see its state.
6. **File transfer:** scp and rsync work directly with the same target names — no extra setup (see the File transfer section below).

## File transfer

Because rsess targets are standard ssh destinations, file transfer works **with the same target names**, no extra setup:

```bash
# Upload (the target alias goes after the colon, like any scp destination)
scp ./myfile   alice@myserver:/home/alice/

# Download
scp alice@myserver:/var/log/syslog   ./syslog

# rsync with the same alias (ssh ControlMaster sharing also benefits)
rsync -avzP ./project/   alice@myserver:~/project/
```

This also applies to wildcard targets — `scp data.tar.gz gzadmin@t-61763:~/` works through the same jump host and port extraction defined in `~/.ssh/config`.

## Installing tmux on the remote (gated)

If `rsess probe` or `rsess open` reports **no usable tmux**, the bundled static binary in `scripts/tmux` (linux x86-64, musl) can be uploaded. **Ask the user for confirmation before installing anything on a remote.** On approval, re-run with `--upload-tmux`: it uploads the binary to `~/.bin/tmux` and drives it via a dedicated socket (`tmux -L rsess`), isolated from any admin-managed tmux. For non-x86-64 remotes, the user must supply a matching binary.

## Configurable defaults

The optional `~/.rsess/config` (sourced as POSIX sh) can override:

| Variable | Default | Meaning |
|---|---|---|
| `RSESS_SOCKET` | `rsess` | remote `tmux -L` socket name (isolates rsess from admin tmux) |
| `RSESS_TIMEOUT` | `120` | seconds `run` waits before reporting a timeout |
| `RSESS_REMOTE_DIR` | `.rsess` | logs/run files directory under the remote `$HOME` |
| `RSESS_REMOTE_BIN` | `.bin/tmux` | where `--upload-tmux` puts the bundled binary |
| `RSESS_MIN_TMUX` | `1.8` | minimum acceptable system tmux version |
