# Architecture baseline captured on 2026-08-04

This directory records a reproducible starting point for the architecture strand. It deliberately
separates two comparisons:

- T0 Pylint comparison: pre-refactoring revision
  cb0d0f1866caae0bbc3393a5c9c04504a01716cb.
- T1 ongoing-redesign baseline: importlinter-config revision
  daddcdabde8d0842d54467cbc1fdfed7c57c4ed1, whose source history includes local main revision
  b9d9ef506a526cf9ab684ca2a772a67ea532ac70.

The early revision has no contur.database package, so the later layered contract is not
retroactively applied to T0. T0 is used only for a like-for-like Pylint comparison. T1 is the
Import Linter baseline against which the unfinished database-boundary redesign can later be
evaluated.

## Fixed tool environment

- Python 3.11.9
- Pylint 4.0.6
- astroid 4.0.4
- Import Linter 2.13
- grimp 3.15

The tools were installed in an isolated temporary virtual environment.

## Pylint command

Run from each exported repository snapshot:

    pylint src/contur --recursive=y --ignore=run_mkthy.py \
      --disable=all --enable=cyclic-import \
      --init-hook='import sys; sys.path.insert(0, "src")' --score=n --persistent=n

The committed src/contur/run/run_mkthy.py in the current source history contains unresolved Git
conflict markers. It was excluded from both Pylint snapshots for a like-for-like comparison and
from the Import Linter snapshot because the current file cannot be parsed. The exclusion must be
removed and the baseline rerun after the upstream syntax problem is fixed.

With that explicit limitation, both T0 and T1 report five R0401 cycle paths. These are paths
reported by Pylint, not five proven independent root causes. The historical note that an earlier
run reported eight paths remains unverified until its original command, tool version, revision and
raw output are recovered.

## Import Linter command

Run from the T1 exported snapshot after excluding the unparsable file:

    PYTHONPATH=src lint-imports --no-cache --verbose

The proposed layered contract is broken:

- contracts kept: 0;
- contracts broken: 1;
- illegal direct imports listed: 12;
- files analysed: 64;
- dependencies analysed: 217.

The broken-contract count and illegal-import count are different metrics and must not be combined.
The raw output records every listed import.

## Evidence boundary

These results are a provisional, reproducible baseline rather than a final dissertation result.
The final comparison must use the same tool versions, commands and contract; include the excluded
file after its conflict markers are fixed; record exact revisions; report cycle paths, broken
contracts and illegal imports separately; and preserve the raw outputs.

## Subsequent GitLab CI baseline

A later GitLab CI run on branch `importlinter-config` supersedes the Import Linter counts above:

- commit: `a1985475`;
- merge request: `!652`;
- pipeline: `2736579327`;
- job: `15742809546`;
- image: `python:3.9`;
- Import Linter 2.5.2 and Grimp 3.13;
- command: `lint-imports --verbose`, with `PYTHONPATH=$CI_PROJECT_DIR/src`;
- result: 65 files, 224 dependencies, one broken contract and 12 illegal direct imports.

This run used the single layered contract after `contur.database` had been added to it. The
corrected `run_mkthy.py` was included. The Import Linter job returned status 1 because the
contract was broken; `allow_failure: true` converted this to a pipeline warning. The result is
therefore a reproducible observation baseline, not a passing architecture check. The associated
pipeline also recorded a successful `pytest` job. The full `a1985475` GitLab trace was supplied
in the project record but has not yet been archived as a raw local text file.
