"""Smoke tests for the retained dissertation evidence and analysis scripts."""

from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "profiling/results/observable_isolated_20260803T004228+0100"


class EvidenceSmokeTest(unittest.TestCase):
    def test_retained_profile_can_be_summarised(self) -> None:
        profile = RESULT / "profiles/baseline/profile.prof"
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "profiling/scripts/profile_summary.py"),
                    str(profile),
                    "--output-dir",
                    str(output_dir),
                ],
                check=True,
            )
            with (output_dir / "profile_summary.tsv").open(
                encoding="utf-8", newline=""
            ) as stream:
                rows = list(csv.DictReader(stream, delimiter="\t"))

        expected = next(
            row
            for row in rows
            if row["function"] == "__getExpected" and row["line"] == "172"
        )
        self.assertEqual(expected["profile_total_calls"], "1156920804")
        self.assertAlmostEqual(float(expected["cumulative_s"]), 300.498194079, places=6)

    def test_retained_core_outputs_match(self) -> None:
        baseline = RESULT / "runs/unprofiled_1_baseline/core_outputs.csv"
        modified = RESULT / "runs/unprofiled_1_modified/core_outputs.csv"
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "profiling/scripts/core_outputs.py"),
                "compare",
                str(baseline),
                str(modified),
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        )
        self.assertIn("MATCH: 300 ordered core-output rows are identical", completed.stdout)


if __name__ == "__main__":
    unittest.main()
