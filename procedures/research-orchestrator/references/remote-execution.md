# Agentless Remote Execution State

> Load this when: a local Agent stages, submits, monitors, resumes, or retrieves a job through `remote-compute`.

The `.research/` directory remains the project control-plane source of truth on the
operator workstation. The remote server is an execution plane: it receives an immutable
job bundle and returns scheduler/process evidence. No DSH/Codex/Claude runtime or model
credential is installed there.

## Before staging

- Engine inputs passed their scientific and deterministic preflight.
- Required plan/structure gates and `cluster-guide-read` artifact are accepted.
- The task names `remote-compute` or `hpc-submit`, the approved target alias, scheduler,
  unique job ID, and expected output types.
- The task's owner directory is protected by an active lease when
  `execution_policy.requires_claim` is true.

Manifest-bound submission needs two sequential task nodes. The staging node has
`approval: none`, may hold the owner-directory lease while calling
`compute_stage_job`, and produces the validated `job-record`. After it is accepted and
its lease released, the submission/monitoring node depends on that record, requires
`approval: expensive_hpc_submission`, and is claimed only after the user's decision is
bound to the exact `manifest_sha256`. Combining both phases under the submission
approval creates a readiness cycle: the approval needs a manifest that the unready task
has not been allowed to stage.

## Job-record artifact

Register the staging receipt as a project-local JSON/Markdown artifact and index it in
`artifacts.jsonl` as `type: job-record`. The registry `path` remains project-root-relative;
do not replace it with an SSH URI. Recommended fields:

```json
{
  "artifact_id": "job-record-T004-wave1",
  "type": "job-record",
  "path": "work/jobs/T004-wave1.json",
  "produced_by": "T004",
  "status": "validated",
  "created_at": "2026-09-07T00:00:00+08:00",
  "provenance": ["engine-preflight", "structure-gate", "cluster-guide-read"],
  "content_hash": "<AICC_JOB.json SHA-256>",
  "lease_id": "<lease-id>",
  "remote_location": {
    "kind": "ssh",
    "target": "approved-alias",
    "job_id": "project-T004-wave1"
  }
}
```

After submission, update the project-local job-record file and append a new
`job_submitted` event containing the scheduler, scheduler job ID, manifest hash,
approval decision ID, target alias, job ID, and lease ID. Never store hostname,
username, private root path, key path, password, or token in `.research/`.

The preceding approval decision must contain `approval_type:
expensive_hpc_submission` and the exact staging `manifest_sha256`. A later cancellation
uses a separate `approval_type: remote_job_cancellation` decision bound to the exact
`scheduler_job_id`; neither authority is transferable to another bundle or job.

## Monitoring and recovery

- Poll the scheduler at meaningful intervals; do not hold an SSH session open for a
  scheduler-managed job. Persist the normalized scheduler state plus the raw scheduler
  response; wrapped LSF long output, for example, may split `DONE` across lines.
- Heartbeat the AICC execution lease while an owned monitoring turn is active. A closed
  local Agent does not stop the scheduler job; reconcile the lease and scheduler state
  on resume.
- `COMPLETED` is process evidence only. Fetch or remotely run the engine parser before
  marking the task `validated`.
- An unknown status, SSH outage, or stale lease is not permission to resubmit. Reconnect,
  query accounting, inspect the remote job record/logs, and record a recovery decision.

## Artifacts

Large remote files may stay remote. A project-local artifact or job record may include:

```json
{
  "remote_location": {
    "kind": "ssh",
    "target": "approved-alias",
    "job_id": "project-T004-wave1",
    "path": "results/OUTCAR"
  },
  "content_hash": "<remote SHA-256>",
  "size_bytes": 123456789,
  "retrieval": "on-demand"
}
```

When a file is retrieved, record the local project-relative path plus the matching
remote/local SHA-256. Reports should consume compact parser results and selected
evidence, not force retrieval of every trajectory, wavefunction, or checkpoint file.
