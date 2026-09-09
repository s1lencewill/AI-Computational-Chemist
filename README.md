# AI Computational Chemist (AICC)

[English](README.md) | [简体中文](README.zh-CN.md)

A harness-neutral skill framework for reproducible computational chemistry and
materials-science workflows.

AICC helps an AI agent turn a scientific request into a traceable workflow: identify
the calculation, preserve the source method, prepare inputs, obtain human approval,
run locally or on an HPC system, validate the outputs, and assemble report-ready
evidence. It supports Claude Code, Codex, Cursor, opencode, DSH, and custom agent loops
that can discover `SKILL.md` instructions.

The project is designed around two rules:

1. calculations must follow the manuscript, literature, or explicitly approved method;
2. scheduler success is not scientific success—results become reportable only after
   parser, convergence, provenance, and scientific acceptance gates pass.

## Architecture

The Agent does not need to run on the compute server.

```text
Windows workstation
  DSH / Codex / Claude
          |
          | discovers AICC skills and records .research state
          v
  local remote-compute MCP gateway
          |
          | OpenSSH/SCP: bounded files and generated operations only
          v
Linux compute server
  SSH + GNU tools + Slurm/PBS + scientific codes
  no Agent, no MCP service, no model API key
```

Skills carry scientific and operational knowledge. The local MCP gateway supplies a
narrow execution capability. `.research/` remains the durable control-plane record on
the workstation, while the scheduler and calculation files remain on the execution
plane.

## What AICC provides

- peer-review response workflows from manuscript and referee comments to validated
  response-letter and SI material;
- machine-readable research orchestration with task DAGs, decisions, artifacts,
  events, leases, and acceptance gates;
- engine skills for VASP, CP2K, Gaussian, GROMACS, LAMMPS, DeePMD, phonopy, CatMAP,
  LOBSTER, Multiwfn, VASPKIT, OVITO, and related workflows;
- structure preparation and independent structure-review gates;
- local, scheduler, persistent-shell, and agentless remote execution modes;
- deterministic preflight checks and parsers that fail loudly instead of silently
  treating incomplete calculations as results.

## Choose an execution mode

| Situation | Use | Agent on server? |
|---|---|---:|
| calculation runs on the same machine as the Agent | engine skill + `hpc-submit` | already local |
| normal SSH/Slurm/PBS job dispatched from Windows | `remote-compute` + `hpc-submit` | no |
| interactive investigation needs persistent shell state or `tmux` | `rsess` + `hpc-submit` | no |
| organization deliberately deploys its harness on the cluster | native engine/HPC skills | yes |

Use `remote-compute` for the normal agentless path. It exposes specific operations for
target discovery, staging, submission, status, bounded logs, artifact hashing,
retrieval, and cancellation. It deliberately exposes no arbitrary-shell tool.

## Quick start: skills only

Install the collection into the skill directory used by your harness:

```bash
./install.sh --target ~/.codex/skills
./install.sh --target ~/.claude/skills --harness claude --project /path/to/work
```

The installer deploys the skills only. It does not install scientific codes,
pseudopotentials, basis sets, licensed data, schedulers, or container images.

For a manual installation:

- Claude Code: make `procedures/*/` and `tools/*/` discoverable under a Claude skill
  directory and load `AGENTS.md` as the project instruction;
- Codex or another `AGENTS.md`-aware harness: keep `AGENTS.md` at the working-project
  root and copy or link the skill directories into its skill location;
- another agent loop: use each skill's frontmatter `description` for routing and load
  `AGENTS.md` as a system or project instruction.

`knowledge/` is a flat reference library, not a set of skills. Do not install each
knowledge file as an independent tool.

## Quick start: Windows DSH to a compute server

### 1. Prepare local prerequisites

- Python 3.11 or newer; on this workstation use the modern Miniconda environment rather
  than a legacy Python 3.6 environment;
- Windows OpenSSH `ssh.exe` and `scp.exe`;
- a tested OpenSSH alias with non-interactive key or SSH-agent authentication;
- the server fingerprint already verified and present in `known_hosts`.

The remote server needs GNU-compatible `sh`, `sha256sum`, `stat`, `find`, `realpath`,
`tail`, and `mv`, plus Slurm or PBS and the required scientific codes.

### 2. Create a private gateway configuration

Copy the example outside the repository:

```powershell
Copy-Item `
  .\tools\remote-compute\examples\config.example.json `
  "$env:USERPROFILE\.dsh\remote-compute.private.json"
```

Replace the placeholders and set narrow project directories for:

- `allowedUploadRoots`—prepared job bundles;
- `allowedDownloadRoots`—retrieved results;
- `allowedResearchRoots`—projects whose `.research/decisions.jsonl` may authorize
  submission or cancellation;
- `remoteRoot`—the only remote job tree the gateway may address.

Keep `submitEnabled` and `cancelEnabled` set to `false` during initial setup. Never
commit this private file.

Validate it without connecting:

```powershell
C:\Users\REPLACE_USER\miniconda3\python.exe `
  .\tools\remote-compute\scripts\remote_compute_mcp.py `
  --config "$env:USERPROFILE\.dsh\remote-compute.private.json" `
  --check-config
```

### 3. Create the DSH sci preset and register the gateway

In DSH's Agent Presets settings, copy the shipped `standard` preset to a user-owned
preset with id `sci`. Then append the direct plugin row from
[`tools/remote-compute/examples/dsh-sci.cordis.example.yml`](tools/remote-compute/examples/dsh-sci.cordis.example.yml)
to `sci/agent.cordis.yml` and replace every `REPLACE_*` value. The example is a preset
composition row, not a profile `cordis.patch.yml` operation. Do not edit a shipped
preset. Start a new `sci` session after saving the file.

DSH exposes tools such as:

```text
mcp__aicc-compute__compute_list_targets
mcp__aicc-compute__compute_probe_target
mcp__aicc-compute__compute_stage_job
mcp__aicc-compute__compute_submit_job
mcp__aicc-compute__compute_get_status
mcp__aicc-compute__compute_fetch_artifact
```

The same stdio server can be registered in Codex, Claude Code, or another MCP client.
See the complete client examples in
[`tools/remote-compute/references/configuration.md`](tools/remote-compute/references/configuration.md).

### 4. Qualify the connection read-only

Before enabling submission:

1. call `compute_list_targets`;
2. call `compute_probe_target` for a configured alias;
3. call `compute_read_cluster_guide` and register its size and SHA-256 as provenance;
4. stage a harmless bundle with a new job ID;
5. verify the staging manifest and remote directory;
6. only then enable submission for that one target and run a minimal scheduler job.

Failure never falls back to local execution. A missing alias, SSH error, changed
manifest, approval mismatch, or scheduler failure remains a visible error.

### 5. Record approval for the exact staged bundle

After `compute_stage_job` returns `manifest_sha256`, obtain human approval and append an
approval decision to the project's `.research/decisions.jsonl`:

```json
{"decision_id":"D-HPC-001","task_id":"T004","kind":"approval","decision":"approved","by":"user","approval_type":"expensive_hpc_submission","manifest_sha256":"<exact staging SHA-256>","reason":"Approved after reviewing target, method, and expected cost.","created_at":"2026-09-07T12:00:00+08:00"}
```

`compute_submit_job` requires that exact decision, task, approval type, and manifest
hash. A superseded or reusable generic approval is rejected. Cancellation requires a
different `remote_job_cancellation` decision bound to the exact `scheduler_job_id`.

The gateway also creates a remote submission marker before calling the scheduler, so
an interrupted SSH response cannot silently cause an automatic duplicate submission.

## Flagship workflow

```text
manuscript + SI + reviews (+ original calculation archive)
  -> review-response: method fingerprint + comment triage
  -> human approval of calculation plan
  -> per-comment calculations: comp-chem-workflow + engine skills
  -> parser, convergence, provenance, and scientific validation
  -> response letter + SI tables/figures
  -> human approval of final draft
```

New calculations match the manuscript's method fingerprint unless a deviation is
explicitly justified and approved. A result that contradicts the manuscript stops the
workflow and returns to the authors; it is never hidden or reframed as confirmation.

## Research orchestration

`procedures/research-orchestrator/` adds a machine-readable control plane for larger or
multi-agent projects:

- `.research/project.yaml`—project metadata, policy, assumptions, and overall status;
- `.research/tasks/*.yaml`—task dependencies, skills, required references, checks,
  success criteria, and outputs;
- `.research/artifacts.jsonl`—artifact identity, provenance, hashes, validation, and
  acceptance;
- `.research/decisions.jsonl`—human approvals and scientific decisions;
- `.research/events.jsonl`—append-only workflow and recovery history;
- `.research/leases/*.json`—exclusive ownership of expensive or stateful tasks.

The state transitions are intentionally distinct:

```text
completed -> validated -> accepted -> reportable
```

A scheduler's `COMPLETED` state satisfies none of the scientific gates by itself.
Engine parsers and critics must establish convergence and relevance before reports
consume the result.

Structure modeling has an independent review boundary. Surface, defect, adsorbate,
slab, and supported-cluster tasks separate literature precedent, structure generation,
and read-only criticism before an expensive engine task can consume the model.

Agentless job receipts, scheduler IDs, hashes, approval references, and retrieval state
are described in
[`procedures/research-orchestrator/references/remote-execution.md`](procedures/research-orchestrator/references/remote-execution.md).

## Repository layout

```text
AGENTS.md                    global guardrails and routing
STRUCTURE.md                 extension and organization conventions
procedures/
  review-response/           manuscript + reviews -> validated response package
  comp-chem-workflow/        calculation lifecycle and scientific gates
  literature-to-calculation/ literature/SI -> concrete calculation target
  research-orchestrator/     task DAG, artifacts, decisions, events, leases
knowledge/                   tool-independent scientific references
tools/
  structure-prep/            molecular and periodic structure preparation
  vasp/ cp2k/ gaussian/      electronic-structure and quantum-chemistry engines
  gromacs/ lammps/ deepmd/   molecular dynamics and machine-learning potentials
  phonopy/ catmap/ lobster/  phonons, microkinetics, and bonding analysis
  multiwfn/ vaspkit/ ovito/  analysis, post-processing, and visualization
  hpc-submit/                scheduler scripts, monitoring, and recovery
  remote-compute/            local MCP -> agentless SSH/Slurm/PBS execution
  rsess/                     persistent interactive remote shell sessions
  report/                    report and response-package assembly
benchmark/                   peer-review replication cases and evaluations
```

Every procedure and tool follows the structure documented in [`STRUCTURE.md`](STRUCTURE.md):

- `SKILL.md` is a concise routing and workflow entry point;
- `references/` contains detailed operation, validation, error, and provenance rules;
- `examples/` contains sanitized configurations or verified cases;
- `scripts/` contains deterministic preflight checks and parsers.

## Helper-script runtime

Install [`uv`](https://docs.astral.sh/uv/) for helpers with third-party dependencies.
Scripts that need packages such as pymatgen, RDKit, or OVITO declare them inline and can
run in isolated cached environments:

```bash
uv run path/to/script.py ...
```

Pure-standard-library preflight checks and parsers need only a modern Python
interpreter. On offline compute nodes, warm `uv` environments on a connected login node,
place `UV_CACHE_DIR` on shared storage, and run with `uv run --offline`. A prepared
conda/mamba environment is the fallback when PyPI is inaccessible or a package is more
reliable from conda-forge.

Cluster-specific mirror URLs, partitions, modules, code paths, quotas, and job templates
belong in the remote user's `~/.cluster-agents.md`, never in this repository.

## Security model

The agentless gateway is fail-closed:

- callers select configured aliases, never raw hostnames or usernames;
- OpenSSH uses batch authentication and strict host-key checking;
- upload, download, research-state, and remote roots are allowlisted;
- job IDs and relative paths use bounded portable character sets;
- symlinks, path traversal, reserved gateway names, and overwrites are rejected;
- staged inputs and downloads are SHA-256 verified;
- submission approval is bound to the exact manifest;
- submission and cancellation default to disabled per target;
- remote submission is guarded against replay;
- no password, private key, physical hostname, model credential, or licensed file is
  written to project state or the repository.

The gateway audit log is execution evidence, not the scientific source of truth. Copy
durable job facts into `.research/` and run the producing engine's parser before
accepting a result.

Read the full protocol and validation ladder before production use:

- [`tools/remote-compute/references/protocol.md`](tools/remote-compute/references/protocol.md)
- [`tools/remote-compute/references/validation.md`](tools/remote-compute/references/validation.md)
- [`tools/remote-compute/references/errors.md`](tools/remote-compute/references/errors.md)

## Current status

The skill structure, local gateway logic, MCP handshake/tool discovery, Windows command
handling, configuration examples, and existing research-orchestrator workflows are
covered by offline tests. Every new workstation/cluster pair must still complete the
read-only and harmless-job activation ladder before production submission is enabled.

Run the local checks with Python 3.11 or newer:

```bash
python -m unittest discover -s tools/remote-compute/scripts -p "test_*.py"
python procedures/research-orchestrator/scripts/smoke_tests.py
```

The second command requires PyYAML; it may also be run through an environment that
provides that dependency.

## Design principles

1. Skills contain concrete scientific and operational knowledge, not generic prompts.
2. Frontmatter descriptions route tasks without a central hard-coded router.
3. Deterministic checks and parsers take precedence over improvised interpretation.
4. Human approval gates precede expensive, destructive, or scientifically consequential
   actions.
5. Durable task, decision, lease, and artifact state makes work resumable and auditable.
6. Remote compute capability remains narrower than a general remote shell.

## Reference values

INCAR templates, Hubbard U values, convergence thresholds, and force-field defaults are
literature or community starting points, not endorsements. When reproducing a paper or
following group conventions, the cited method or approved group policy wins. Adapting
the reference files to encode a group's reviewed conventions is an intended use.

## Peer-review replication benchmark

`benchmark/` contains five redacted Nature Communications cases with computational
requests preserved and the authors' computational answers withheld. It includes the
task prompt, rubric, mandatory red flags, agent reports, orchestration protocol, design
rationale, and two independent evaluator result sets. See
[`benchmark/README.md`](benchmark/README.md).

## License

This repository is licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
The benchmark fixtures derive from open-access Nature Communications articles under CC
BY 4.0; DOI attribution is provided with each case.

## Citation

If you use this collection or benchmark, cite the repository via `CITATION.cff` and the
accompanying paper:

> R. Wang, J. Cai & J.-C. Liu. *A harness-neutral skill framework for agentic
> computational chemistry evaluated on peer-review-derived tasks.* Manuscript in
> preparation (2026).
