# Contur performance and package architecture

This repository accompanies an MSc Scientific Computing dissertation at UCL. The project studies
performance profiling and package dependency architecture in
[Contur](https://gitlab.com/hepcedar/contur).

Most production changes were developed and reviewed in the upstream Contur GitLab repository.
This repository provides a stable assessment index, the project-specific profiling and dependency
analysis tools, and the evidence used in the dissertation. It does not present open or draft work
as merged into Contur.

## Repository contents

- [`CONTRIBUTIONS.md`](CONTRIBUTIONS.md) maps each contribution to its GitLab merge request,
  recorded status, revision and dissertation topic.
- [`profiling/`](profiling/) contains the experiment scripts and retained evidence for the
  controlled performance comparison.
- [`dependency-analysis/`](dependency-analysis/) contains the recorded Import Linter and Pylint
  snapshots together with the reproducible cross-package import census.
- [`patches/`](patches/) explains why the linked upstream merge requests are used as the
  authoritative contribution diffs.
- [`tests/`](tests/) contains standard-library tests for the retained evidence and the main
  analysis-script boundary cases.
- [`thesis/`](thesis/) contains the dissertation PDF associated with this evidence snapshot.

## Quick start

The repository's tests use only Python's standard library and the retained sample evidence. They
check that the baseline cProfile file can be read, that the 300 selected statistical output rows
match between one recorded baseline and modified run, and that mismatched outputs, elapsed-time
formats and non-module-scope imports are handled as intended:

```bash
python3 -m unittest discover -s tests -v
```

The retained profile can also be summarised directly:

```bash
python3 profiling/scripts/profile_summary.py \
  profiling/results/observable_isolated_20260803T004228+0100/profiles/baseline/profile.prof \
  --output-dir /tmp/contur-profile-summary
```

To inspect the interactive call graph, install
[SnakeViz](https://jiffyclub.github.io/snakeviz/) and open the same `.prof` file. The dependency
census requires a local Contur Git checkout; a complete example is given in
[`dependency-analysis/package-import-counts/README.md`](dependency-analysis/package-import-counts/README.md).

## Main recorded result

For the accepted controlled comparison, three serial warm-cache runs were performed for each of
two isolated Contur revisions on one UCL HEP cluster node. Each run processed a 10 by 10 grid with
300 YODA input files. Removing unused expected-scatter construction reduced mean elapsed time from
601.750 s to 386.767 s, a reduction of 35.726%. The selected `SMBG`, `EXP` and `HLEXP` output rows
matched exactly in three unprofiled comparisons and one additional profiled comparison.

The result is bounded to the recorded workload and environment. See
[`profiling/README.md`](profiling/README.md) for the revisions, commands, dependencies and retained
evidence.

## Software and data dependencies

The analysis scripts use Python 3 and its standard library. Re-running Contur itself additionally
requires a working Contur environment and its scientific dependencies, including Rivet and YODA.
The accepted run used Python 3.9.12, Contur 3.1.4, Rivet 4.1.3 and YODA 2.1.3.

The complete 300-file grid input is not distributed in this repository. The retained `.prof` and
`core_outputs.csv` files provide sample inputs for the smoke tests above. They support inspection
of the recorded analysis, while reproducing the full benchmark also requires access to the
original Contur grid input described in [`profiling/README.md`](profiling/README.md).

## Status and evidence cut-off

Architecture contribution status was recorded on 16 August 2026 and is reported as a fixed
dissertation cut-off. Later database-boundary changes are outside the scope of this evidence
snapshot. The only later branch revision retained here is the configuration-only Import Linter
commit `af8102009b` from 26 August 2026, which updates the proposed contract after the merged
`webpages` relocation without adding a new quantitative result.
