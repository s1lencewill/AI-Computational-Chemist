#!/usr/bin/env python3
"""Offline tests for the Gaussian parser."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from parse_gaussian import main, parse_gaussian_text


CLEAN_LOG = """ #p B3LYP/6-31G(d) opt
 SCF Done:  E(RB3LYP) =  -76.40000000 A.U.
 Maximum Force            0.000010     0.000450     YES
 RMS     Force            0.000005     0.000300     YES
 Maximum Displacement     0.000020     0.001800     YES
 RMS     Displacement     0.000010     0.001200     YES
 Stationary point found.
 Normal termination of Gaussian 09
 #p geom=allcheck freq
 Frequencies --   1700.0 3700.0 3800.0
 Sum of electronic and zero-point Energies= -76.380000
 Sum of electronic and thermal Enthalpies= -76.376000
 Sum of electronic and thermal Free Energies= -76.397000
 Normal termination of Gaussian 09
"""


class GaussianParserTests(unittest.TestCase):
    def test_clean_opt_freq_result(self) -> None:
        result = parse_gaussian_text(CLEAN_LOG)
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["normal_terminations"], 2)
        self.assertTrue(result["optimization"]["criteria_all_converged"])
        self.assertEqual(result["frequencies"]["imaginary_count"], 0)

    def test_incomplete_multistep_log_is_error(self) -> None:
        result = parse_gaussian_text(CLEAN_LOG.rsplit("Normal termination", 1)[0])
        self.assertEqual(result["exit_code"], 2)
        self.assertTrue(any("incomplete Gaussian steps" in item for item in result["issues"]))

    def test_json_cli_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="aicc-gaussian-parser-") as temp_dir:
            path = Path(temp_dir) / "job.log"
            path.write_text(CLEAN_LOG, encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main(["--json", str(path)])
            self.assertEqual(exit_code, 0)
            self.assertEqual(json.loads(output.getvalue())["status"], "pass")


if __name__ == "__main__":
    unittest.main()
