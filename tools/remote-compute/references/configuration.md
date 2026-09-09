# Agentless Gateway Configuration

> Load this when: installing the local MCP server, defining an approved target, or connecting DSH/Codex/Claude to it.

## Boundary

`remote_compute_mcp.py` runs on the operator workstation. It invokes the workstation's
OpenSSH `ssh` and `scp` clients with `shell=False`. The remote machine needs no Harness,
MCP server, LLM runtime, inbound web service, or model credential.

Remote prerequisites:

- non-interactive OpenSSH access through a tested alias;
- POSIX `sh` plus GNU-compatible `sha256sum`, `stat`, `find`, `realpath`, `tail`, and
  `mv`;
- Slurm (`sbatch`, `sacct`, `scancel`) or PBS (`qsub`, `qstat`, `qdel`);
- the computational codes and environment described by `~/.cluster-agents.md`.

The current implementation targets Python 3.11 or newer on Windows/Linux/macOS. On the
operator's Windows machine, use the modern Miniconda interpreter, not a legacy Python
3.6 environment.

## Private config

Copy `examples/config.example.json` outside the repository, for example:

```text
C:\Users\<USER>\.dsh\remote-compute.private.json
```

Replace placeholders locally. Do not commit the resulting file. Start with
`submitEnabled` and `cancelEnabled` false.

Validate without connecting:

```powershell
C:\Users\<USER>\miniconda3\python.exe `
  tools\remote-compute\scripts\remote_compute_mcp.py `
  --config C:\Users\<USER>\.dsh\remote-compute.private.json `
  --check-config
```

`sshAlias` is an alias from the operator's OpenSSH config. Keep the actual hostname,
username, jump host, key path, and port there rather than in the MCP config. The gateway
forces batch authentication and strict host-key checking. `knownHostsFile` may point at
an explicit private known-hosts file; otherwise OpenSSH's normal file is used.

Every target has separate local upload, download, and research-state roots. A path
outside them is rejected before SSH is invoked. `allowedResearchRoots` contains only
project parents whose `.research/decisions.jsonl` records the user approvals accepted
by this target; keep it as narrow as the projects that may actually submit. If omitted,
it defaults to `allowedUploadRoots` for backward compatibility. `remoteRoot` is the only
remote tree the gateway can address and must be an absolute portable POSIX path without
spaces.

## DSH sci preset

Create a user-owned `sci` preset by copying DSH's shipped `standard` preset. After
replacing every `REPLACE_*` token in `examples/dsh-sci.cordis.example.yml`, append that
direct MCP plugin row to `sci/agent.cordis.yml`. Do not include the example's row in a
profile `cordis.patch.yml` unless every preset should see the gateway, and do not edit a
shipped preset.

DSH exposes the tools as
`mcp__aicc-compute__compute_list_targets`,
`mcp__aicc-compute__compute_stage_job`, and so on. `failOnStartupError: false` keeps
literature/writing work available when the private config, Python, SSH, or server is
offline. The longer tool timeout covers bounded file transfer; scheduler jobs themselves
are submitted and polled rather than held open in one MCP call.

The AICC skills remain under the sci preset's skill discovery root. Mounting the MCP
row provides execution capability; it does not replace the `remote-compute`,
`hpc-submit`, engine, or orchestrator skills.

## Generic stdio MCP client

Use absolute paths and keep the config outside the repository:

```json
{
  "mcpServers": {
    "aicc-remote-compute": {
      "command": "C:\\Users\\<USER>\\miniconda3\\python.exe",
      "args": [
        "C:\\path\\to\\AI-Computational-Chemist\\tools\\remote-compute\\scripts\\remote_compute_mcp.py",
        "--config",
        "C:\\Users\\<USER>\\.dsh\\remote-compute.private.json"
      ]
    }
  }
}
```

Use the equivalent stdio-MCP registration surface in DSH, Codex, Claude Code, or
another client. Keep one private gateway config so all local Agents receive the same
target aliases and policy. DSH is still a developer preview, so pin the tested DSH
version and repeat `tools/list` plus the unit/smoke tests after upgrades.

## Activation ladder

1. `--check-config` succeeds.
2. Ordinary `ssh <alias>` succeeds non-interactively and the host fingerprint is pinned.
3. MCP `compute_list_targets`, `compute_probe_target`, and
   `compute_read_cluster_guide` succeed while submission remains disabled.
4. Stage a harmless small bundle into a disposable target root and verify its manifest.
5. Enable `submitEnabled` and submit one minimal scheduler job after human approval.
6. Validate status, log, artifact hash, download, and the engine parser.
7. Enable `cancelEnabled` only after its approval/audit behavior is tested.

Failure must remain loud: an SSH, scheduler, checksum, or policy error never falls back
to local execution.
