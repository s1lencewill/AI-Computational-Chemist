# Remote-Compute Tool Contract

> Load this when: building a job bundle, recording MCP results, diagnosing a gateway rejection, or extending the MCP surface.

## Job bundle

`compute_stage_job` accepts one existing local directory beneath a configured upload
root. It rejects empty bundles, symlinks, traversal, non-portable relative paths, excess
file count, and excess bytes. The named scheduler script must already be in the bundle.

Staging adds:

- `AICC_JOB.json` — canonical target, scheduler, submit script, timestamp, file sizes and hashes;
- `SHA256SUMS` — remote transfer verification for every operator-provided file.

`AICC_JOB.json`, `SHA256SUMS`, and `.aicc-submit-started` are reserved gateway names
and are rejected in an operator-provided bundle.

The gateway uploads into a random `.incoming-*` directory, verifies all hashes remotely,
then atomically renames it to `<remoteRoot>/<job_id>`. An existing final job directory is
a hard failure. Retrying after an uncertain transfer uses a new `job_id`; inspect and
clean an abandoned `.incoming-*` directory manually under site policy.

Submission creates `.aicc-submit-started` atomically before invoking the scheduler and
stores the returned scheduler ID beneath it. A second submission attempt for the same
job directory fails. If the SSH response is lost after submission starts, do not remove
the marker or resubmit automatically; reconcile scheduler accounting and the marker
under site policy.

## Tool sequence

```text
compute_list_targets
  -> compute_probe_target
  -> compute_read_cluster_guide
  -> local engine + research pre-submit gates
  -> compute_stage_job
  -> recorded human approval + active lease
  -> compute_submit_job
  -> compute_get_status / compute_read_log
  -> compute_stat_artifact
  -> compute_fetch_artifact
  -> engine parser + scientific validation
```

`compute_submit_job` verifies that the remote `AICC_JOB.json` hash still equals the
staging receipt. It also resolves the supplied project or `.research` directory beneath
an `allowedResearchRoots` entry and requires `approval_ref` to identify exactly one
unsuperseded `.research/decisions.jsonl` row with `kind: approval`, `decision: approved`,
`by: user`, and the supplied `task_id` and `approval_type`. The decisions-file SHA-256
is included in the receipt and audit entry. A submission decision must also contain the
exact staged `manifest_sha256`, preventing a valid approval from authorizing different
inputs. The Agent remains responsible for asking the human before recording that
decision and invoking the mutating tool.

In `.research/`, immutable staging and approved submission should be separate sequential
tasks. This avoids a dependency cycle between `claim_task.py` readiness and an
`expensive_hpc_submission` decision that cannot be bound until staging produces the
manifest hash.

`compute_cancel_job` performs the same local decision verification with a distinct
cancellation approval type and requires the decision's `scheduler_job_id` to match the
requested job. A submission approval must not be reused as cancellation authority.

Scheduler adapters are deliberately narrow: Slurm uses `sbatch`/`sacct`/`scancel`,
PBS uses `qsub`/`qstat`/`qdel`, and LSF uses `bsub`/`bjobs` (falling back to `bhist`)
and `bkill`. LSF submission accepts only the staged script on standard input and parses
the numeric job ID from the canonical `Job <ID>` acknowledgement.

`compute_get_status` returns both `raw_status` and normalized `scheduler_state` plus a
boolean `terminal`. Normalization tolerates wrapped LSF `Status <DONE>` output. These
fields describe only scheduler/process state and never replace the engine parser.

Downloads are two-step. First obtain the server-side size/hash with
`compute_stat_artifact`; then pass that hash to `compute_fetch_artifact`. The download
lands in a randomized partial file, is hashed locally, and is renamed only on a match.
Existing local files are never overwritten.

Before stat, bounded log reads, or download, the gateway requires a regular non-symlink
file whose resolved path remains inside the selected remote job directory. This blocks
a job-created link from turning an artifact request into a read elsewhere on the host.
The check uses POSIX-compatible `test` operands prefixed with `./`; it does not rely on
the nonportable `test --` extension found missing on some HPC login shells.

## Path and command policy

- Tool calls select a target alias, never a hostname or username.
- Remote operations are constructed by the gateway; callers never submit raw shell.
- `job_id`, task IDs, approval types, scheduler job IDs, approval IDs, and relative
  paths use bounded portable character sets.
- Remote job paths are always derived from the configured root plus validated segments.
- OpenSSH is invoked as an argument vector with `shell=False`, batch authentication, and
  strict host-key checking. The remote POSIX shell sees only gateway-generated commands
  with quoted validated paths.

## Audit and `.research/`

The private audit JSONL records probe, guide-read, stage, submit, status, fetch, and
cancel actions. It deliberately does not store credentials, guide contents, job input
contents, or log contents.

Copy durable facts into `.research/`:

- staging manifest SHA-256 and remote-location alias;
- approval decision ID and execution lease ID;
- scheduler and scheduler job ID;
- status observations and timestamps;
- remote and local artifact SHA-256 values;
- engine parser command/status and scientific gate verdict.

Do not interpret scheduler `COMPLETED` as technical convergence or scientific validity.
