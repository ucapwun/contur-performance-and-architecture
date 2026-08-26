# Contur dissertation profiling experiments

These scripts collect dissertation-grade evidence without modifying or switching a source
checkout. Run them on the UCL cluster after loading the normal CEDAR/Rivet/Contur environment.

## Files

- `run_profile_experiment.sh`: validates revisions and imported source paths, alternates
  unprofiled runs, records GNU `time -v`, and produces one serial cProfile per case.
- `profile_summary.py`: exports cumulative/internal pstats reports and a machine-readable summary.
- `summarise_timings.py`: converts GNU `time -v` logs into per-run, grouped and two-case effect
  tables (mean, sample standard deviation, percentage reduction and speed-up ratio).
- `core_outputs.py`: extracts `SMBG`, `EXP` and `HLEXP` rows from `contur_run.db`, or compares two
  extracted CSV files exactly.
- `evidence-inventory.md`: provenance audit of the files already recovered locally.

## One-time cluster preparation

Use separate worktrees so the formal experiment does not change the working development branch.
The commands below create new directories; choose paths that do not already exist.

```bash
cd /unix/cedar/junyingwu/contur
git fetch origin

git worktree add --detach \
  /unix/cedar/junyingwu/dissertation_worktrees/observable_before \
  cb0d0f1866caae0bbc3393a5c9c04504a01716cb

git worktree add --detach \
  /unix/cedar/junyingwu/dissertation_worktrees/observable_after \
  d18011524877b53be0be7d21d78825a5bc606974
```

Load the normal environment and build each checkout using the same procedure:

```bash
source "$CEDARINSTDIR/setupEnv.sh"
make -C /unix/cedar/junyingwu/dissertation_worktrees/observable_before
make -C /unix/cedar/junyingwu/dissertation_worktrees/observable_after
```

Copy the complete `experiments` directory to the cluster, for example under
`/unix/cedar/junyingwu/dissertation_tools/experiments`.

## Experiment B: isolated Observable optimisation

```bash
bash /unix/cedar/junyingwu/dissertation_tools/experiments/run_profile_experiment.sh \
  --case baseline \
    /unix/cedar/junyingwu/dissertation_worktrees/observable_before \
    cb0d0f1866caae0bbc3393a5c9c04504a01716cb \
  --case modified \
    /unix/cedar/junyingwu/dissertation_worktrees/observable_after \
    d18011524877b53be0be7d21d78825a5bc606974 \
  --grid /unix/cedar/junyingwu/contur_compare/grid_snapshot \
  --out-root /unix/cedar/junyingwu/contur_compare/dissertation_runs \
  --experiment observable_isolated \
  --repetitions 3
```

The six unprofiled timings run in the order baseline, modified, modified, baseline, baseline,
modified. The two cProfile runs occur afterwards. Do not add `--nopyscripts` unless it is confirmed
that omitting it makes the two revisions perform non-equivalent work; whichever choice is made must
be identical on both sides and recorded as an extra argument after `--`.

## Experiment C: latest-main status

After `git fetch origin`, resolve and record the full main hash, then create and build a separate
worktree. Substitute the recorded hash in both positions below.

```bash
git -C /unix/cedar/junyingwu/contur rev-parse origin/main

bash /unix/cedar/junyingwu/dissertation_tools/experiments/run_profile_experiment.sh \
  --case latest \
    /unix/cedar/junyingwu/dissertation_worktrees/latest_main \
    FULL_MAIN_HASH \
  --grid /unix/cedar/junyingwu/contur_compare/grid_snapshot \
  --out-root /unix/cedar/junyingwu/contur_compare/dissertation_runs \
  --experiment latest_main_status \
  --repetitions 3
```

## Output comparison

Each successful run containing `ANALYSIS/contur_run.db` automatically receives a
`core_outputs.csv`. A two-case experiment compares every corresponding CSV automatically and
stores the results under `comparisons/`. A missing or different core-output set makes the runner
exit non-zero after preserving all artefacts. A comparison can also be repeated manually with:

```bash
python /unix/cedar/junyingwu/dissertation_tools/experiments/core_outputs.py compare \
  BASELINE/core_outputs.csv MODIFIED/core_outputs.csv
```

The command exits with status zero only when all ordered `SMBG`, `EXP` and `HLEXP` rows match
exactly. Preserve the printed result with the experiment artefacts.

## Acceptance checks

Before using a result in the dissertation, verify that:

1. both exit-status files contain `0`;
2. `environment_*.txt` records the expected full commit and an imported module under that case's
   source tree;
3. the YODA-file count is the expected 300;
4. the same extra Contur arguments were used for both comparison cases;
5. all unprofiled timing files and both raw `.prof` files are retained;
6. the core-output comparison passes, or every difference is investigated;
7. no result directory was reused or overwritten.
