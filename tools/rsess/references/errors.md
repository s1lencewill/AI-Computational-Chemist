# rsess Error Recovery

> Load this when: a connection fails, `run` times out, tmux is missing, a session is dead, or commands produce unexpected empty output.

| Symptom | Likely cause | Fix |
|---|---|---|
| `cannot reach <target> over ssh` | ssh config missing or auth failure | `ssh <target> hostname` manually first; fix `~/.ssh/config` or key/agent |
| `no usable tmux on '<target>'` | tmux too old or not installed | re-run `open` with `--upload-tmux` (after user approval); or install system tmux on the remote |
| `bundled tmux not found` | `scripts/tmux` missing from the skill directory | verify the skill directory is intact; the bundled binary is a static linux x86-64 ELF |
| `uploaded tmux not runnable on remote` | architecture mismatch (bundled binary is x86-64) or missing libc | for non-x86-64 remotes, source a matching static tmux binary; for very old kernels the musl binary may also fail — test manually |
| `failed to start remote tmux session` | tmux server crashed, disk full, or `$HOME` unwritable on remote | `ssh <target> "df -h ~ && tmux -L rsess new -d -s test 'echo ok'"` to isolate |
| `run` returns empty output | command produced no stdout, or the run file was lost (rare) | `peek` to check pane state; re-run with `>` redirection inside the command to a known file |
| `run` times out (exit 124) | command ran longer than `RSESS_TIMEOUT` | the command is still running; `peek` to check progress or `RSESS_TIMEOUT=600 rsess run ...` for longer runs |
| `send` appears to do nothing | `send` is fire-and-forget (no wait, no capture) | follow with `peek` to see the result |
| Session listed as `DEAD` | remote tmux session was killed (reboot, OOM, manual `tmux kill-session`) | `rsess close <session>` to clean up locally; open a fresh session |
| `Disk quota exceeded` on remote | `~/.rsess` transcript logs growing unbounded | `rsess close <session> --purge-logs` periodically; adjust `RSESS_REMOTE_DIR` to a scratch volume if needed |
| Command runs on the wrong host / local machine | rsess resolves the target from its session metadata, not from ambient state — this should not happen unless the session was opened with the wrong target | `rsess close` and re-`open` with the correct target; verify with `rsess probe <target>` first |
| `run` output corrupted (wrapped lines, escape codes) | tmux pane-width wrapping or terminal escape leakage | rsess captures `run` output through per-command files, not the pane — this should be a non-issue by design; if it occurs, check for `script`/`tee` interference in the remote shell's rc files |
