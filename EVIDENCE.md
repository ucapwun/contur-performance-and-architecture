# Profiling evidence inventory

This inventory separates the accepted controlled rerun from historical artefacts and claims that
survive only in working notes.

## Accepted controlled rerun (3 August 2026)

The complete accepted result is stored under
`profiling/results/observable_isolated_20260803T004228+0100/`.

- isolated revisions: baseline `cb0d0f1866caae0bbc3393a5c9c04504a01716cb`; modified
  `d18011524877b53be0be7d21d78825a5bc606974`;
- workload: one 10x10 grid of 100 model-parameter points, with one YODA file per point at each
  of 7, 8 and 13 TeV, giving 300 YODA files in total;
- execution: serial (`--nomultip`), warm cache, three unprofiled repetitions per revision on
  `pc207.hep.ucl.ac.uk`;
- environment: Python 3.9.12, Contur 3.1.4, Rivet 4.1.3 and YODA 2.1.3;
- baseline elapsed time: mean 601.750 s, sample SD 4.181 s;
- modified elapsed time: mean 386.767 s, sample SD 3.186 s;
- difference: -214.983 s, a 35.726% reduction and 1.5558-fold speed-up;
- diagnostic cProfile totals: 831.269 s and 1,156,920,804 calls before; 534.094 s and
  736,177,812 calls after;
- `Observable.__getExpected` cumulative time: 300.498 s before and 0.654 s after;
- validation: three unprofiled pairs and one profiled pair each contained 300 identical ordered
  core-output rows; all eight processes exited with status zero.

The repeated unprofiled elapsed times are the primary performance result. The one profile per
revision is diagnostic because its reported time includes profiler overhead.

## Recovered historical line-profile artefacts

The original exploratory driver and two complete logs were recovered from the Cedar filesystem
and copied without modification to `profiling/scripts/historical-line-profiler/`:

- `profile_test_observable_lines.py` creates a `LineProfiler`, registers seven Observable methods
  through `add_function`, wraps `run_analysis.main` and prints the resulting statistics;
- `line_profile_single_runpoint.log` loads
  `/unix/cedar/junyingwu/contur/src/contur/factories/test_observable.py`;
- `line_profile_single_no_expected_yoda.log` loads
  `/unix/cedar/junyingwu/contur-dev/src/contur/factories/test_observable.py`.

Both logs identify Contur 3.1.4, the same input
`runpoint_0000.yoda.gz`, a timer unit of `1e-09 s`, host-side Cedar paths, identical `SMBG`, `EXP`
and `HLEXP` values, and exit status zero. The baseline log reports 958 entries to
`Observable.__getExpected` and 10.3573 s within the method: the reference-scatter clone accounts
for 24.2% and the point-wise `setY` line for 72.1%. The modified log reports 0.0168232 s within
the method and contains neither operation. The source listings and line numbers are consistent
with the isolated baseline and modified revisions below, although the historical logs do not
embed Git hashes. These artefacts therefore support line-level mechanism attribution; the
accepted controlled rerun remains the quantitative performance result.

## Revisions recovered from Git

| Role | Full revision | Status |
|---|---|---|
| Contur 3.1.3 tag | `3ffe4095702f89136c6278e3646ecddb31fa50fb` | Resolved locally from `contur-3.1.3` |
| Observable isolated baseline | `cb0d0f1866caae0bbc3393a5c9c04504a01716cb` | First parent of the optimisation commit |
| Observable modified | `d18011524877b53be0be7d21d78825a5bc606974` | Removes unused expected-scatter construction |
| Local `origin/main` reference at the 30 July 2026 audit | `4a005f6b84...` | Must be fetched and frozen again before the latest-main experiment |

The optimisation commit modifies only `src/contur/factories/test_observable.py`, with two lines
added and seven removed. This supports using its first parent and the commit itself as the isolated
before/after pair, provided both are built and run under the same environment and command.

## Historical local profile fingerprints not selected as evidence

These files were inspected in the private project workspace using `pstats` but are not distributed
in this assessment repository. Their totals do not match the recorded
`2043.157 s` or `1323.941 s` full-grid comparison, so filenames alone must not be used to relabel
them as that experiment.

| File | Profile total (s) | Total calls | Observable source signature |
|---|---:|---:|---|
| `contur-main/runarea/contur_3.1.3.prof` | 2443.467 | 1,102,569,529 | `__getExpected` line 212, 122,100 calls |
| `contur-main/runarea/profile_3.1.3_nomultip.prof` | 2462.017 | 1,104,640,670 | `__getExpected` line 212, 122,100 calls |
| `contur-main/runarea/313_profile.prof` | 2453.448 | 1,102,566,457 | `__getExpected` line 212, 122,100 calls |
| `contur-main/runarea/profile_main_nomultip.prof` | 867.874 | 1,139,863,127 | `__getExpected` line 171, 120,500 calls |
| `contur-main/runarea/profile_main.prof` | 1619.474 | 66,325,532 | No matching Observable functions |

Several other local profiles contain implausibly large totals for an elapsed-time comparison and
appear to aggregate or otherwise record a different execution shape. They remain archived but are
not selected as dissertation evidence without their generating commands and logs.

## Results retained only in working notes

`CONTUR_DEPENDENCY_NOTES.md` records the following results:

- baseline profile: `2043.157 s`, 1,156,914,449 calls;
- optimised profile with an explicit source-tree `PYTHONPATH`: `1323.941 s`, 736,177,380 calls;
- `Observable.__getExpected` cumulative time: `699.246 s` to `1.533 s`;
- exact matches for `SMBG`, `EXP` and `HLEXP` on runpoints `0000` through `0004` at 13 TeV;
- a successful optimised run with exit status zero.

The corresponding raw files named in the notes---including
`profile_main_3.1.4_nomultip.prof`, `profile_full_no_expected_yoda_srcpath.prof` and
`run_full_no_expected_yoda_srcpath.log`---are not present in this local workspace. Until they are
recovered from the cluster or replaced by the controlled rerun, the dissertation should continue
to call these values recorded or preliminary profile evidence rather than repeated wall-clock
benchmark results.

## Safe conclusions now

1. The isolated Observable optimisation reduced mean elapsed time by 35.726% for the accepted
   serial, warm-cache, 300-file workload on `pc207`.
2. All extracted core-output rows matched in four paired comparisons.
3. The source-loading failure mechanism is documented and the runner rejects the wrong module
   path automatically.
4. The older profile archive remains historical context and is not the primary dissertation
   benchmark.
5. No performance result for a later `main` revision is claimed by the dissertation or this
   repository.

## Architecture merge-request evidence (16 August 2026)

The architecture status below is kept separate from the profiling evidence. Merge status was
checked against the local `origin/main` history and the GitLab merge-request view supplied for
the dissertation update.

- `!678`, **Move webpage generation out of util**, is merged. Merge commit `436f021355` is an
  ancestor of local `origin/main`. The change moves `util/rst_utils.py` to
  `webpages/report.py`, updates the run entry point and adds two focused webpage tests. The new
  module still imports `database.static_db` directly.
- `!681`, **Characterise analysis database object identity**, is merged. Merge commit
  `1a8dd9835c` is an ancestor of local `origin/main`. Its tests show reuse of cached analysis,
  pool, beam and experiment instances, shared mutable SM-prediction identity across lookup paths,
  and reuse of the cached analysis by `obsFinder`.
- `!685`, **Add low-level analysis database records**, remains open. Branch commit
  `5f621beed9` is not an ancestor of local `origin/main`. It adds immutable low-level record
  classes and a record reader. Domain-object construction remains in `static_db.init_dbs()`, so
  this branch does not yet remove the database--data cycle.
- `!652`, **Add import-linter dependency rules**, remains a draft branch by design. It records
  violations through a non-blocking CI job and is intended to remain separate until the circular
  dependencies have been handled. The dissertation's quantitative snapshot remains the verified
  run at commit `a1985475`; a later like-for-like rerun is still required.

### Original Import Linter CI baseline

The original baseline was recorded by GitLab job `15420374888` in pipeline `2688653739` at
commit `c88cd32e61d76d9916bc2b849a2d58e7766b7636` on the `importlinter-config` branch. The branch
was based on source revision `cb0d0f1866caae0bbc3393a5c9c04504a01716cb`; its four commits
changed only `.gitlab-ci.yml` and `pyproject.toml`, so the Import Linter run measured the starting
Contur source without the later architectural changes. The dedicated `database` package did not
yet exist. The job used Python 3.9, installed `import-linter>=2.0`, and ran
`lint-imports --verbose`. The exact resolved Import Linter and Grimp versions are not present in
the retained screenshot.

The job reported 14 direct violations across eight package directions: `util -> factories` (1),
`util -> data` (3), `util -> run` (1), `data -> scan` (2), `data -> factories` (2),
`data -> plot` (1), `scan -> run` (1), and `factories -> plot` (3). The broken-contract exit
status is expected because the CI job used `allow_failure: true` to record violations without
blocking the pipeline. The accompanying `pytest` job passed. The complete raw job trace still
needs to be archived locally; the current record is the supplied GitLab job screenshot.
