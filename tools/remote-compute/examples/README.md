# Remote-Compute Examples

`config.example.json` is a non-secret Windows workstation template. Copy it outside the
repository, replace `REPLACE_USER` and the placeholder research roots, and keep submit
and cancellation disabled through the read-only validation stage. Never commit the
resulting private file.

This directory intentionally contains no live hostname, username, key, scheduler
account, partition, module, licensed-code path, or runnable production job.

`dsh-sci.cordis.example.yml` is a default-off-by-configuration stdio MCP row for the
user-owned DSH `sci` preset. Replace every `REPLACE_*` token and keep the private target
config outside the repository before mounting it.

`manifest-approval-task-pair.md` shows the required two-task `.research/` pattern for
immutable staging followed by exact manifest-bound submission approval. It contains no
site-specific target or scheduler values.
