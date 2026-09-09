# Remote-Compute Examples

`config.example.json` is a non-secret Windows workstation template. Copy it outside the
repository, replace `REPLACE_USER` and the placeholder research roots, and keep submit
and cancellation disabled through the read-only validation stage. Never commit the
resulting private file.

This directory intentionally contains no live hostname, username, key, scheduler
account, partition, module, licensed-code path, or runnable production job.

`dsh-sci.cordis.example.yml` is a direct stdio MCP plugin row for the user-owned DSH
`sci` preset's `agent.cordis.yml`. It is not a profile `cordis.patch.yml` operation.
Replace every `REPLACE_*` token and keep the private target config outside the repository
before mounting it.
