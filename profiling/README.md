# Performance profiling evidence

## Accepted controlled comparison

- Baseline revision: `cb0d0f1866caae0bbc3393a5c9c04504a01716cb`
- Modified revision: `d18011524877b53be0be7d21d78825a5bc606974`
- Host: `pc207.hep.ucl.ac.uk`
- Execution: serial (`--nomultip`), warm cache
- Workload: 100 model-parameter points and 300 YODA files
- Repetitions: three unprofiled runs per revision, followed by one profiled run per revision
- Environment: Python 3.9.12, Contur 3.1.4, Rivet 4.1.3 and YODA 2.1.3

The unprofiled run order was baseline, modified, modified, baseline, baseline, modified. Mean
elapsed time changed from 601.750 s to 386.767 s. The diagnostic profiles recorded 831.269 s
before the change and 534.094 s after it. Profiled times include profiler overhead and are not
the primary benchmark.

## Contents

- `scripts/run_profile_experiment.sh` runs and records the controlled comparison.
- `scripts/summarise_timings.py` produces the timing tables.
- `scripts/profile_summary.py` exports readable `pstats` summaries.
- `scripts/core_outputs.py` extracts and compares selected database output fields.
- `scripts/historical-line-profiler/` preserves the recovered exploratory driver and logs.
- `results/observable_isolated_20260803T004228+0100/` contains the accepted commands, timings,
  profiles, output extracts and comparison records.

Generated `contur_run.db` files are intentionally omitted from this assessment copy because eight
identical-size databases would add about 197 MB. The retained `core_outputs.csv`, comparison
records, manifests, commands, logs and raw `.prof` files preserve the evidence used in the
dissertation. The original databases remain in the private project workspace.

## Re-running

The runner requires GNU `time`, Python 3, two built Contur worktrees and an input grid. Run:

```text
bash scripts/run_profile_experiment.sh --help
```

The full command used for the accepted comparison and its acceptance checks are recorded in
`scripts/experiment-protocol.md`. Host-specific paths in the retained command files document the
original run and will need to be changed for another machine.

The complete input grid is not yet present in this local repository draft. A redistributable
sample input and its expected output must be added before submission to satisfy the assessment
guidance independently of access to the UCL cluster.

