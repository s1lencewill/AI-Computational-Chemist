---
name: remote-compute
description: Dispatch, monitor, and retrieve computational chemistry jobs from a local Agent to policy-approved SSH/Slurm/PBS/LSF targets through the AICC remote-compute MCP gateway, without installing an Agent on the server. Use when the reasoning runtime is local but calculation files or scheduler commands must run remotely.
---

# Agentless Remote Compute

Keep the Agent, credentials, workflow state, and scientific decisions on the operator's
machine. The server is an execution target only: OpenSSH, scheduler, computational
codes, and optionally the copied AICC checker/parser scripts. Do not install or launch a
remote DSH/Codex/Claude runtime for this mode.

Use this skill together with `hpc-submit`: this skill owns the transport boundary and
remote artifact identity; `hpc-submit` owns scheduler mechanics; the engine skill owns
scientific preflight and output validation.

## Required workflow

1. Call `compute_list_targets`; use only a configured alias. Never invent a host.
2. Call `compute_probe_target`, then `compute_read_cluster_guide`. Register the latter's
   path, size, hash, target, and timestamp as the accepted `cluster-guide-read` artifact.
3. Prepare a project-local job directory with portable relative paths and its scheduler
   script. Run the engine preflight and `check_pre_submit.py` before submission. When
   `.research/` is used, make immutable staging a separate task with `approval: none`;
   the later submission task depends on its accepted `job-record`.
4. Claim the staging task when its owner directory requires a lease, call
   `compute_stage_job`, and record the returned `manifest_sha256` and remote location in
   the `job-record`. Staging creates a new directory and never overwrites one. Validate,
   accept, and release the staging task before the submission task is claimed.
5. Obtain the required exact human approval and claim the submission task. Pass `research_dir`,
   `task_id`, the recorded decision ID, and its `approval_type` to
   `compute_submit_job`. The gateway verifies the exact unsuperseded user approval in
   `.research/decisions.jsonl`, including a matching `manifest_sha256`; do not invent
   or reuse a mismatched approval ID.
6. Record the returned scheduler job ID immediately. Poll with `compute_get_status` at
   meaningful intervals; use its normalized `scheduler_state` and `terminal` fields for
   control flow, but retain `raw_status` as evidence. A terminal scheduler state is not
   convergence.
7. Use `compute_read_log` for bounded diagnosis. Use `compute_stat_artifact` followed by
   `compute_fetch_artifact` for outputs; the latter requires the observed SHA-256.
8. Run the producing engine's parser, register validation evidence, then apply the
   scientific result gate. Use `compute_cancel_job` only after a recorded cancellation
   approval bound to the exact `scheduler_job_id` and only when local target policy
   enables it.

## Where to find what

| Situation | Go to |
|---|---|
| private Windows configuration, DSH/Codex/Claude MCP examples, first connection | `references/configuration.md` |
| tool contract, job-bundle rules, audit and recovery fields | `references/protocol.md` |
| acceptance ladder before enabling submit/cancel | `references/validation.md` |
| connection, policy, scheduler, transfer, and checksum failures | `references/errors.md` |
| authoritative protocol/SSH/scheduler documentation | `references/resources.md` |
| scheduler templates, queue semantics, recovery | `tools/hpc-submit/` |
| durable remote execution state and `.research/` records | `procedures/research-orchestrator/references/remote-execution.md` |
| MCP implementation | `scripts/remote_compute_mcp.py` |

## Hard guardrails

- The MCP server runs locally. Remote hosts receive no model API key and no Agent runtime.
- Prefer OpenSSH aliases backed by key or SSH-agent authentication. Never put passwords,
  private-key material, hostnames, usernames, or site paths in committed files.
- Target roots and local upload, download, and research-state roots come only from the
  private gateway config. Tool arguments cannot expand them.
- `submitEnabled` and `cancelEnabled` default to false. Enable them per target only after
  read-only probing and a harmless scheduler test succeed.
- Job IDs and bundle paths are portable safe segments. Symlinks, path traversal, spaces,
  control characters, overwrites, and unverified downloads are rejected.
- A manifest hash binds approval to the exact staged input bundle. If it changes, restage
  under a new job ID; never bypass the mismatch. Submission revalidates both the
  checksum-list identity and every staged input hash.
- The MCP audit log is execution evidence, not the `.research/` source of truth. Record
  the corresponding decision, lease, job ID, hashes, and parser verdict in the project.
- Do not expose a generic arbitrary-shell MCP tool as a shortcut. Add a narrow operation
  with validation when a recurring capability is genuinely missing.
