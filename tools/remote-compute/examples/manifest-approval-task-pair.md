# Manifest-Bound Remote Submission Task Pair

Use two sequential `.research/tasks/*.yaml` nodes when submission approval must contain
the manifest SHA-256 returned by `compute_stage_job`. Replace IDs, paths, checks, and
roles with project-specific values.

The staging task is claimable without submission authority:

```yaml
schema_version: 1
id: T020
title: Stage immutable engine bundle
role: engine-runner
skill: remote-compute
status: proposed
depends_on: [T019]
approval: none
inputs:
  - artifact_id: accepted-engine-inputs
    min_status: accepted
can_read:
  - artifact_type: engine-input-set
can_write:
  - artifact_type: job-record
cannot:
  - submit the staged job
outputs_expected:
  - artifact_id: staged-job-record
    type: job-record
    path: work/jobs/T020.json
success_criteria:
  - compute_stage_job returns a manifest SHA-256
  - the job record contains only an approved target alias and portable job ID
required_refs:
  - tools/remote-compute/SKILL.md
required_checks: []
release_gates: []
execution_policy:
  mode: single_owner
  allow_parallel_subagents: false
  requires_claim: true
  lease_ttl_minutes: 60
  heartbeat_interval_minutes: 10
  owner_dir: work/runs/T020/
  exclusive_paths: [work/runs/T020/]
assumptions: []
provenance: []
```

After T020 is validated, accepted, and released, show the exact target, inputs, cost,
portable job ID, and manifest SHA-256 to the user. Record their authorization as:

```json
{"decision_id":"D-HPC-020","task_id":"T021","kind":"approval","decision":"approved","by":"user","approval_type":"expensive_hpc_submission","manifest_sha256":"<exact-sha256>","reason":"Approved after reviewing the exact staged job.","created_at":"<timestamp>"}
```

Then the submission and monitoring task becomes claimable:

```yaml
schema_version: 1
id: T021
title: Submit, monitor, retrieve, and validate staged job
role: engine-runner
skill: hpc-submit
status: proposed
depends_on: [T020]
approval: expensive_hpc_submission
inputs:
  - artifact_id: staged-job-record
    min_status: validated
can_read:
  - artifact_type: job-record
can_write:
  - artifact_type: job-record
  - artifact_type: parser-result
cannot:
  - submit a manifest not named by the approval
  - treat a terminal scheduler state as engine convergence
outputs_expected:
  - artifact_id: engine-parser-result
    type: parser-result
    path: work/results/T021.json
success_criteria:
  - the scheduler job ID is recorded immediately
  - fetched outputs match remote SHA-256 values
  - the engine parser passes before result acceptance
required_refs:
  - tools/hpc-submit/SKILL.md
  - tools/remote-compute/SKILL.md
required_checks: []
release_gates: []
execution_policy:
  mode: single_owner
  allow_parallel_subagents: false
  requires_claim: true
  lease_ttl_minutes: 60
  heartbeat_interval_minutes: 10
  owner_dir: work/runs/T020/
  exclusive_paths: [work/runs/T020/]
assumptions: []
provenance:
  - work/jobs/T020.json
```

The two leases never overlap. Staging produces the approval binding; submission consumes
it. A changed bundle must be staged under a new portable job ID and approved again.
