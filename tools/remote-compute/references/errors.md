# Remote-Compute Errors

> Load this when: a gateway config, SSH connection, stage, scheduler call, or artifact transfer fails.

| Symptom | Likely cause | Response |
|---|---|---|
| `executable not found` | Windows OpenSSH path is absent/wrong | Verify `ssh.exe`/`scp.exe`; update only the private config. |
| host-key verification failure | host missing/mismatched in known_hosts | Stop; verify the new fingerprint out of band before updating known_hosts. |
| authentication failure with `BatchMode=yes` | key/agent/alias is not ready | Fix OpenSSH config or ssh-agent locally; never add a password to MCP arguments. |
| target/root/path rejected | value is outside policy or not portable | Correct the private roots/job bundle; do not broaden to a drive/home root for convenience. |
| existing remote job directory | duplicate job ID or uncertain prior stage | Inspect it, reconcile provenance, then use a new job ID; do not overwrite. |
| `.incoming-*` remains | transfer/checksum/finalize was interrupted | Inspect it manually under site policy; it is never submitted and the gateway will not reuse it. |
| manifest or checksum-list changed | staged content changed after receipt | Stop and restage under a new job ID after diagnosing the change. |
| `sbatch`/`qsub` missing | wrong login environment or target policy | Read the cluster guide; confirm modules/path without inventing site commands. |
| scheduler returned invalid job ID | warning/banner mixed with command output | Inspect raw SSH behavior and site wrappers; do not guess or fabricate an ID. |
| status missing/unknown | accounting delay, purged history, SSH outage | Query again later and reconcile logs/accounting; never resubmit solely from absence. |
| artifact hash mismatch | file changed, incomplete transfer, or wrong expected hash | Delete only the gateway-created partial (automatic), restat remotely, and diagnose. |
| destination exists | overwrite protection | Choose a new approved destination or obtain separate manual overwrite authorization. |

Do not solve a gateway rejection by adding a raw-shell tool, disabling strict host-key
checking, permitting arbitrary paths, or setting submission/cancellation globally true.
