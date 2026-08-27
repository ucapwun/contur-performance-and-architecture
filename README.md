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
- [`thesis/`](thesis/) contains the dissertation PDF associated with this evidence snapshot.

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

The complete 300-file grid input is not included in this repository. The retained timing,
environment and comparison files support the dissertation's reported result, but reproducing the
full benchmark also requires access to the recorded Contur grid input described in
[`profiling/README.md`](profiling/README.md).

## Status and evidence cut-off

Architecture contribution status was recorded on 16 August 2026 and is reported as a fixed
dissertation cut-off. Later database-boundary changes are outside the scope of this evidence
snapshot. The only later branch revision retained here is the configuration-only Import Linter
commit `af8102009b` from 26 August 2026, which updates the proposed contract after the merged
`webpages` relocation without adding a new quantitative result.
