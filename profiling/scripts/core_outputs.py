#!/usr/bin/env python3
"""Extract or exactly compare Contur core statistical outputs."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path


FIELDS = [
    "model_name",
    "model_version",
    "run_point",
    "yoda_files",
    "map_name",
    "stat_type",
    "combined_exclusion",
]


def parse_args() -> argparse.Namespace:
    """Parse the extract or compare subcommand and its file paths."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract = subparsers.add_parser("extract")
    extract.add_argument("database", type=Path)
    extract.add_argument("output", type=Path)
    extract.add_argument("--run-point", action="append", default=[])

    compare = subparsers.add_parser("compare")
    compare.add_argument("baseline", type=Path)
    compare.add_argument("modified", type=Path)
    return parser.parse_args()


def extract_rows(database: Path, selected_run_points: list[str]) -> list[dict[str, str]]:
    """Extract ordered core statistical-output rows from one Contur result database."""
    query = """
        SELECT model.name,
               model.version,
               model_point.run_point,
               model_point.yoda_files,
               map.name,
               run.stat_type,
               run.combined_exclusion
          FROM run
          JOIN model_point ON model_point.id = run.model_point_id
          LEFT JOIN model ON model.id = model_point.model_id
          LEFT JOIN map ON map.id = run.map_id
         WHERE run.stat_type IN ('SMBG', 'EXP', 'HLEXP')
         ORDER BY model.name,
                  model.version,
                  model_point.run_point,
                  model_point.yoda_files,
                  map.name,
                  run.stat_type
    """
    with sqlite3.connect(database) as connection:
        raw_rows = connection.execute(query).fetchall()

    selected = set(selected_run_points)
    rows = []
    for raw in raw_rows:
        if selected and str(raw[2]) not in selected:
            continue
        values = ["" if value is None else str(value) for value in raw[:-1]]
        values.append(format(float(raw[-1]), ".17g"))
        rows.append(dict(zip(FIELDS, values)))
    return rows


def write_rows(output: Path, rows: list[dict[str, str]]) -> None:
    """Write extracted rows with the stable field order used for comparison."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read a core-output CSV and reject an unexpected schema."""
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != FIELDS:
            raise ValueError(f"Unexpected columns in {path}: {reader.fieldnames}")
        return list(reader)


def compare_rows(baseline: Path, modified: Path) -> int:
    """Compare two ordered extracts exactly and report the first difference."""
    left = read_rows(baseline)
    right = read_rows(modified)
    if left == right:
        print(f"MATCH: {len(left)} ordered core-output rows are identical")
        return 0

    print("MISMATCH: extracted core outputs differ")
    print(f"baseline rows: {len(left)}")
    print(f"modified rows: {len(right)}")
    for index, (left_row, right_row) in enumerate(zip(left, right), start=1):
        if left_row != right_row:
            print(f"first differing row: {index}")
            print(f"baseline: {left_row}")
            print(f"modified: {right_row}")
            break
    return 1


def main() -> int:
    """Run the requested extraction or exact-comparison operation."""
    args = parse_args()
    if args.command == "extract":
        rows = extract_rows(args.database, args.run_point)
        if not rows:
            print(f"ERROR: no SMBG, EXP or HLEXP rows found in {args.database}")
            return 1
        write_rows(args.output, rows)
        print(f"WROTE: {len(rows)} rows to {args.output}")
        return 0
    return compare_rows(args.baseline, args.modified)


if __name__ == "__main__":
    raise SystemExit(main())
