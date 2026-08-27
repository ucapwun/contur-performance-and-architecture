# Contribution index

This index separates changes merged into upstream Contur from work that remains on feature
branches. Architecture merge-request status was recorded on 16 August 2026. The Import Linter
row additionally records the later configuration-only revision described below.

| Contribution | Upstream record | Recorded status | Stable revision | Dissertation topic |
|---|---|---|---|---|
| Remove unused expected-scatter construction | [Commit](https://gitlab.com/hepcedar/contur/-/commit/d18011524877b53be0be7d21d78825a5bc606974) | Merged in the recorded upstream history | `d18011524877b53be0be7d21d78825a5bc606974` | Performance profiling and optimisation |
| Clean utility imports and undefined names | [MR !653](https://gitlab.com/hepcedar/contur/-/merge_requests/653) | Merged, pipeline passed | `56d4e7564081f6c8acad1e63f6e464d3d8645867` | Utility audit |
| Move theory-prediction lookup to `factories` | [MR !654](https://gitlab.com/hepcedar/contur/-/merge_requests/654) | Merged, pipeline passed | `02ca39fc64d7110c7f95985c4ffc0cda302e48c6` | Responsibility relocation |
| Move static database access to a `database` package | [MR !657](https://gitlab.com/hepcedar/contur/-/merge_requests/657) | Merged, pipeline passed | `39683d8c296dd710a2e80321a5610782f8cdd82a` | Database package boundary |
| Move `newlogspace` to the `scan` package | [MR !674](https://gitlab.com/hepcedar/contur/-/merge_requests/674) | Merged, pipeline passed | `353301fe709ccfa90d45aea0a83f0b9e308eb46c` | Responsibility relocation |
| Move webpage generation out of `util` | [MR !678](https://gitlab.com/hepcedar/contur/-/merge_requests/678) | Merged, pipeline passed | `436f021355ca5834e39a740df3fcbf1720fc5beb` | Webpage package boundary |
| Characterise analysis-database object identity | [MR !681](https://gitlab.com/hepcedar/contur/-/merge_requests/681) | Merged, pipeline passed | `1a8dd9835c8f9248d1054e95365cf256a25585f1` | Database redesign tests |
| Add low-level analysis database records | [MR !685](https://gitlab.com/hepcedar/contur/-/merge_requests/685) | Open feature branch | `5f621beed978905f09ecc96772d26bf01a10883d` | Partial database boundary implementation |
| Add Import Linter dependency rules | [MR !652](https://gitlab.com/hepcedar/contur/-/merge_requests/652) | Draft feature branch, intentionally not merged | `af8102009b58f7a60a527bfb25e339f88dfd3fcd` | Non-blocking architecture check updated after the `webpages` relocation |

The target dependency structure in the dissertation is a design target. It is not a claim that
the current Contur package already satisfies every proposed boundary.

The Import Linter row records the later configuration state. Its quantitative dissertation
snapshot remains the earlier CI run at `a1985475be99f8708441f35c9a40875424350fe7`; no new
violation total is attributed to `af8102009b`.
