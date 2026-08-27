"""Smoke tests for the retained dissertation evidence and analysis scripts."""

from __future__ import annotations

import ast
import csv
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "profiling/results/observable_isolated_20260803T004228+0100"


def load_script(name: str, relative_path: str) -> ModuleType:
    """Load a repository script as a module for focused unit tests."""
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


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

    def test_core_output_difference_returns_failure(self) -> None:
        fields = [
            "model_name",
            "model_version",
            "run_point",
            "yoda_files",
            "map_name",
            "stat_type",
            "combined_exclusion",
        ]
        row = {
            "model_name": "example",
            "model_version": "1",
            "run_point": "0",
            "yoda_files": "input.yoda.gz",
            "map_name": "example.map",
            "stat_type": "SMBG",
            "combined_exclusion": "0.5",
        }
        with tempfile.TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline.csv"
            modified = Path(directory) / "modified.csv"
            for path, exclusion in ((baseline, "0.5"), (modified, "0.6")):
                with path.open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=fields)
                    writer.writeheader()
                    writer.writerow({**row, "combined_exclusion": exclusion})
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "profiling/scripts/core_outputs.py"),
                    "compare",
                    str(baseline),
                    str(modified),
                ],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
            )

        self.assertEqual(completed.returncode, 1)
        self.assertIn("MISMATCH: extracted core outputs differ", completed.stdout)

    def test_elapsed_time_boundaries(self) -> None:
        timings = load_script(
            "summarise_timings_test", "profiling/scripts/summarise_timings.py"
        )
        self.assertEqual(timings.elapsed_seconds("0:00.50"), 0.5)
        self.assertEqual(timings.elapsed_seconds("1:02:03.5"), 3723.5)
        with self.assertRaises(ValueError):
            timings.elapsed_seconds("12")

    def test_import_census_includes_non_module_scope_imports(self) -> None:
        census = load_script(
            "count_package_imports_test", "dependency-analysis/count_package_imports.py"
        )
        tree = ast.parse(
            """
from typing import TYPE_CHECKING
from contur.data import data_objects

def load():
    from contur.run import run_analysis

if TYPE_CHECKING:
    from contur.plot import plotting
"""
        )
        visitor = census.ImportVisitor(
            "src/contur/util/example.py",
            "contur.util.example",
            {"util", "data", "run", "plot"},
        )
        visitor.visit(tree)

        observed = {
            (record.target_package, record.context, record.violates_target)
            for record in visitor.records
        }
        self.assertEqual(
            observed,
            {
                ("data", "module", True),
                ("run", "function", True),
                ("plot", "TYPE_CHECKING", True),
            },
        )
        self.assertFalse(census.violates_target("data", "database"))
        self.assertTrue(census.violates_target("webpages", "database"))


if __name__ == "__main__":
    unittest.main()
