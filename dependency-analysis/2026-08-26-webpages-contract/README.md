# Import Linter configuration after the webpages relocation

This directory records the later configuration-only state of the `importlinter-config` branch at
commit `af8102009b58f7a60a527bfb25e339f88dfd3fcd`. It follows the merged relocation of webpage
generation from `contur.util.rst_utils` to `contur.webpages.report`.

The revision changed only `.gitlab-ci.yml` and `pyproject.toml`. It did not change files under
`src/contur`, and no new violation count from this configuration is used as a dissertation result.
The quantitative Import Linter result remains the earlier recorded run at `a1985475be`.

The saved contract adds four points that were absent from the earlier snapshot:

- `webpages` is included with `plot`, `scan` and `oracle` in the proposed layers;
- the layered contract is exhaustive;
- a protected contract permits direct imports of `contur.database` only from `contur.data`;
- the CI job installs `import-linter>=2.5,<2.6` before running `lint-imports --verbose`.

The CI job remained non-blocking through `allow_failure: true`.
`import-linter-contract.toml` is the exact Import Linter section extracted from `pyproject.toml`,
and `import-linter-ci.yml` is the exact job extracted from `.gitlab-ci.yml` at the recorded commit.
