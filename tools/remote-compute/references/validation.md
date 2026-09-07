# Remote-Compute Validation

> Load this when: qualifying a new workstation/cluster connection or deciding whether `submitEnabled`/`cancelEnabled` may be turned on.

## Local checks

- Python is 3.11 or newer; run `python -m unittest discover -s
  tools/remote-compute/scripts -p 'test_*.py'`.
- The private config passes `remote_compute_mcp.py --check-config`.
- `ssh -o BatchMode=yes <alias> true` succeeds and strict host-key checking uses the
  expected fingerprint.
- Upload/download roots are narrow project directories, not a drive root, home, or a
  broad shared tree.
- The audit path is private, writable, and outside the repository.

## Read-only target checks

Keep submit/cancel disabled while verifying:

- `compute_list_targets` reveals aliases and policy only, not physical connection data;
- `compute_probe_target` reports the expected Linux host and scheduler command;
- `compute_read_cluster_guide` returns the expected size/hash and current operating guide;
- a missing alias, path traversal, symlink, oversized bundle, or path outside a local
  root fails before mutation;
- an SSH or scheduler error remains an error and never falls back to local execution.
- an invented, duplicated, superseded, non-user, wrong-task, wrong-type, or
  wrong-manifest approval is rejected locally before the scheduler command is
  constructed;

## Harmless scheduler acceptance

After operator approval, enable submission for one target and use a minimal site-approved
job that prints hostname/date and exits. Verify:

1. staging creates exactly one new remote job directory;
2. local and remote manifest SHA-256 match;
3. changing an input, `SHA256SUMS`, or `AICC_JOB.json` blocks submission;
4. the submitted scheduler job ID is recorded in the private audit and `.research/`;
5. a second submit call for the same staged job is rejected by the remote submission
   marker;
6. status reaches a terminal state without a persistent SSH process;
7. log tail is bounded;
8. artifact stat plus download produces matching remote/local SHA-256;
9. an existing local destination is not overwritten.

Only then test an engine smoke job. Engine parser success is separate from scheduler
success. Enable cancellation last and verify it needs both local policy and a distinct,
matching, unsuperseded user approval record.
