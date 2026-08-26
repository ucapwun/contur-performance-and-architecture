# Cross-package direct-import counts

These files record the package-level import census used in Chapter 4. They were generated on
20 August 2026 with Python 3.12.4 by:

```bash
python3 \
  dependency-analysis/count_package_imports.py \
  --repo <path-to-contur> \
  --revision cb0d0f1866caae0bbc3393a5c9c04504a01716cb \
  --label baseline-cb0d0f1866 \
  --output-dir dependency-analysis/package-import-counts

python3 \
  dependency-analysis/count_package_imports.py \
  --repo <path-to-contur> \
  --revision cf6ca9b157c5bf54f58e661bc236fec5b399b5be \
  --label post-change-cf6ca9b157 \
  --output-dir dependency-analysis/package-import-counts
```

The baseline is the starting source revision used by the original Import Linter branch. The
post-change revision is the locally recorded `origin/main` revision used for this rerun. It
contains the merged utility clean-up, theory-lookup, database-package, scan-helper and webpage
relocations discussed in Chapter 5. It does not contain the open low-level analysis-record work.

## Counting rule

The script parses every `src/contur/**/*.py` file with the standard-library `ast` module. One
imported target package on an `import` or `from ... import ...` statement counts as one direct
import. Module-scope, function-local and `TYPE_CHECKING` imports are included. Imports within the
same top-level Contur package and imports of third-party modules are excluded. No file failed to
parse in either revision. The recorded `SyntaxWarning` messages concern string escapes and do not
exclude the affected files.

The baseline census contains 167 cross-package direct imports. Applying the target directions
encoded by the script reports 14 imports across eight disallowed directions. This exactly
reproduces the original Import Linter CI snapshot, providing a check that the AST counting unit is
comparable with that snapshot.

The post-change census contains 170 cross-package direct imports. Against the same target
directions, it reports 26 imports across eleven disallowed directions. The increase does not mean
that every change worsened the architecture. The utility violations fall to zero, while moving
`static_db` into the new `database` package makes sixteen existing callers visible as direct
accesses that conflict with the target restriction that only `data` may access `database`.

## Files

- `*-imports.csv`: one row per counted direct import, with source location and scope;
- `*-matrix.csv`: complete package-direction matrix, including incoming and outgoing totals;
- `*-violations.csv`: directions that conflict with the target structure;
- `*-summary.json`: revisions, counting rules, parse status and totals.
