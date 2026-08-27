# Dependency analysis evidence

The original Import Linter baseline was recorded by GitLab job `15420374888` in pipeline
`2688653739` at commit `c88cd32e61d76d9916bc2b849a2d58e7766b7636` on the
`importlinter-config` branch. The branch added the CI job and contract without changing files
under `src/contur`. The run therefore records the starting source before the later architectural
changes and before the dedicated `database` package existed. It reported 14 direct violations
across eight package directions.

The complete job trace has not yet been archived in this local repository. The current evidence
is the retained GitLab screenshot, which records the commit, job, pipeline, complete violation
list, broken-contract exit status and passing `pytest` job.

The `2026-08-04-baseline` directory records a later Import Linter contract, command output and
related Pylint snapshots used for the architecture strand.

The Import Linter configuration belongs to draft merge request
[!652](https://gitlab.com/hepcedar/contur/-/merge_requests/652). It is a non-blocking measurement
of a provisional boundary and is intentionally not presented as an enforceable, passing contract.
The recorded snapshot at revision `a1985475be99f8708441f35c9a40875424350fe7` reported 12 direct
violations across eight package directions.

The `2026-08-26-webpages-contract` directory records a later configuration-only revision of the
same branch at `af8102009b58f7a60a527bfb25e339f88dfd3fcd`. This revision follows the merged
`webpages` relocation. It adds `webpages` to the proposed layers, makes the layered contract
exhaustive, and adds a protected contract under which only `contur.data` may import
`contur.database` directly. The CI job remained non-blocking. No new violation total from this
configuration is used in the dissertation, so the recorded quantitative result above is not
replaced.

The reconstructed result at revision `ea70f51cb12af174459aa4f7a254943d133cbd9f` is no longer
used as the dissertation's initial baseline because several project changes had already modified
the source by that point.

## Cross-package import census

`count_package_imports.py` uses the Python standard-library `ast` module to count direct imports
between top-level Contur packages at specified Git revisions. The retained baseline and
post-change CSV and JSON files use the same counting rule and record every counted source
location, the complete package matrix and the directions that conflict with the dissertation's
target structure. The baseline census reproduces the original 14 Import Linter violations across
eight package directions.
