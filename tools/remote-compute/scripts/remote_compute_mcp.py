#!/usr/bin/env python3
"""Stdio MCP facade for the AICC agentless remote-compute gateway."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

from remote_compute_core import GatewayConfig, GatewayError, RemoteComputeGateway


SERVER_INFO = {"name": "aicc-remote-compute", "version": "0.1.0"}
LEGACY_PROTOCOL = "2025-06-18"
MODERN_PROTOCOL = "2026-07-28"
MAX_LINE_BYTES = 4 * 1024 * 1024


def object_schema(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
        "additionalProperties": False,
    }


TOOLS: list[dict[str, Any]] = [
    {
        "name": "compute_list_targets",
        "description": "List policy-defined compute target aliases without exposing credentials or remote roots.",
        "inputSchema": object_schema({}),
    },
    {
        "name": "compute_probe_target",
        "description": "Probe one approved SSH target and report its OS, root availability, and scheduler command.",
        "inputSchema": object_schema({"target": {"type": "string"}}, ["target"]),
    },
    {
        "name": "compute_read_cluster_guide",
        "description": "Read the approved target's ~/.cluster-agents.md with size and SHA-256 provenance.",
        "inputSchema": object_schema({"target": {"type": "string"}}, ["target"]),
    },
    {
        "name": "compute_stage_job",
        "description": "Upload a bounded local job bundle into a new immutable remote job directory and verify hashes.",
        "inputSchema": object_schema(
            {
                "target": {"type": "string"},
                "job_id": {"type": "string"},
                "input_dir": {"type": "string"},
                "submit_script": {"type": "string"},
            },
            ["target", "job_id", "input_dir", "submit_script"],
        ),
    },
    {
        "name": "compute_submit_job",
        "description": "Submit an unchanged staged job after AICC gates and an exact expensive_hpc_submission user approval bound to its manifest; returns the scheduler job ID.",
        "inputSchema": object_schema(
            {
                "target": {"type": "string"},
                "job_id": {"type": "string"},
                "manifest_sha256": {"type": "string"},
                "research_dir": {"type": "string"},
                "task_id": {"type": "string"},
                "approval_ref": {"type": "string"},
                "approval_type": {"type": "string"},
            },
            [
                "target",
                "job_id",
                "manifest_sha256",
                "research_dir",
                "task_id",
                "approval_ref",
                "approval_type",
            ],
        ),
    },
    {
        "name": "compute_get_status",
        "description": "Read authoritative Slurm/PBS status for a scheduler job; this does not claim scientific convergence.",
        "inputSchema": object_schema(
            {"target": {"type": "string"}, "scheduler_job_id": {"type": "string"}},
            ["target", "scheduler_job_id"],
        ),
    },
    {
        "name": "compute_list_job_files",
        "description": "List regular files up to two levels below an approved remote job directory.",
        "inputSchema": object_schema(
            {"target": {"type": "string"}, "job_id": {"type": "string"}},
            ["target", "job_id"],
        ),
    },
    {
        "name": "compute_stat_artifact",
        "description": "Return the size and SHA-256 of one portable relative path inside a remote job directory.",
        "inputSchema": object_schema(
            {
                "target": {"type": "string"},
                "job_id": {"type": "string"},
                "path": {"type": "string"},
            },
            ["target", "job_id", "path"],
        ),
    },
    {
        "name": "compute_read_log",
        "description": "Read a bounded tail of one text log inside a remote job directory.",
        "inputSchema": object_schema(
            {
                "target": {"type": "string"},
                "job_id": {"type": "string"},
                "path": {"type": "string"},
                "max_bytes": {"type": "integer", "minimum": 1},
            },
            ["target", "job_id", "path"],
        ),
    },
    {
        "name": "compute_fetch_artifact",
        "description": "Download one remote job artifact atomically into an allowed local root and verify its expected SHA-256.",
        "inputSchema": object_schema(
            {
                "target": {"type": "string"},
                "job_id": {"type": "string"},
                "path": {"type": "string"},
                "destination_dir": {"type": "string"},
                "expected_sha256": {"type": "string"},
            },
            ["target", "job_id", "path", "destination_dir", "expected_sha256"],
        ),
    },
    {
        "name": "compute_cancel_job",
        "description": "Cancel a Slurm/PBS job only when local policy enables it and an exact remote_job_cancellation user approval is bound to that scheduler job ID.",
        "inputSchema": object_schema(
            {
                "target": {"type": "string"},
                "scheduler_job_id": {"type": "string"},
                "research_dir": {"type": "string"},
                "task_id": {"type": "string"},
                "approval_ref": {"type": "string"},
                "approval_type": {"type": "string"},
                "reason": {"type": "string"},
            },
            [
                "target",
                "scheduler_job_id",
                "research_dir",
                "task_id",
                "approval_ref",
                "approval_type",
                "reason",
            ],
        ),
    },
]


def tool_result(value: dict[str, Any], is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False, indent=2)}],
        "structuredContent": value,
        **({"isError": True} if is_error else {}),
    }


def dispatch(gateway: RemoteComputeGateway, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    calls: dict[str, Callable[[], dict[str, Any]]] = {
        "compute_list_targets": gateway.list_targets,
        "compute_probe_target": lambda: gateway.probe_target(arguments.get("target")),
        "compute_read_cluster_guide": lambda: gateway.read_cluster_guide(arguments.get("target")),
        "compute_stage_job": lambda: gateway.stage_job(
            arguments.get("target"),
            arguments.get("job_id"),
            arguments.get("input_dir"),
            arguments.get("submit_script"),
        ),
        "compute_submit_job": lambda: gateway.submit_job(
            arguments.get("target"),
            arguments.get("job_id"),
            arguments.get("manifest_sha256"),
            arguments.get("research_dir"),
            arguments.get("task_id"),
            arguments.get("approval_ref"),
            arguments.get("approval_type"),
        ),
        "compute_get_status": lambda: gateway.get_status(
            arguments.get("target"), arguments.get("scheduler_job_id")
        ),
        "compute_list_job_files": lambda: gateway.list_job_files(
            arguments.get("target"), arguments.get("job_id")
        ),
        "compute_stat_artifact": lambda: gateway.stat_artifact(
            arguments.get("target"), arguments.get("job_id"), arguments.get("path")
        ),
        "compute_read_log": lambda: gateway.read_log(
            arguments.get("target"),
            arguments.get("job_id"),
            arguments.get("path"),
            arguments.get("max_bytes"),
        ),
        "compute_fetch_artifact": lambda: gateway.fetch_artifact(
            arguments.get("target"),
            arguments.get("job_id"),
            arguments.get("path"),
            arguments.get("destination_dir"),
            arguments.get("expected_sha256"),
        ),
        "compute_cancel_job": lambda: gateway.cancel_job(
            arguments.get("target"),
            arguments.get("scheduler_job_id"),
            arguments.get("research_dir"),
            arguments.get("task_id"),
            arguments.get("approval_ref"),
            arguments.get("approval_type"),
            arguments.get("reason"),
        ),
    }
    call = calls.get(name)
    if call is None:
        raise KeyError(name)
    return call()


def modern_request(request: dict[str, Any]) -> bool:
    params = request.get("params")
    if not isinstance(params, dict):
        return False
    meta = params.get("_meta")
    return isinstance(meta, dict) and meta.get("io.modelcontextprotocol/protocolVersion") == MODERN_PROTOCOL


def modern_result(result: Any) -> Any:
    if not isinstance(result, dict):
        return result
    value = dict(result)
    value.setdefault("resultType", "complete")
    meta = dict(value.get("_meta") or {})
    meta.setdefault("io.modelcontextprotocol/serverInfo", SERVER_INFO)
    value["_meta"] = meta
    return value


def response(
    request_id: Any,
    *,
    result: Any = None,
    error: dict[str, Any] | None = None,
    modern: bool = False,
) -> None:
    payload: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id}
    if error is None:
        payload["result"] = modern_result(result) if modern else result
    else:
        payload["error"] = error
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def serve(gateway: RemoteComputeGateway) -> int:
    for raw_line in sys.stdin.buffer:
        if len(raw_line) > MAX_LINE_BYTES:
            print("discarded oversized MCP input line", file=sys.stderr)
            continue
        try:
            request = json.loads(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            print("discarded invalid MCP JSON", file=sys.stderr)
            continue
        if not isinstance(request, dict):
            continue
        method = request.get("method")
        request_id = request.get("id")
        if request_id is None:
            continue
        try:
            is_modern = modern_request(request) or method == "server/discover"
            if method == "server/discover":
                response(
                    request_id,
                    modern=True,
                    result={
                        "supportedVersions": [MODERN_PROTOCOL],
                        "capabilities": {"tools": {}},
                        "instructions": (
                            "Use only configured aliases. Stage immutable bundles before submission; "
                            "submission and cancellation require local policy plus recorded approval."
                        ),
                    },
                )
            elif method == "initialize":
                requested = (request.get("params") or {}).get("protocolVersion")
                protocol = requested if isinstance(requested, str) and requested.startswith("2025-") else LEGACY_PROTOCOL
                response(
                    request_id,
                    result={
                        "protocolVersion": protocol,
                        "capabilities": {"tools": {"listChanged": False}},
                        "serverInfo": SERVER_INFO,
                    },
                )
            elif method == "ping":
                response(request_id, result={}, modern=is_modern)
            elif method == "tools/list":
                result = {"tools": TOOLS}
                if is_modern:
                    result.update({"ttlMs": 60000, "cacheScope": "private"})
                response(request_id, result=result, modern=is_modern)
            elif method == "tools/call":
                params = request.get("params") or {}
                name = params.get("name")
                arguments = params.get("arguments") or {}
                if not isinstance(name, str) or not isinstance(arguments, dict):
                    response(
                        request_id,
                        error={"code": -32602, "message": "invalid tools/call parameters"},
                    )
                    continue
                try:
                    value = dispatch(gateway, name, arguments)
                    response(request_id, result=tool_result(value), modern=is_modern)
                except GatewayError as exc:
                    response(
                        request_id,
                        result=tool_result({"error": str(exc)}, is_error=True),
                        modern=is_modern,
                    )
                except KeyError:
                    response(request_id, error={"code": -32601, "message": f"unknown tool: {name}"})
            else:
                response(request_id, error={"code": -32601, "message": f"method not found: {method}"})
        except Exception as exc:  # keep protocol stdout clean; details stay local
            print(f"internal gateway error: {type(exc).__name__}: {exc}", file=sys.stderr)
            response(request_id, error={"code": -32603, "message": "internal gateway error"})
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default=os.environ.get("AICC_REMOTE_COMPUTE_CONFIG"),
        help="Absolute private JSON config path (or AICC_REMOTE_COMPUTE_CONFIG).",
    )
    parser.add_argument("--check-config", action="store_true")
    args = parser.parse_args()
    if not args.config:
        parser.error("--config or AICC_REMOTE_COMPUTE_CONFIG is required")
    try:
        config = GatewayConfig.load(Path(args.config))
    except GatewayError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2
    if args.check_config:
        print(json.dumps(RemoteComputeGateway(config).list_targets(), indent=2))
        return 0
    return serve(RemoteComputeGateway(config))


if __name__ == "__main__":
    raise SystemExit(main())
