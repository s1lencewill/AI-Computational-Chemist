#!/usr/bin/env python3
"""Offline tests for the agentless remote-compute gateway."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from remote_compute_core import (
    CommandResult,
    GatewayConfig,
    GatewayError,
    RemoteComputeGateway,
    _normalize_scheduler_state,
)


PAYLOAD = b"validated artifact\n"


class FakeRunner:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.manifest_sha256 = "0" * 64
        self.manifest = {
            "schema_version": 1,
            "job_id": "job-001",
            "target": "test-slurm",
            "scheduler": "slurm",
            "submit_script": "submit.sh",
            "checksums_sha256": "1" * 64,
            "files": [],
        }

    def run(self, argv: list[str], timeout_seconds: int) -> CommandResult:
        del timeout_seconds
        self.calls.append(list(argv))
        if argv[0] == "scp-fake" and not argv[-1].endswith("/"):
            Path(argv[-1]).write_bytes(PAYLOAD)
            return CommandResult(0)
        command = argv[-1] if argv and argv[0] == "ssh-fake" else ""
        if "sha256sum --" in command and "AICC_JOB.json" in command:
            return CommandResult(0, f"{self.manifest_sha256}  AICC_JOB.json\n")
        if "sha256sum --" in command and "SHA256SUMS" in command:
            return CommandResult(0, f"{self.manifest['checksums_sha256']}  SHA256SUMS\n")
        if "cat --" in command and "AICC_JOB.json" in command:
            return CommandResult(0, json.dumps(self.manifest))
        if "sbatch --parsable" in command:
            return CommandResult(0, "12345;cluster-a\n")
        if "bsub <" in command:
            return CommandResult(0, "Job <67890> is submitted to queue <normal>.\n")
        if "sacct -n -P" in command:
            return CommandResult(0, "12345|COMPLETED|0:0|00:01:02|start|end\n")
        if "bjobs -a -l" in command:
            return CommandResult(0, "Job <67890>, Status <DO\n NE>, Exit Code <0>\n")
        if "tail -c" in command:
            return CommandResult(0, "calculation log tail\n")
        if "stat -c" in command and "sha256sum" in command:
            return CommandResult(0, f"{hashlib.sha256(PAYLOAD).hexdigest()}  result.dat\n{len(PAYLOAD)}\n")
        if "$HOME/.cluster-agents.md" in command:
            content = "# test cluster\nScheduler: Slurm\n"
            digest = hashlib.sha256(content.encode()).hexdigest()
            return CommandResult(0, f"__AICC_META__ {len(content.encode())} {digest}\n{content}")
        if "hostname" in command:
            return CommandResult(0, "host=test\nkernel=Linux\nroot_exists=yes\nscheduler_command=sbatch\n")
        return CommandResult(0)


class GatewayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="aicc-gateway-test-")
        self.root = Path(self.temp.name)
        self.upload = self.root / "upload"
        self.download = self.root / "download"
        self.upload.mkdir()
        self.download.mkdir()
        self.project = self.upload / "project"
        decisions_dir = self.project / ".research"
        decisions_dir.mkdir(parents=True)
        decisions = [
            {
                "decision_id": "D-HPC-001",
                "task_id": "T004",
                "kind": "approval",
                "decision": "approved",
                "by": "user",
                "approval_type": "expensive_hpc_submission",
                "manifest_sha256": "0" * 64,
                "reason": "Approve the exact staged test bundle.",
                "created_at": "2026-09-07T00:00:00Z",
            },
            {
                "decision_id": "D-CANCEL-001",
                "task_id": "T004",
                "kind": "approval",
                "decision": "approved",
                "by": "user",
                "approval_type": "remote_job_cancellation",
                "scheduler_job_id": "12345",
                "reason": "Approve cancellation of the test job.",
                "created_at": "2026-09-07T00:01:00Z",
            },
        ]
        (decisions_dir / "decisions.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in decisions), encoding="utf-8"
        )
        self.config_path = self.root / "config.json"
        self.config_path.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "sshExecutable": "ssh-fake",
                    "scpExecutable": "scp-fake",
                    "auditLog": str(self.root / "audit.jsonl"),
                    "targets": {
                        "test-slurm": {
                            "sshAlias": "test-slurm",
                            "scheduler": "slurm",
                            "remoteRoot": "/scratch/test/aicc-jobs",
                            "allowedUploadRoots": [str(self.upload)],
                            "allowedDownloadRoots": [str(self.download)],
                            "allowedResearchRoots": [str(self.upload)],
                            "submitEnabled": True,
                            "cancelEnabled": True,
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        self.runner = FakeRunner()
        self.gateway = RemoteComputeGateway(GatewayConfig.load(self.config_path), self.runner)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_target_listing_redacts_connection_details(self) -> None:
        listed = self.gateway.list_targets()
        self.assertEqual(listed["targets"][0]["target"], "test-slurm")
        self.assertNotIn("ssh_alias", listed["targets"][0])
        self.assertNotIn("remote_root", listed["targets"][0])

    def test_lsf_scheduler_and_non_login_shell(self) -> None:
        raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        target = raw["targets"].pop("test-slurm")
        target.update(
            {
                "sshAlias": "test-lsf",
                "scheduler": "lsf",
                "loginShell": False,
            }
        )
        raw["targets"]["test-lsf"] = target
        self.config_path.write_text(json.dumps(raw), encoding="utf-8")

        runner = FakeRunner()
        runner.manifest.update(
            {
                "target": "test-lsf",
                "scheduler": "lsf",
                "submit_script": "submit.lsf",
            }
        )
        gateway = RemoteComputeGateway(GatewayConfig.load(self.config_path), runner)
        listed = gateway.list_targets()["targets"][0]
        self.assertEqual(listed["scheduler"], "lsf")
        self.assertFalse(listed["login_shell"])

        job = self.project / "lsf-job"
        job.mkdir()
        (job / "submit.lsf").write_text("#!/bin/bash\necho test\n", encoding="utf-8")
        (job / "input.in").write_text("input\n", encoding="utf-8")
        staged = gateway.stage_job("test-lsf", "job-001", str(job), "submit.lsf")
        runner.manifest_sha256 = staged["manifest_sha256"]
        decisions_path = self.project / ".research" / "decisions.jsonl"
        decisions = [json.loads(line) for line in decisions_path.read_text().splitlines()]
        decisions[0]["manifest_sha256"] = staged["manifest_sha256"]
        decisions_path.write_text(
            "".join(json.dumps(row) + "\n" for row in decisions), encoding="utf-8"
        )

        submitted = gateway.submit_job(
            "test-lsf",
            "job-001",
            staged["manifest_sha256"],
            str(self.project),
            "T004",
            "D-HPC-001",
            "expensive_hpc_submission",
        )
        self.assertEqual(submitted["scheduler_job_id"], "67890")
        lsf_status = gateway.get_status("test-lsf", "67890")
        self.assertEqual(lsf_status["scheduler_state"], "DONE")
        self.assertTrue(lsf_status["terminal"])
        self.assertTrue(any(call[-1].startswith("sh -c ") for call in runner.calls))
        self.assertTrue(any("bsub < submit.lsf" in call[-1] for call in runner.calls))
        self.assertTrue(any("bjobs -a -l 67890" in call[-1] for call in runner.calls))

        cancelled = gateway.cancel_job(
            "test-lsf",
            "12345",
            str(self.project),
            "T004",
            "D-CANCEL-001",
            "remote_job_cancellation",
            "operator request",
        )
        self.assertTrue(cancelled["cancelled"])
        self.assertTrue(any("bkill 12345" in call[-1] for call in runner.calls))

    def test_scheduler_state_normalization(self) -> None:
        self.assertEqual(
            _normalize_scheduler_state("slurm", "123|COMPLETED|0:0|00:01:00"),
            ("COMPLETED", True),
        )
        self.assertEqual(
            _normalize_scheduler_state("slurm", "123|RUNNING|0:0|00:00:03"),
            ("RUNNING", False),
        )
        self.assertEqual(
            _normalize_scheduler_state("pbs", "job_state = F\nExit_status = 0"),
            ("F", True),
        )
        self.assertEqual(
            _normalize_scheduler_state("lsf", "Job <1>, Status <DO\n NE>"),
            ("DONE", True),
        )
        self.assertEqual(_normalize_scheduler_state("lsf", "unrecognized"), ("UNKNOWN", False))

    def test_paths_and_ids_fail_closed(self) -> None:
        outside = self.root / "outside"
        outside.mkdir()
        with self.assertRaises(GatewayError):
            self.gateway.stage_job("test-slurm", "job-001", str(outside), "submit.sh")
        with self.assertRaises(GatewayError):
            self.gateway.read_log("test-slurm", "../escape", "run.log")
        with self.assertRaises(GatewayError):
            self.gateway.read_log("test-slurm", "job-001", "../run.log")

    def test_reserved_submission_marker_is_rejected(self) -> None:
        job = self.upload / "reserved"
        (job / ".aicc-submit-started").mkdir(parents=True)
        (job / "submit.sh").write_text("#!/bin/sh\n", encoding="utf-8")
        with self.assertRaisesRegex(GatewayError, "reserved gateway name"):
            self.gateway.stage_job("test-slurm", "job-reserved", str(job), "submit.sh")

    def test_stage_submit_status_and_log(self) -> None:
        job = self.project / "job"
        job.mkdir()
        (job / "submit.sh").write_text("#!/bin/bash\necho test\n", encoding="utf-8")
        (job / "input.in").write_text("input\n", encoding="utf-8")
        staged = self.gateway.stage_job("test-slurm", "job-001", str(job), "submit.sh")
        self.runner.manifest_sha256 = staged["manifest_sha256"]
        decisions_path = self.project / ".research" / "decisions.jsonl"
        decisions = [json.loads(line) for line in decisions_path.read_text().splitlines()]
        decisions[0]["manifest_sha256"] = staged["manifest_sha256"]
        decisions_path.write_text(
            "".join(json.dumps(row) + "\n" for row in decisions), encoding="utf-8"
        )
        submitted = self.gateway.submit_job(
            "test-slurm",
            "job-001",
            staged["manifest_sha256"],
            str(self.project),
            "T004",
            "D-HPC-001",
            "expensive_hpc_submission",
        )
        self.assertEqual(submitted["scheduler_job_id"], "12345")
        self.assertEqual(submitted["approval_ref"], "D-HPC-001")
        self.assertRegex(submitted["decisions_sha256"], r"^[a-f0-9]{64}$")
        self.assertTrue(
            any("mkdir -- .aicc-submit-started" in call[-1] for call in self.runner.calls)
        )
        status = self.gateway.get_status("test-slurm", "12345")
        self.assertIn("COMPLETED", status["raw_status"])
        log = self.gateway.read_log("test-slurm", "job-001", "slurm-12345.out", 4096)
        self.assertIn("calculation log", log["content"])

    def test_cluster_guide_has_provenance(self) -> None:
        guide = self.gateway.read_cluster_guide("test-slurm")
        self.assertEqual(guide["path"], "remote:~/.cluster-agents.md")
        self.assertRegex(guide["sha256"], r"^[a-f0-9]{64}$")
        self.assertIn("Scheduler", guide["content"])

    def test_artifact_download_is_hash_verified_and_non_overwriting(self) -> None:
        digest = hashlib.sha256(PAYLOAD).hexdigest()
        fetched = self.gateway.fetch_artifact(
            "test-slurm", "job-001", "results/result.dat", str(self.download), digest
        )
        path = Path(fetched["local_path"])
        self.assertEqual(path.read_bytes(), PAYLOAD)
        self.assertTrue(
            any(call[0] == "ssh-fake" and "realpath -e" in call[-1] for call in self.runner.calls)
        )
        boundary_calls = [
            call[-1]
            for call in self.runner.calls
            if call[0] == "ssh-fake" and "realpath -e" in call[-1]
        ]
        self.assertTrue(any("candidate=./results/result.dat" in call for call in boundary_calls))
        self.assertTrue(all("test -f --" not in call for call in boundary_calls))
        self.assertTrue(all("test ! -L --" not in call for call in boundary_calls))
        with self.assertRaises(GatewayError):
            self.gateway.fetch_artifact(
                "test-slurm", "job-001", "results/result.dat", str(self.download), digest
            )

    def test_submit_and_cancel_are_disabled_by_default(self) -> None:
        raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        raw["targets"]["test-slurm"]["submitEnabled"] = False
        raw["targets"]["test-slurm"]["cancelEnabled"] = False
        self.config_path.write_text(json.dumps(raw), encoding="utf-8")
        gateway = RemoteComputeGateway(GatewayConfig.load(self.config_path), self.runner)
        with self.assertRaisesRegex(GatewayError, "submission is disabled"):
            gateway.submit_job(
                "test-slurm",
                "job-001",
                "0" * 64,
                str(self.project),
                "T004",
                "D-HPC-001",
                "expensive_hpc_submission",
            )
        with self.assertRaisesRegex(GatewayError, "cancellation is disabled"):
            gateway.cancel_job(
                "test-slurm",
                "12345",
                str(self.project),
                "T004",
                "D-CANCEL-001",
                "remote_job_cancellation",
                "operator request",
            )

    def test_submit_rejects_invented_or_mismatched_approval(self) -> None:
        arguments = (
            "test-slurm",
            "job-001",
            "0" * 64,
            str(self.project),
            "T004",
        )
        with self.assertRaisesRegex(GatewayError, "exactly one decision"):
            self.gateway.submit_job(
                *arguments, "D-FAKE", "expensive_hpc_submission"
            )
        with self.assertRaisesRegex(GatewayError, "must be expensive_hpc_submission"):
            self.gateway.submit_job(
                *arguments, "D-HPC-001", "remote_job_cancellation"
            )
        with self.assertRaisesRegex(GatewayError, "not bound to.*manifest_sha256"):
            self.gateway.submit_job(
                "test-slurm",
                "job-001",
                "f" * 64,
                str(self.project),
                "T004",
                "D-HPC-001",
                "expensive_hpc_submission",
            )

    def test_submit_rejects_superseded_approval(self) -> None:
        decisions_path = self.project / ".research" / "decisions.jsonl"
        superseding = {
            "decision_id": "D-HPC-002",
            "task_id": "T004",
            "kind": "approval",
            "decision": "rejected",
            "by": "user",
            "approval_type": "expensive_hpc_submission",
            "manifest_sha256": "0" * 64,
            "supersedes": "D-HPC-001",
            "reason": "Withdraw the earlier approval.",
            "created_at": "2026-09-07T00:02:00Z",
        }
        with decisions_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(superseding) + "\n")
        with self.assertRaisesRegex(GatewayError, "was superseded"):
            self.gateway.submit_job(
                "test-slurm",
                "job-001",
                "0" * 64,
                str(self.project),
                "T004",
                "D-HPC-001",
                "expensive_hpc_submission",
            )

    def test_cancel_uses_recorded_user_approval(self) -> None:
        cancelled = self.gateway.cancel_job(
            "test-slurm",
            "12345",
            str(self.project),
            "T004",
            "D-CANCEL-001",
            "remote_job_cancellation",
            "operator request",
        )
        self.assertTrue(cancelled["cancelled"])
        self.assertEqual(cancelled["approval_ref"], "D-CANCEL-001")

    def test_missing_config_is_a_gateway_error(self) -> None:
        with self.assertRaisesRegex(GatewayError, "cannot read gateway config"):
            GatewayConfig.load(self.root / "missing.json")

    def test_stdio_mcp_initialize_and_tools_list(self) -> None:
        server = Path(__file__).with_name("remote_compute_mcp.py")
        messages = "\n".join(
            [
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {"protocolVersion": "2025-06-18", "capabilities": {}},
                    }
                ),
                json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
                json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "server/discover",
                        "params": {
                            "_meta": {
                                "io.modelcontextprotocol/protocolVersion": "2026-07-28",
                                "io.modelcontextprotocol/clientCapabilities": {},
                            }
                        },
                    }
                ),
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 4,
                        "method": "tools/list",
                        "params": {
                            "_meta": {
                                "io.modelcontextprotocol/protocolVersion": "2026-07-28"
                            }
                        },
                    }
                ),
                "",
            ]
        )
        result = subprocess.run(
            [sys.executable, str(server), "--config", str(self.config_path)],
            input=messages,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        responses = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(responses[0]["result"]["protocolVersion"], "2025-06-18")
        names = {tool["name"] for tool in responses[1]["result"]["tools"]}
        self.assertIn("compute_stage_job", names)
        self.assertIn("compute_submit_job", names)
        self.assertEqual(responses[2]["result"]["supportedVersions"], ["2026-07-28"])
        self.assertEqual(responses[2]["result"]["resultType"], "complete")
        self.assertIn("io.modelcontextprotocol/serverInfo", responses[2]["result"]["_meta"])
        self.assertEqual(responses[3]["result"]["cacheScope"], "private")


if __name__ == "__main__":
    unittest.main()
