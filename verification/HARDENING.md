# Compatibility and packaging verification

Development preview 0.1.0-dev.3, 2026-09-22. This report supplements the historical offline-workbench snapshot in STATUS.md.

## Completed pre-integration runs

- Functional changes: `60074ea5ad663bad75b100c46d757000c101a992`.
- Canonical formatting / generated API commit: `46fe7a79f014eb5b1daab0d48454e407a52748c1`.
- [Normalize and recheck run 35739776164](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35739776164): successful normalization, both target suites and fresh-package reconstruction. The initial unformatted commit's standalone formatting gates failed as intended; that failure is retained, not presented as a pass.
- [Tool run 35739776345](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35739776345): built and exercised the compiled core, synthetic comparison, two public examples, CLI and Chromium file-mode UI.

The downloaded tool-verification archive was inspected. It records:

| Check | Actual result |
| --- | --- |
| Synthetic scikit-rf corpus | 77 files / 4398 complex values; max absolute complex difference 6.938893903907228e-16 |
| Two upstream-labelled measured files | 2 files / 141 complex values; max absolute complex difference 5.551115123125783e-17 |
| Node file CLI / stale-build handling | 8 scenario groups passed |
| Chromium local file UI | 16 checks passed, including BOM and CR-only file input |

These error maxima apply only to the recorded inputs. They are not universal bounds. The public fixtures are the unchanged scikit-rf 1.8.0 ring-slot and inductor examples; provenance is locked to their Git blobs before comparison. Upstream describes them as measured, but the acquisition was not repeated by this project. See docs/TEST_DATA.md for the inductor export-header qualification.

Local use of the same official MoonBit toolchain also passed 72/72 tests on JS and wasm-gc with --deny-warn, format checks, package reconstruction and the eight host test groups. Local browser file navigation remains blocked by environment policy; the actual file-mode browser evidence is from GitHub Actions, not that local attempt.

## Integration status

The cleanup commit removes the one-off write-enabled normalization workflow. The permanent verification workflows are read-only. Full CI must be checked on the cleaned, formatted branch before merge; later results will be appended with their exact commit and run identifiers. No package has been published and no competition form has been submitted.
