#!/usr/bin/env python3
"""Create stable text and TSV summaries from one cProfile file."""

from __future__ import annotations

import argparse
import csv
import pstats
from pathlib import Path


TARGET_NAMES = {"__init__", "__getExpected", "add_signal_component"}


def parse_args() -> argparse.Namespace:
    """Parse the profile path and summary-output options."""
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=50)
    return parser.parse_args()


def write_sorted_stats(profile: Path, destination: Path, sort_key: str, limit: int) -> None:
    """Write a bounded pstats report sorted by one supported statistic."""
    with destination.open("w", encoding="utf-8") as stream:
        stats = pstats.Stats(str(profile), stream=stream)
        stats.strip_dirs().sort_stats(sort_key).print_stats(limit)


def main() -> int:
    """Create text summaries and a TSV row set for the selected profile."""
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    stats = pstats.Stats(str(args.profile))
    write_sorted_stats(
        args.profile, args.output_dir / "pstats_cumulative.txt", "cumulative", args.limit
    )
    write_sorted_stats(
        args.profile, args.output_dir / "pstats_internal.txt", "time", args.limit
    )

    rows = []
    for (filename, line, name), values in stats.stats.items():
        primitive_calls, total_calls, total_time, cumulative_time, _callers = values
        if "test_observable.py" in filename and name in TARGET_NAMES:
            rows.append(
                (
                    name,
                    filename,
                    line,
                    primitive_calls,
                    total_calls,
                    total_time,
                    cumulative_time,
                )
            )

    with (args.output_dir / "profile_summary.tsv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(
            [
                "profile",
                "profile_total_s",
                "profile_total_calls",
                "profile_primitive_calls",
                "function",
                "source_file",
                "line",
                "primitive_calls",
                "total_calls",
                "internal_s",
                "cumulative_s",
            ]
        )
        if not rows:
            writer.writerow(
                [
                    args.profile.name,
                    f"{stats.total_tt:.9f}",
                    stats.total_calls,
                    stats.prim_calls,
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            )
        for row in sorted(rows):
            writer.writerow(
                [
                    args.profile.name,
                    f"{stats.total_tt:.9f}",
                    stats.total_calls,
                    stats.prim_calls,
                    *row[:5],
                    f"{row[5]:.9f}",
                    f"{row[6]:.9f}",
                ]
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
