# rsess Validation

> Load this when: setting up rsess for the first time on a target, or verifying a session is healthy before relying on it for HPC work.

## One-time preflight (per remote)

- The rsess script is executable at `scripts/rsess` and the bundled `scripts/tmux` binary is present.
- The target is reachable: `ssh <target> hostname` succeeds without a password prompt (key or agent auth works).
- `rsess probe <target>` reports a usable tmux (system or bundled).

## Per-session preflight

- `rsess open <topic> <target>` completes without error and prints a session name.
- `rsess run <session> hostname` returns the expected remote hostname within a few seconds — confirms the shell is alive and on the right machine.
- `rsess peek <session> 5` shows a clean shell prompt with no error messages from `.bashrc`/`.zshrc` that would interfere with `run` (beware of `set -e`, `exit`-invoking lines, or interactive-only prompts in rc files).

## Before submitting HPC jobs through a session

- The session's working directory is set correctly: `rsess run <session> pwd`.
- Required modules load: `rsess run <session> 'module load <engine> && which <binary>'`.
- Scheduler commands work: `rsess run <session> 'squeue -u $USER'` (or `qstat` equivalent).
- The file-transfer route (scp/rsync, from the local bootstrap) works independently — rsess does not handle file transfer.
