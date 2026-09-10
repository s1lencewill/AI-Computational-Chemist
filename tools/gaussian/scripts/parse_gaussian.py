#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# ///
"""Validate and summarize a Gaussian log file.

Usage:
  uv run parse_gaussian.py JOB.log
  uv run parse_gaussian.py --json JOB.log

Exit codes: 0 clean, 1 finished with scientific issues, 2 incomplete/error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


HARTREE_EV = 27.211386
CRITERION_RE = re.compile(
    r"^\s*(Maximum Force|RMS\s+Force|Maximum Displacement|RMS\s+Displacement)"
    r"\s+[-+\d.DEe]+\s+[-+\d.DEe]+\s+(YES|NO)\s*$",
    re.M,
)


def parse_gaussian_text(text: str) -> dict[str, Any]:
    issues: list[str] = []
    normal = len(re.findall(r"Normal termination of Gaussian", text))
    error = re.search(r"Error termination via Lnk1e in (\S+?l(\d+)\.exe)", text)
    route_lines = re.findall(r"^ #.*", text, re.M)
    n_steps = max(1, len(route_lines))
    route = " ".join(route_lines[:6]).lower()
    is_opt = bool(re.search(r"\bopt\b", route))

    scf_matches = re.findall(r"SCF Done:\s+E\((\S+)\)\s*=\s*([-\d.]+)", text)
    final_scf = None
    if scf_matches:
        method, energy_text = scf_matches[-1]
        energy = float(energy_text)
        final_scf = {
            "method": method,
            "energy_hartree": energy,
            "energy_ev": energy * HARTREE_EV,
        }

    stationary = "Stationary point found" in text
    criteria: dict[str, str] = {}
    for label, verdict in CRITERION_RE.findall(text):
        criteria[" ".join(label.split()).lower().replace(" ", "_")] = verdict
    criteria_all_converged = None if len(criteria) < 4 else all(
        verdict == "YES" for verdict in criteria.values()
    )

    freq_lines = re.findall(r"Frequencies --\s+(.+)", text)
    frequencies = [float(value) for line in freq_lines for value in line.split()]
    n_imag = sum(1 for value in frequencies if value < 0)

    thermochemistry: dict[str, float] = {}
    for label, pattern in [
        ("electronic_plus_zpe", r"Sum of electronic and zero-point Energies=\s+([-\d.]+)"),
        ("enthalpy_298K", r"Sum of electronic and thermal Enthalpies=\s+([-\d.]+)"),
        ("gibbs_free_energy_298K", r"Sum of electronic and thermal Free Energies=\s+([-\d.]+)"),
    ]:
        match = re.search(pattern, text)
        if match:
            thermochemistry[label] = float(match.group(1))

    s2_matches = re.findall(r"S\*\*2 before annihilation\s+([\d.]+)", text)
    error_link = f"l{error.group(2)}" if error else None
    incomplete = normal == 0 or normal < n_steps

    if error_link:
        issues.append(f"error termination in {error_link} (see gaussian/references/errors.md)")
    if normal < n_steps:
        issues.append(
            f"incomplete Gaussian steps: {normal} normal termination(s) for {n_steps} route section(s)"
        )
    if is_opt and not stationary and not error_link:
        issues.append("optimization did not converge (no 'Stationary point found')")
    if criteria_all_converged is False:
        issues.append("one or more optimization convergence criteria are not YES")
    if n_imag > 1:
        issues.append(f"{n_imag} imaginary modes: not a stationary point of interest")

    exit_code = 2 if error_link or incomplete else (1 if issues else 0)
    return {
        "schema_version": 1,
        "status": "pass" if exit_code == 0 else ("issues" if exit_code == 1 else "error"),
        "exit_code": exit_code,
        "normal_terminations": normal,
        "route_sections_seen": n_steps,
        "error_link": error_link,
        "final_scf": final_scf,
        "optimization": {
            "requested": is_opt,
            "stationary_point_found": stationary,
            "criteria": criteria,
            "criteria_all_converged": criteria_all_converged,
        },
        "frequencies": {
            "count": len(frequencies),
            "values_cm-1": frequencies,
            "imaginary_count": n_imag,
            "lowest_cm-1": min(frequencies) if frequencies else None,
        },
        "thermochemistry_hartree": thermochemistry,
        "s2_before_annihilation": float(s2_matches[-1]) if s2_matches else None,
        "issues": issues,
    }


def print_text(result: dict[str, Any]) -> None:
    print(
        f"normal terminations: {result['normal_terminations']} "
        f"(route sections seen: {result['route_sections_seen']})"
    )
    final_scf = result["final_scf"]
    if final_scf:
        print(
            f"final SCF: E({final_scf['method']}) = {final_scf['energy_hartree']:.8f} Ha "
            f"= {final_scf['energy_ev']:.4f} eV"
        )
    optimization = result["optimization"]
    if optimization["requested"]:
        print(f"stationary point found: {optimization['stationary_point_found']}")
        if optimization["criteria_all_converged"] is not None:
            print(f"optimization criteria all converged: {optimization['criteria_all_converged']}")
    frequencies = result["frequencies"]
    if frequencies["count"]:
        print(
            f"frequencies: {frequencies['count']} modes, "
            f"{frequencies['imaginary_count']} imaginary "
            f"(lowest {frequencies['lowest_cm-1']:.1f} cm^-1)"
        )
        if frequencies["imaginary_count"] == 1:
            print("  -> 1 imaginary mode: valid only if this is an intended TS")
    labels = {
        "electronic_plus_zpe": "E+ZPE",
        "enthalpy_298K": "H(298)",
        "gibbs_free_energy_298K": "G(298)",
    }
    for key, value in result["thermochemistry_hartree"].items():
        print(f"{labels[key]}: {value:.6f} Ha")
    if result["s2_before_annihilation"] is not None:
        print(f"S**2 (last, before annihilation): {result['s2_before_annihilation']}")
    for issue in result["issues"]:
        print(f"ISSUE: {issue}")


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < (3, 8):
        raise SystemExit(
            "parse_gaussian.py targets modern Python (>=3.8); run via `uv run "
            "parse_gaussian.py` or load the cluster guide's Python (conda/uv/module)."
        )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, help="Gaussian .log/.out file")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable result")
    args = parser.parse_args(argv)
    try:
        text = args.log.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        print(f"cannot read Gaussian log: {exc}", file=sys.stderr)
        return 2
    result = parse_gaussian_text(text)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_text(result)
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
