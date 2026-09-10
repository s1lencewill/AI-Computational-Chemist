#!/usr/bin/env python3
"""Policy-gated, agentless SSH/SFTP execution core for AICC."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Protocol


SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SAFE_APPROVAL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
SAFE_SSH_ALIAS = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._@-]{0,254}$")
SAFE_REMOTE_ROOT = re.compile(r"^/[A-Za-z0-9._/@+-]+(?:/[A-Za-z0-9._@+-]+)*$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
RESERVED_BUNDLE_NAMES = {"AICC_JOB.json", "SHA256SUMS", ".aicc-submit-started"}

SLURM_TERMINAL_STATES = {
    "BOOT_FAIL",
    "CANCELLED",
    "COMPLETED",
    "DEADLINE",
    "FAILED",
    "NODE_FAIL",
    "OUT_OF_MEMORY",
    "PREEMPTED",
    "REVOKED",
    "SPECIAL_EXIT",
    "TIMEOUT",
}
PBS_TERMINAL_STATES = {"C", "F"}
LSF_TERMINAL_STATES = {"DONE", "EXIT", "ZOMBI"}


class GatewayError(RuntimeError):
    """A safe, user-visible gateway failure."""


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


class Runner(Protocol):
    def run(self, argv: list[str], timeout_seconds: int) -> CommandResult: ...


class SubprocessRunner:
    def run(self, argv: list[str], timeout_seconds: int) -> CommandResult:
        try:
            completed = subprocess.run(
                argv,
                shell=False,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise GatewayError(f"executable not found: {argv[0]}") from exc
        except subprocess.TimeoutExpired as exc:
            raise GatewayError(f"command timed out after {timeout_seconds}s") from exc
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def _integer(value: Any, label: str, minimum: int, maximum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not minimum <= value <= maximum:
        raise GatewayError(f"{label} must be an integer between {minimum} and {maximum}")
    return value


def _boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise GatewayError(f"{label} must be true or false")
    return value


def _absolute_local_path(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise GatewayError(f"{label} must be a non-empty absolute path")
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise GatewayError(f"{label} must be absolute")
    return path.resolve(strict=False)


def _path_list(value: Any, label: str) -> tuple[Path, ...]:
    if not isinstance(value, list) or not value:
        raise GatewayError(f"{label} must be a non-empty list of absolute paths")
    return tuple(_absolute_local_path(item, f"{label}[]") for item in value)


def _safe_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise GatewayError(f"{label} must match {SAFE_ID.pattern}")
    return value


def _safe_relative(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise GatewayError(f"{label} must be a non-empty relative POSIX path")
    if any(ord(char) < 32 for char in value) or "\\" in value or " " in value:
        raise GatewayError(f"{label} must be a portable path without spaces, controls, or backslashes")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise GatewayError(f"{label} must stay inside the job directory")
    if any(not re.fullmatch(r"[A-Za-z0-9._@+=-]+", part) for part in path.parts):
        raise GatewayError(f"{label} contains an unsupported path character")
    return path.as_posix()


def _inside(path: Path, roots: tuple[Path, ...], label: str) -> Path:
    resolved = path.expanduser().resolve(strict=False)
    for root in roots:
        try:
            resolved.relative_to(root)
            return resolved
        except ValueError:
            continue
    raise GatewayError(f"{label} is outside the configured local roots")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_scheduler_state(scheduler: str, raw_status: str) -> tuple[str, bool]:
    """Return a stable scheduler state without interpreting engine convergence."""
    state = "UNKNOWN"
    if scheduler == "slurm":
        for line in raw_status.splitlines():
            fields = line.strip().split("|")
            if len(fields) >= 2 and fields[1].strip():
                state = re.split(r"[ +]", fields[1].strip().upper(), maxsplit=1)[0]
                break
        return state, state in SLURM_TERMINAL_STATES

    if scheduler == "pbs":
        match = re.search(r"^\s*job_state\s*=\s*([A-Za-z])\s*$", raw_status, re.M)
        if match:
            state = match.group(1).upper()
        return state, state in PBS_TERMINAL_STATES

    # LSF long output wraps at the terminal width, including inside
    # `Status <DONE>`. Collapse whitespace inside the status token only.
    match = re.search(r"Status\s*<([^>]+)>", raw_status, re.I | re.S)
    if match:
        state = re.sub(r"\s+", "", match.group(1)).upper()
    elif re.search(r"\bDone successfully\b", raw_status, re.I):
        state = "DONE"
    elif re.search(r"\bExited\b", raw_status, re.I):
        state = "EXIT"
    return state, state in LSF_TERMINAL_STATES


@dataclass(frozen=True)
class Target:
    name: str
    ssh_alias: str
    scheduler: str
    login_shell: bool
    remote_root: str
    allowed_upload_roots: tuple[Path, ...]
    allowed_download_roots: tuple[Path, ...]
    allowed_research_roots: tuple[Path, ...]
    known_hosts_file: Path | None
    connect_timeout_seconds: int
    command_timeout_seconds: int
    max_upload_files: int
    max_upload_bytes: int
    max_text_bytes: int
    submit_enabled: bool
    cancel_enabled: bool

    @classmethod
    def parse(cls, name: str, value: Any) -> "Target":
        if not SAFE_ID.fullmatch(name):
            raise GatewayError(f"invalid target name: {name}")
        if not isinstance(value, dict):
            raise GatewayError(f"target {name} must be an object")
        ssh_alias = value.get("sshAlias")
        if not isinstance(ssh_alias, str) or not SAFE_SSH_ALIAS.fullmatch(ssh_alias):
            raise GatewayError(f"target {name}.sshAlias is not a safe OpenSSH alias")
        scheduler = value.get("scheduler")
        if scheduler not in {"slurm", "pbs", "lsf"}:
            raise GatewayError(f"target {name}.scheduler must be slurm, pbs, or lsf")
        remote_root = value.get("remoteRoot")
        if not isinstance(remote_root, str) or not SAFE_REMOTE_ROOT.fullmatch(remote_root):
            raise GatewayError(
                f"target {name}.remoteRoot must be an absolute portable POSIX path without spaces"
            )
        if ".." in PurePosixPath(remote_root).parts:
            raise GatewayError(f"target {name}.remoteRoot must not contain ..")
        known_hosts = value.get("knownHostsFile")
        known_hosts_file = (
            None
            if known_hosts is None or known_hosts == ""
            else _absolute_local_path(known_hosts, f"target {name}.knownHostsFile")
        )
        return cls(
            name=name,
            ssh_alias=ssh_alias,
            scheduler=scheduler,
            login_shell=_boolean(value.get("loginShell", True), f"target {name}.loginShell"),
            remote_root=remote_root.rstrip("/"),
            allowed_upload_roots=_path_list(
                value.get("allowedUploadRoots"), f"target {name}.allowedUploadRoots"
            ),
            allowed_download_roots=_path_list(
                value.get("allowedDownloadRoots"), f"target {name}.allowedDownloadRoots"
            ),
            allowed_research_roots=_path_list(
                value.get("allowedResearchRoots", value.get("allowedUploadRoots")),
                f"target {name}.allowedResearchRoots",
            ),
            known_hosts_file=known_hosts_file,
            connect_timeout_seconds=_integer(
                value.get("connectTimeoutSeconds", 15),
                f"target {name}.connectTimeoutSeconds",
                1,
                300,
            ),
            command_timeout_seconds=_integer(
                value.get("commandTimeoutSeconds", 120),
                f"target {name}.commandTimeoutSeconds",
                1,
                3600,
            ),
            max_upload_files=_integer(
                value.get("maxUploadFiles", 2000), f"target {name}.maxUploadFiles", 1, 100000
            ),
            max_upload_bytes=_integer(
                value.get("maxUploadBytes", 2 * 1024**3),
                f"target {name}.maxUploadBytes",
                1,
                100 * 1024**3,
            ),
            max_text_bytes=_integer(
                value.get("maxTextBytes", 200000),
                f"target {name}.maxTextBytes",
                1024,
                10 * 1024**2,
            ),
            submit_enabled=_boolean(value.get("submitEnabled", False), f"target {name}.submitEnabled"),
            cancel_enabled=_boolean(value.get("cancelEnabled", False), f"target {name}.cancelEnabled"),
        )


@dataclass(frozen=True)
class GatewayConfig:
    config_path: Path
    ssh_executable: str
    scp_executable: str
    audit_log: Path
    targets: dict[str, Target]

    @classmethod
    def load(cls, path: Path) -> "GatewayConfig":
        try:
            resolved = path.expanduser().resolve(strict=True)
            raw = json.loads(resolved.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, RuntimeError) as exc:
            raise GatewayError(f"cannot read gateway config: {exc}") from exc
        if not isinstance(raw, dict) or raw.get("schemaVersion") != 1:
            raise GatewayError("gateway config must be an object with schemaVersion 1")
        ssh_executable = raw.get("sshExecutable", "ssh")
        scp_executable = raw.get("scpExecutable", "scp")
        if not isinstance(ssh_executable, str) or not ssh_executable.strip():
            raise GatewayError("sshExecutable must be a non-empty string")
        if not isinstance(scp_executable, str) or not scp_executable.strip():
            raise GatewayError("scpExecutable must be a non-empty string")
        audit_value = raw.get("auditLog")
        if audit_value is None:
            audit_log = resolved.with_name("remote-compute-audit.jsonl")
        else:
            audit_log = _absolute_local_path(audit_value, "auditLog")
        target_values = raw.get("targets")
        if not isinstance(target_values, dict) or not target_values:
            raise GatewayError("targets must be a non-empty object")
        targets = {name: Target.parse(name, value) for name, value in target_values.items()}
        return cls(resolved, ssh_executable, scp_executable, audit_log, targets)


class RemoteComputeGateway:
    def __init__(self, config: GatewayConfig, runner: Runner | None = None):
        self.config = config
        self.runner = runner or SubprocessRunner()

    def _target(self, name: Any) -> Target:
        if not isinstance(name, str) or name not in self.config.targets:
            raise GatewayError("target must be one of the configured target aliases")
        return self.config.targets[name]

    def _ssh_base(self, target: Target) -> list[str]:
        argv = [
            self.config.ssh_executable,
            "-T",
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            f"ConnectTimeout={target.connect_timeout_seconds}",
        ]
        if target.known_hosts_file is not None:
            argv.extend(["-o", f"UserKnownHostsFile={target.known_hosts_file}"])
        return argv

    def _scp_base(self, target: Target) -> list[str]:
        argv = [
            self.config.scp_executable,
            "-B",
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            f"ConnectTimeout={target.connect_timeout_seconds}",
        ]
        if target.known_hosts_file is not None:
            argv.extend(["-o", f"UserKnownHostsFile={target.known_hosts_file}"])
        return argv

    def _run(self, argv: list[str], timeout_seconds: int, label: str) -> CommandResult:
        result = self.runner.run(argv, timeout_seconds)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "no diagnostic output").strip()
            if len(detail) > 2000:
                detail = detail[-2000:]
            raise GatewayError(f"{label} failed with exit {result.returncode}: {detail}")
        return result

    def _remote_shell(self, target: Target, script: str, label: str) -> CommandResult:
        shell_flag = "-lc" if target.login_shell else "-c"
        remote_command = f"sh {shell_flag} {shlex.quote(script)}"
        argv = self._ssh_base(target) + ["--", target.ssh_alias, remote_command]
        return self._run(argv, target.command_timeout_seconds, label)

    def _job_dir(self, target: Target, job_id: Any) -> tuple[str, str]:
        safe_job_id = _safe_id(job_id, "job_id")
        return safe_job_id, f"{target.remote_root}/{safe_job_id}"

    def _audit(self, action: str, **fields: Any) -> None:
        row = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "action": action,
            **fields,
        }
        self.config.audit_log.parent.mkdir(parents=True, exist_ok=True)
        with self.config.audit_log.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    def list_targets(self) -> dict[str, Any]:
        return {
            "targets": [
                {
                    "target": target.name,
                    "scheduler": target.scheduler,
                    "login_shell": target.login_shell,
                    "submit_enabled": target.submit_enabled,
                    "cancel_enabled": target.cancel_enabled,
                }
                for target in sorted(self.config.targets.values(), key=lambda item: item.name)
            ]
        }

    def probe_target(self, target_name: Any) -> dict[str, Any]:
        target = self._target(target_name)
        scheduler_command = {
            "slurm": "sbatch",
            "pbs": "qsub",
            "lsf": "bsub",
        }[target.scheduler]
        script = (
            "set -eu; "
            "printf 'host='; hostname; "
            "printf 'kernel='; uname -s; "
            f"if test -d {shlex.quote(target.remote_root)}; then echo 'root_exists=yes'; "
            "else echo 'root_exists=no'; fi; "
            f"if command -v {scheduler_command} >/dev/null 2>&1; then "
            f"echo 'scheduler_command={scheduler_command}'; else echo 'scheduler_command=missing'; fi"
        )
        result = self._remote_shell(target, script, "target probe")
        self._audit("target_probed", target=target.name)
        return {"target": target.name, "scheduler": target.scheduler, "facts": result.stdout.strip()}

    def read_cluster_guide(self, target_name: Any) -> dict[str, Any]:
        target = self._target(target_name)
        script = (
            "set -eu; p=\"$HOME/.cluster-agents.md\"; test -f \"$p\"; "
            "size=$(wc -c < \"$p\"); hash=$(sha256sum \"$p\" | awk '{print $1}'); "
            "printf '__AICC_META__ %s %s\\n' \"$size\" \"$hash\"; "
            f"head -c {target.max_text_bytes} \"$p\""
        )
        result = self._remote_shell(target, script, "cluster guide read")
        first, separator, content = result.stdout.partition("\n")
        match = re.fullmatch(r"__AICC_META__\s+(\d+)\s+([a-f0-9]{64})", first.strip())
        if not separator or not match:
            raise GatewayError("cluster guide response did not contain valid metadata")
        size = int(match.group(1))
        self._audit("cluster_guide_read", target=target.name, size_bytes=size, sha256=match.group(2))
        return {
            "target": target.name,
            "path": "remote:~/.cluster-agents.md",
            "size_bytes": size,
            "sha256": match.group(2),
            "truncated": size > target.max_text_bytes,
            "content": content,
        }

    def _scan_upload(self, source: Path, target: Target) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        total = 0
        for path in sorted(source.rglob("*")):
            if path.is_symlink():
                raise GatewayError(f"job bundle contains a symlink: {path.relative_to(source)}")
            if path.relative_to(source).parts[0] in RESERVED_BUNDLE_NAMES:
                raise GatewayError(
                    f"job bundle uses reserved gateway name: {path.relative_to(source).parts[0]}"
                )
            if not path.is_file():
                continue
            relative = _safe_relative(path.relative_to(source).as_posix(), "job bundle path")
            size = path.stat().st_size
            total += size
            rows.append({"path": relative, "size_bytes": size, "sha256": _sha256_file(path)})
            if len(rows) > target.max_upload_files:
                raise GatewayError("job bundle exceeds maxUploadFiles")
            if total > target.max_upload_bytes:
                raise GatewayError("job bundle exceeds maxUploadBytes")
        if not rows:
            raise GatewayError("job bundle is empty")
        return rows

    def stage_job(
        self, target_name: Any, job_id: Any, input_dir: Any, submit_script: Any
    ) -> dict[str, Any]:
        target = self._target(target_name)
        safe_job_id, final_dir = self._job_dir(target, job_id)
        script_name = _safe_relative(submit_script, "submit_script")
        if not isinstance(input_dir, str):
            raise GatewayError("input_dir must be a local directory path")
        source = _inside(Path(input_dir), target.allowed_upload_roots, "input_dir")
        if not source.is_dir():
            raise GatewayError("input_dir does not exist or is not a directory")
        files = self._scan_upload(source, target)
        if script_name not in {row["path"] for row in files}:
            raise GatewayError("submit_script is not present in input_dir")

        checksum_lines = [f"{row['sha256']}  {row['path']}" for row in files]
        checksum_bytes = ("\n".join(checksum_lines) + "\n").encode("utf-8")
        manifest = {
            "schema_version": 1,
            "job_id": safe_job_id,
            "target": target.name,
            "scheduler": target.scheduler,
            "submit_script": script_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "checksums_sha256": hashlib.sha256(checksum_bytes).hexdigest(),
            "files": files,
        }
        manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
        incoming_name = f".incoming-{safe_job_id}-{uuid.uuid4().hex[:10]}"
        incoming_dir = f"{target.remote_root}/{incoming_name}"

        prepare = (
            "set -eu; umask 077; "
            f"mkdir -p -- {shlex.quote(target.remote_root)}; "
            f"test ! -e {shlex.quote(final_dir)}; test ! -e {shlex.quote(incoming_dir)}"
        )
        self._remote_shell(target, prepare, "remote staging preflight")

        with tempfile.TemporaryDirectory(prefix="aicc-stage-") as temp_name:
            staging = Path(temp_name) / incoming_name
            shutil.copytree(source, staging, symlinks=False)
            (staging / "AICC_JOB.json").write_bytes(manifest_bytes)
            (staging / "SHA256SUMS").write_bytes(checksum_bytes)
            destination = f"{target.ssh_alias}:{target.remote_root}/"
            scp_argv = self._scp_base(target) + ["-r", str(staging), destination]
            self._run(scp_argv, target.command_timeout_seconds, "job upload")

        finalize = (
            "set -eu; "
            f"(cd {shlex.quote(incoming_dir)} && sha256sum -c -- SHA256SUMS >/dev/null); "
            f"mv -T --no-clobber -- {shlex.quote(incoming_dir)} {shlex.quote(final_dir)}; "
            f"test ! -e {shlex.quote(incoming_dir)}"
        )
        self._remote_shell(target, finalize, "remote checksum/finalize")
        total_bytes = sum(int(row["size_bytes"]) for row in files)
        self._audit(
            "job_staged",
            target=target.name,
            job_id=safe_job_id,
            manifest_sha256=manifest_sha256,
            file_count=len(files),
            total_bytes=total_bytes,
        )
        return {
            "target": target.name,
            "job_id": safe_job_id,
            "scheduler": target.scheduler,
            "manifest_sha256": manifest_sha256,
            "file_count": len(files),
            "total_bytes": total_bytes,
            "remote_location": {"kind": "ssh", "target": target.name, "job_id": safe_job_id},
            "next": "run scientific/pre-submit gates, obtain approval, then call compute_submit_job",
        }

    def _remote_manifest_sha256(self, target: Target, job_dir: str) -> str:
        result = self._remote_shell(
            target,
            f"set -eu; sha256sum -- {shlex.quote(job_dir + '/AICC_JOB.json')}",
            "remote manifest hash",
        )
        digest = result.stdout.strip().split(maxsplit=1)[0] if result.stdout.strip() else ""
        if not SHA256.fullmatch(digest):
            raise GatewayError("remote manifest hash response is invalid")
        return digest

    def _verify_user_approval(
        self,
        target: Target,
        research_dir: Any,
        task_id: Any,
        approval_ref: Any,
        approval_type: Any,
        binding_field: str,
        binding_value: str,
    ) -> dict[str, str]:
        if not isinstance(research_dir, str):
            raise GatewayError("research_dir must be a local project or .research directory")
        root = _inside(Path(research_dir), target.allowed_research_roots, "research_dir")
        state_dir = root if root.name == ".research" else root / ".research"
        decisions_path = _inside(
            state_dir / "decisions.jsonl", target.allowed_research_roots, "decisions.jsonl"
        )
        if not decisions_path.is_file():
            raise GatewayError("research_dir has no readable .research/decisions.jsonl")
        safe_task = _safe_id(task_id, "task_id")
        if not isinstance(approval_ref, str) or not SAFE_APPROVAL.fullmatch(approval_ref):
            raise GatewayError("approval_ref must identify a recorded approval decision")
        safe_type = _safe_id(approval_type, "approval_type")
        rows: list[dict[str, Any]] = []
        try:
            decisions_bytes = decisions_path.read_bytes()
            decisions_text = decisions_bytes.decode("utf-8")
            for number, line in enumerate(decisions_text.splitlines(), 1):
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError(f"line {number} is not an object")
                rows.append(row)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise GatewayError(f"cannot validate approval decisions: {exc}") from exc
        matches = [row for row in rows if row.get("decision_id") == approval_ref]
        if len(matches) != 1:
            raise GatewayError("approval_ref must identify exactly one decision")
        row = matches[0]
        expected = {
            "kind": "approval",
            "decision": "approved",
            "by": "user",
            "task_id": safe_task,
            "approval_type": safe_type,
        }
        mismatches = [key for key, value in expected.items() if row.get(key) != value]
        if mismatches:
            raise GatewayError(
                "approval decision does not match the required user/task/type fields: "
                + ", ".join(mismatches)
            )
        if row.get(binding_field) != binding_value:
            raise GatewayError(
                f"approval decision is not bound to the requested {binding_field}"
            )
        if any(item.get("supersedes") == approval_ref for item in rows):
            raise GatewayError("approval decision was superseded")
        return {
            "approval_ref": approval_ref,
            "approval_type": safe_type,
            "task_id": safe_task,
            "decisions_sha256": hashlib.sha256(decisions_bytes).hexdigest(),
        }

    def submit_job(
        self,
        target_name: Any,
        job_id: Any,
        manifest_sha256: Any,
        research_dir: Any,
        task_id: Any,
        approval_ref: Any,
        approval_type: Any,
    ) -> dict[str, Any]:
        target = self._target(target_name)
        if not target.submit_enabled:
            raise GatewayError("submission is disabled for this target by local policy")
        safe_job_id, job_dir = self._job_dir(target, job_id)
        if not isinstance(manifest_sha256, str) or not SHA256.fullmatch(manifest_sha256):
            raise GatewayError("manifest_sha256 must be a lowercase SHA-256 digest")
        if approval_type != "expensive_hpc_submission":
            raise GatewayError(
                "approval_type must be expensive_hpc_submission for job submission"
            )
        approval = self._verify_user_approval(
            target,
            research_dir,
            task_id,
            approval_ref,
            approval_type,
            "manifest_sha256",
            manifest_sha256,
        )
        remote_hash = self._remote_manifest_sha256(target, job_dir)
        if remote_hash != manifest_sha256:
            raise GatewayError("remote job manifest changed after staging")

        manifest_result = self._remote_shell(
            target,
            f"set -eu; cat -- {shlex.quote(job_dir + '/AICC_JOB.json')}",
            "remote manifest read",
        )
        try:
            manifest = json.loads(manifest_result.stdout)
        except json.JSONDecodeError as exc:
            raise GatewayError("remote job manifest is not valid JSON") from exc
        submit_script = _safe_relative(manifest.get("submit_script"), "manifest submit_script")
        if manifest.get("job_id") != safe_job_id or manifest.get("scheduler") != target.scheduler:
            raise GatewayError("remote job manifest does not match the requested job")
        checksums_sha256 = manifest.get("checksums_sha256")
        if not isinstance(checksums_sha256, str) or not SHA256.fullmatch(checksums_sha256):
            raise GatewayError("remote job manifest has no valid SHA256SUMS identity")
        sums_result = self._remote_shell(
            target,
            f"set -eu; sha256sum -- {shlex.quote(job_dir + '/SHA256SUMS')}",
            "remote checksum-list hash",
        )
        actual_sums_hash = sums_result.stdout.strip().split(maxsplit=1)[0] if sums_result.stdout.strip() else ""
        if actual_sums_hash != checksums_sha256:
            raise GatewayError("remote SHA256SUMS changed after staging")

        if target.scheduler == "slurm":
            submit_command = (
                f"cd {shlex.quote(job_dir)} && sha256sum -c -- SHA256SUMS >/dev/null "
                "&& mkdir -- .aicc-submit-started "
                "&& sha256sum -c -- SHA256SUMS >/dev/null "
                f"&& raw_job_id=$(sbatch --parsable {shlex.quote(submit_script)}) "
                "&& printf '%s\\n' \"$raw_job_id\" > .aicc-submit-started/scheduler-job-id "
                "&& printf '%s\\n' \"$raw_job_id\""
            )
        elif target.scheduler == "pbs":
            submit_command = (
                f"cd {shlex.quote(job_dir)} && sha256sum -c -- SHA256SUMS >/dev/null "
                "&& mkdir -- .aicc-submit-started "
                "&& sha256sum -c -- SHA256SUMS >/dev/null "
                f"&& raw_job_id=$(qsub {shlex.quote(submit_script)}) "
                "&& printf '%s\\n' \"$raw_job_id\" > .aicc-submit-started/scheduler-job-id "
                "&& printf '%s\\n' \"$raw_job_id\""
            )
        else:
            submit_command = (
                f"cd {shlex.quote(job_dir)} && sha256sum -c -- SHA256SUMS >/dev/null "
                "&& mkdir -- .aicc-submit-started "
                "&& sha256sum -c -- SHA256SUMS >/dev/null "
                f"&& raw_job_id=$(bsub < {shlex.quote(submit_script)}) "
                "&& scheduler_job_id=$(printf '%s\\n' \"$raw_job_id\" | "
                "sed -n 's/.*Job <\\([0-9][0-9]*\\)>.*/\\1/p') "
                "&& test -n \"$scheduler_job_id\" "
                "&& printf '%s\\n' \"$scheduler_job_id\" > .aicc-submit-started/scheduler-job-id "
                "&& printf '%s\\n' \"$raw_job_id\""
            )
        result = self._remote_shell(target, f"set -eu; {submit_command}", "scheduler submission")
        raw_job_id = result.stdout.strip().splitlines()[-1].strip() if result.stdout.strip() else ""
        if target.scheduler == "slurm":
            scheduler_job_id = raw_job_id.split(";", 1)[0]
        elif target.scheduler == "lsf":
            match = re.search(r"Job <([0-9]+)>", raw_job_id)
            scheduler_job_id = match.group(1) if match else ""
        else:
            scheduler_job_id = raw_job_id
        if not SAFE_ID.fullmatch(scheduler_job_id):
            raise GatewayError(f"scheduler returned an invalid job id: {raw_job_id!r}")
        self._audit(
            "job_submitted",
            target=target.name,
            job_id=safe_job_id,
            scheduler=target.scheduler,
            scheduler_job_id=scheduler_job_id,
            manifest_sha256=manifest_sha256,
            **approval,
        )
        return {
            "target": target.name,
            "job_id": safe_job_id,
            "scheduler": target.scheduler,
            "scheduler_job_id": scheduler_job_id,
            "manifest_sha256": manifest_sha256,
            **approval,
            "note": "scheduler acceptance is not scientific validation",
        }

    def get_status(self, target_name: Any, scheduler_job_id: Any) -> dict[str, Any]:
        target = self._target(target_name)
        job = _safe_id(scheduler_job_id, "scheduler_job_id")
        if target.scheduler == "slurm":
            script = (
                f"sacct -n -P -j {shlex.quote(job)} "
                "--format=JobIDRaw,State,ExitCode,Elapsed,Start,End"
            )
        elif target.scheduler == "pbs":
            script = f"qstat -f {shlex.quote(job)}"
        else:
            script = (
                f"bjobs -a -l {shlex.quote(job)} 2>&1 "
                f"|| bhist -l {shlex.quote(job)} 2>&1"
            )
        result = self._remote_shell(target, script, "scheduler status")
        raw_status = result.stdout.strip()
        scheduler_state, terminal = _normalize_scheduler_state(target.scheduler, raw_status)
        self._audit("job_status_read", target=target.name, scheduler_job_id=job)
        return {
            "target": target.name,
            "scheduler": target.scheduler,
            "scheduler_job_id": job,
            "scheduler_state": scheduler_state,
            "terminal": terminal,
            "raw_status": raw_status,
            "note": "terminal scheduler state must still be followed by the engine parser",
        }

    def list_job_files(self, target_name: Any, job_id: Any) -> dict[str, Any]:
        target = self._target(target_name)
        safe_job_id, job_dir = self._job_dir(target, job_id)
        script = (
            f"set -eu; cd {shlex.quote(job_dir)}; "
            "find . -maxdepth 2 -type f -printf '%P\\t%s\\n' | sort"
        )
        result = self._remote_shell(target, script, "job file listing")
        return {"target": target.name, "job_id": safe_job_id, "files": result.stdout.strip()}

    def _assert_remote_regular_file(
        self, target: Target, job_dir: str, relative: str
    ) -> None:
        # POSIX `test` has no portable `--` terminator. Prefix the already-
        # validated relative path with `./` so a dash-leading filename cannot
        # be interpreted as an operand, while retaining compatibility with
        # older /bin/sh implementations used on HPC login nodes.
        candidate = shlex.quote(f"./{relative}")
        script = (
            f"set -eu; cd {shlex.quote(job_dir)}; root=$(pwd -P); candidate={candidate}; "
            "test -f \"$candidate\"; test ! -L \"$candidate\"; "
            "resolved=$(realpath -e -- \"$candidate\"); "
            "case \"$resolved\" in \"$root\"/*) ;; *) exit 65 ;; esac"
        )
        self._remote_shell(target, script, "remote artifact boundary check")

    def stat_artifact(self, target_name: Any, job_id: Any, path: Any) -> dict[str, Any]:
        target = self._target(target_name)
        safe_job_id, job_dir = self._job_dir(target, job_id)
        relative = _safe_relative(path, "path")
        self._assert_remote_regular_file(target, job_dir, relative)
        remote_path = f"{job_dir}/{relative}"
        script = (
            f"set -eu; sha256sum -- {shlex.quote(remote_path)}; "
            f"stat -c '%s' -- {shlex.quote(remote_path)}"
        )
        result = self._remote_shell(target, script, "artifact stat")
        lines = result.stdout.splitlines()
        digest = lines[0].split(maxsplit=1)[0] if lines else ""
        if len(lines) < 2 or not SHA256.fullmatch(digest) or not lines[1].strip().isdigit():
            raise GatewayError("artifact stat response is invalid")
        return {
            "target": target.name,
            "job_id": safe_job_id,
            "path": relative,
            "size_bytes": int(lines[1].strip()),
            "sha256": digest,
        }

    def read_log(
        self, target_name: Any, job_id: Any, path: Any, max_bytes: Any | None = None
    ) -> dict[str, Any]:
        target = self._target(target_name)
        safe_job_id, job_dir = self._job_dir(target, job_id)
        relative = _safe_relative(path, "path")
        self._assert_remote_regular_file(target, job_dir, relative)
        limit = target.max_text_bytes if max_bytes is None else _integer(
            max_bytes, "max_bytes", 1, target.max_text_bytes
        )
        remote_path = f"{job_dir}/{relative}"
        result = self._remote_shell(
            target,
            f"set -eu; tail -c {limit} -- {shlex.quote(remote_path)}",
            "log read",
        )
        return {
            "target": target.name,
            "job_id": safe_job_id,
            "path": relative,
            "max_bytes": limit,
            "content": result.stdout,
        }

    def fetch_artifact(
        self,
        target_name: Any,
        job_id: Any,
        path: Any,
        destination_dir: Any,
        expected_sha256: Any,
    ) -> dict[str, Any]:
        target = self._target(target_name)
        safe_job_id, job_dir = self._job_dir(target, job_id)
        relative = _safe_relative(path, "path")
        self._assert_remote_regular_file(target, job_dir, relative)
        if not isinstance(destination_dir, str):
            raise GatewayError("destination_dir must be a local directory path")
        destination_root = _inside(
            Path(destination_dir), target.allowed_download_roots, "destination_dir"
        )
        if not isinstance(expected_sha256, str) or not SHA256.fullmatch(expected_sha256):
            raise GatewayError("expected_sha256 must be a lowercase SHA-256 digest")
        destination_root.mkdir(parents=True, exist_ok=True)
        final_path = destination_root / PurePosixPath(relative).name
        if final_path.exists():
            raise GatewayError("destination already exists; overwrite is not allowed")
        partial = destination_root / f".{final_path.name}.partial-{uuid.uuid4().hex[:10]}"
        remote_spec = f"{target.ssh_alias}:{job_dir}/{relative}"
        try:
            self._run(
                self._scp_base(target) + [remote_spec, str(partial)],
                target.command_timeout_seconds,
                "artifact download",
            )
            actual = _sha256_file(partial)
            if actual != expected_sha256:
                raise GatewayError("downloaded artifact hash does not match expected_sha256")
            os.replace(partial, final_path)
        finally:
            if partial.exists():
                partial.unlink()
        self._audit(
            "artifact_fetched",
            target=target.name,
            job_id=safe_job_id,
            remote_path=relative,
            local_path=str(final_path),
            sha256=expected_sha256,
        )
        return {
            "target": target.name,
            "job_id": safe_job_id,
            "path": relative,
            "local_path": str(final_path),
            "sha256": expected_sha256,
        }

    def cancel_job(
        self,
        target_name: Any,
        scheduler_job_id: Any,
        research_dir: Any,
        task_id: Any,
        approval_ref: Any,
        approval_type: Any,
        reason: Any,
    ) -> dict[str, Any]:
        target = self._target(target_name)
        if not target.cancel_enabled:
            raise GatewayError("cancellation is disabled for this target by local policy")
        job = _safe_id(scheduler_job_id, "scheduler_job_id")
        if approval_type != "remote_job_cancellation":
            raise GatewayError(
                "approval_type must be remote_job_cancellation for job cancellation"
            )
        approval = self._verify_user_approval(
            target,
            research_dir,
            task_id,
            approval_ref,
            approval_type,
            "scheduler_job_id",
            job,
        )
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 500:
            raise GatewayError("reason must be a non-empty string of at most 500 characters")
        command = {
            "slurm": "scancel",
            "pbs": "qdel",
            "lsf": "bkill",
        }[target.scheduler]
        self._remote_shell(target, f"{command} {shlex.quote(job)}", "scheduler cancellation")
        self._audit(
            "job_cancelled",
            target=target.name,
            scheduler_job_id=job,
            **approval,
            reason=reason.strip(),
        )
        return {
            "target": target.name,
            "scheduler_job_id": job,
            "cancelled": True,
            **approval,
        }
