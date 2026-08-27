#!/usr/bin/env python3
"""Count direct cross-package imports in a recorded Contur Git revision.

The counter uses Python's standard-library ``ast`` module.  Each imported target
package on an ``import`` or ``from ... import ...`` statement counts once.  The
walk includes imports at module scope, inside functions and inside
``TYPE_CHECKING`` blocks.  Imports within the same top-level Contur package and
imports of third-party modules are excluded.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import subprocess
import warnings
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


PACKAGE_ORDER = [
    "run",
    "plot",
    "scan",
    "oracle",
    "webpages",
    "factories",
    "data",
    "database",
    "util",
    "config",
]

LAYER = {
    "run": 0,
    "plot": 1,
    "scan": 1,
    "oracle": 1,
    "webpages": 1,
    "factories": 2,
    "data": 3,
    "database": 4,
    "util": 5,
    "config": 6,
}


@dataclass(frozen=True)
class ImportRecord:
    source_file: str
    line: int
    context: str
    source_module: str
    source_package: str
    target_module: str
    target_package: str
    violates_target: bool


def git(repo: Path, *args: str) -> str:
    """Run a read-only Git command in the selected repository and return stdout."""
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def module_from_path(path: str) -> str:
    """Convert a Python source path below src into its dotted module name."""
    relative = path.removeprefix("src/").removesuffix(".py")
    parts = relative.split("/")
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def source_package(module: str, packages: set[str]) -> str | None:
    """Return the top-level Contur package owning a source module, if recognised."""
    parts = module.split(".")
    if len(parts) >= 2 and parts[0] == "contur" and parts[1] in packages:
        return parts[1]
    return None


def current_package(module: str, source_file: str) -> list[str]:
    """Return the package components used to resolve a relative import."""
    parts = module.split(".")
    if not source_file.endswith("/__init__.py"):
        parts = parts[:-1]
    return parts


def resolve_from_module(module: str, source_file: str, node: ast.ImportFrom) -> str:
    """Resolve the module named by an absolute or relative from-import node."""
    if node.level == 0:
        return node.module or ""
    base = current_package(module, source_file)
    ascend = node.level - 1
    if ascend:
        base = base[:-ascend]
    if node.module:
        base.extend(node.module.split("."))
    return ".".join(base)


def target_package(target: str, packages: set[str]) -> str | None:
    """Return the recognised top-level package imported by a dotted target."""
    parts = target.split(".")
    if len(parts) >= 2 and parts[0] == "contur" and parts[1] in packages:
        return parts[1]
    return None


def violates_target(source: str, target: str) -> bool:
    """Check one package direction against the dissertation target contract."""
    if target == "database":
        return source != "data"
    return LAYER[target] <= LAYER[source]


class ImportVisitor(ast.NodeVisitor):
    """Collect cross-package imports and the source context in which they occur."""

    def __init__(
        self,
        source_file: str,
        module: str,
        packages: set[str],
    ) -> None:
        self.source_file = source_file
        self.module = module
        self.packages = packages
        self.source = source_package(module, packages)
        self.function_depth = 0
        self.type_checking_depth = 0
        self.records: list[ImportRecord] = []

    def context(self) -> str:
        """Describe whether the current import is at module, function or type-checking scope."""
        if self.type_checking_depth:
            return "TYPE_CHECKING"
        if self.function_depth:
            return "function"
        return "module"

    def add_targets(self, node: ast.AST, targets: set[str]) -> None:
        """Add one record per distinct imported top-level package on a statement."""
        if self.source is None:
            return
        seen_packages: set[str] = set()
        for target in sorted(targets):
            package = target_package(target, self.packages)
            if package is None or package == self.source or package in seen_packages:
                continue
            seen_packages.add(package)
            self.records.append(
                ImportRecord(
                    source_file=self.source_file,
                    line=node.lineno,
                    context=self.context(),
                    source_module=self.module,
                    source_package=self.source,
                    target_module=target,
                    target_package=package,
                    violates_target=violates_target(self.source, package),
                )
            )

    def visit_Import(self, node: ast.Import) -> None:
        self.add_targets(node, {alias.name for alias in node.names})

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        base = resolve_from_module(self.module, self.source_file, node)
        targets: set[str] = set()
        base_package = target_package(base, self.packages)
        if base_package is not None:
            targets.add(base)
        elif base == "contur":
            for alias in node.names:
                if alias.name != "*":
                    targets.add(f"contur.{alias.name}")
        self.add_targets(node, targets)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_depth += 1
        self.generic_visit(node)
        self.function_depth -= 1

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_If(self, node: ast.If) -> None:
        is_type_checking = (
            isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING"
        ) or (
            isinstance(node.test, ast.Attribute)
            and node.test.attr == "TYPE_CHECKING"
        )
        if is_type_checking:
            self.type_checking_depth += 1
        for child in node.body:
            self.visit(child)
        if is_type_checking:
            self.type_checking_depth -= 1
        for child in node.orelse:
            self.visit(child)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    """Write a deterministic CSV file with the requested columns."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    """Parse the repository revision and output-location arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def discover_source(repo: Path, revision: str) -> tuple[list[str], set[str]]:
    """List Python files and top-level packages in one recorded Git revision."""
    paths = [
        path
        for path in git(
            repo,
            "ls-tree",
            "-r",
            "--name-only",
            revision,
            "--",
            "src/contur",
        ).splitlines()
        if path.endswith(".py")
    ]
    packages = {
        path.split("/")[2]
        for path in paths
        if path.count("/") >= 3 and path.endswith("/__init__.py")
    }
    return paths, packages


def collect_imports(
    repo: Path, revision: str, paths: list[str], packages: set[str]
) -> tuple[list[ImportRecord], list[dict[str, str]], list[dict[str, str]]]:
    """Parse the selected files and return imports, syntax errors and syntax warnings."""
    records: list[ImportRecord] = []
    parse_errors: list[dict[str, str]] = []
    parse_warnings: list[dict[str, str]] = []
    for path in paths:
        source = git(repo, "show", f"{revision}:{path}")
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", SyntaxWarning)
                tree = ast.parse(source, filename=path)
            parse_warnings.extend(
                {"source_file": path, "warning": str(item.message)} for item in caught
            )
        except SyntaxError as error:
            parse_errors.append({"source_file": path, "error": str(error)})
            continue
        visitor = ImportVisitor(path, module_from_path(path), packages)
        visitor.visit(tree)
        records.extend(visitor.records)
    records.sort(
        key=lambda item: (
            item.source_package,
            item.target_package,
            item.source_file,
            item.line,
        )
    )
    return records, parse_errors, parse_warnings


def ordered_package_names(packages: set[str]) -> list[str]:
    """Return recognised packages in the stable order used by the output matrix."""
    ordered = [package for package in PACKAGE_ORDER if package in packages]
    ordered.extend(sorted(packages - set(ordered)))
    return ordered


def write_census(
    output_dir: Path,
    label: str,
    revision: str,
    paths: list[str],
    packages: set[str],
    records: list[ImportRecord],
    parse_errors: list[dict[str, str]],
    parse_warnings: list[dict[str, str]],
) -> dict[str, object]:
    """Write detailed, matrix, violation and JSON summary files for one census."""
    direction_counts = Counter(
        (record.source_package, record.target_package) for record in records
    )
    violation_counts = Counter(
        (record.source_package, record.target_package)
        for record in records
        if record.violates_target
    )
    contexts = Counter(record.context for record in records)
    ordered_packages = ordered_package_names(packages)
    output_dir.mkdir(parents=True, exist_ok=True)

    write_csv(
        output_dir / f"{label}-imports.csv",
        list(asdict(records[0]).keys()) if records else list(ImportRecord.__annotations__),
        [asdict(record) for record in records],
    )
    matrix_rows: list[dict[str, object]] = []
    for source in ordered_packages:
        row: dict[str, object] = {"source_package": source}
        for target in ordered_packages:
            row[target] = "" if source == target else direction_counts[(source, target)]
        row["outgoing_total"] = sum(
            direction_counts[(source, target)] for target in ordered_packages
        )
        matrix_rows.append(row)
    incoming_row: dict[str, object] = {"source_package": "incoming_total"}
    for target in ordered_packages:
        incoming_row[target] = sum(
            direction_counts[(source, target)] for source in ordered_packages
        )
    incoming_row["outgoing_total"] = len(records)
    matrix_rows.append(incoming_row)
    write_csv(
        output_dir / f"{label}-matrix.csv",
        ["source_package", *ordered_packages, "outgoing_total"],
        matrix_rows,
    )
    violation_rows = [
        {
            "source_package": source,
            "target_package": target,
            "direct_imports": count,
        }
        for (source, target), count in sorted(violation_counts.items())
    ]
    write_csv(
        output_dir / f"{label}-violations.csv",
        ["source_package", "target_package", "direct_imports"],
        violation_rows,
    )

    summary: dict[str, object] = {
        "label": label,
        "revision": revision,
        "counting_rules": {
            "unit": "one imported target package per AST import statement",
            "module_scope_imports": "included",
            "function_local_imports": "included",
            "TYPE_CHECKING_imports": "included",
            "same_package_imports": "excluded",
            "third_party_imports": "excluded",
        },
        "packages": ordered_packages,
        "python_files": len(paths),
        "parse_errors": parse_errors,
        "parse_warnings": parse_warnings,
        "cross_package_direct_imports": len(records),
        "contexts": dict(sorted(contexts.items())),
        "target_contract_violations": sum(violation_counts.values()),
        "violation_directions": len(violation_counts),
    }
    (output_dir / f"{label}-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    """Run a reproducible cross-package import census for one Git revision."""
    args = parse_args()

    repo = args.repo.resolve()
    revision = git(repo, "rev-parse", args.revision).strip()
    paths, packages = discover_source(repo, revision)
    records, parse_errors, parse_warnings = collect_imports(
        repo, revision, paths, packages
    )
    summary = write_census(
        args.output_dir,
        args.label,
        revision,
        paths,
        packages,
        records,
        parse_errors,
        parse_warnings,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
