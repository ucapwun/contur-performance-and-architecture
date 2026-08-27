#!/usr/bin/env python3
"""Summarise GNU time -v files from a profiling experiment directory."""

from __future__ import annotations

import argparse
import csv
import re
import statistics
from collections import defaultdict
from pathlib import Path


RUN_PATTERN = re.compile(r"^unprofiled_(\d+)_(.+)$")
ELAPSED_PATTERN = re.compile(
    r"^\s*Elapsed \(wall clock\) time.*?:\s*([0-9]+(?::[0-9]+){1,2}(?:\.[0-9]+)?)\s*$"
)


def elapsed_seconds(value: str) -> float:
    """Convert a GNU time elapsed value in MM:SS or HH:MM:SS form to seconds."""
    fields = value.split(":")
    if len(fields) == 2:
        minutes, seconds = fields
        return int(minutes) * 60 + float(seconds)
    if len(fields) == 3:
        hours, minutes, seconds = fields
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    raise ValueError(f"Unrecognised elapsed-time value: {value}")


def read_time(path: Path) -> dict[str, str]:
    """Read the elapsed time and available resource fields from one GNU time file."""
    values = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        elapsed_match = ELAPSED_PATTERN.match(line)
        if elapsed_match:
            values["elapsed_s"] = f"{elapsed_seconds(elapsed_match.group(1)):.6f}"
        elif "Maximum resident set size (kbytes):" in line:
            values["max_rss_kb"] = line.rsplit(":", 1)[1].strip()
        elif "User time (seconds):" in line:
            values["user_s"] = line.rsplit(":", 1)[1].strip()
        elif "System time (seconds):" in line:
            values["system_s"] = line.rsplit(":", 1)[1].strip()
    if "elapsed_s" not in values:
        raise ValueError(f"No elapsed wall-clock time found in {path}")
    return values


def main() -> int:
    """Summarise all retained unprofiled timings and optionally compare two cases."""
    parser = argparse.ArgumentParser()
    parser.add_argument("result_root", type=Path)
    parser.add_argument("--baseline-label")
    parser.add_argument("--modified-label")
    args = parser.parse_args()

    rows = []
    grouped = defaultdict(list)
    for time_file in sorted((args.result_root / "runs").glob("unprofiled_*/time.txt")):
        match = RUN_PATTERN.match(time_file.parent.name)
        if not match:
            continue
        repetition, label = match.groups()
        values = read_time(time_file)
        row = {
            "case": label,
            "repetition": repetition,
            "elapsed_s": values["elapsed_s"],
            "user_s": values.get("user_s", ""),
            "system_s": values.get("system_s", ""),
            "max_rss_kb": values.get("max_rss_kb", ""),
            "time_file": str(time_file.relative_to(args.result_root)),
        }
        rows.append(row)
        grouped[label].append(float(values["elapsed_s"]))

    with (args.result_root / "timings.tsv").open("w", encoding="utf-8", newline="") as stream:
        fields = [
            "case",
            "repetition",
            "elapsed_s",
            "user_s",
            "system_s",
            "max_rss_kb",
            "time_file",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    with (args.result_root / "timing_summary.tsv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(["case", "n", "mean_s", "sample_sd_s", "median_s", "min_s", "max_s"])
        for label in sorted(grouped):
            values = grouped[label]
            sample_sd = statistics.stdev(values) if len(values) > 1 else 0.0
            writer.writerow(
                [
                    label,
                    len(values),
                    f"{statistics.mean(values):.6f}",
                    f"{sample_sd:.6f}",
                    f"{statistics.median(values):.6f}",
                    f"{min(values):.6f}",
                    f"{max(values):.6f}",
                ]
            )
    if args.baseline_label or args.modified_label:
        if not (args.baseline_label and args.modified_label):
            raise ValueError("Both --baseline-label and --modified-label are required")
        baseline = grouped[args.baseline_label]
        modified = grouped[args.modified_label]
        if not baseline or not modified:
            raise ValueError("The requested comparison labels have no timings")
        baseline_mean = statistics.mean(baseline)
        modified_mean = statistics.mean(modified)
        with (args.result_root / "timing_comparison.tsv").open(
            "w", encoding="utf-8", newline=""
        ) as stream:
            writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
            writer.writerow(
                [
                    "baseline_case",
                    "modified_case",
                    "baseline_mean_s",
                    "modified_mean_s",
                    "modified_minus_baseline_s",
                    "time_reduction_percent",
                    "speedup_ratio",
                ]
            )
            writer.writerow(
                [
                    args.baseline_label,
                    args.modified_label,
                    f"{baseline_mean:.6f}",
                    f"{modified_mean:.6f}",
                    f"{modified_mean - baseline_mean:.6f}",
                    f"{100.0 * (baseline_mean - modified_mean) / baseline_mean:.6f}",
                    f"{baseline_mean / modified_mean:.6f}",
                ]
            )
    print(f"WROTE: {len(rows)} timings from {len(grouped)} case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
