# Changelog

## 0.1.0-dev.3 — 2026-09-22

### Fixed

- Accept pure CR and mixed CR/LF/CRLF without merging physical records or corrupting diagnostic line numbers.
- Accept exactly one initial BOM; do not silently strip embedded or repeated markers.
- Refuse an offline build when the compiled bridge is absent instead of reusing a stale dist/core.cjs.

### Added

- 18 compatibility regression tests, bringing the core suite to 72 tests. Includes 24 option permutations and all eight two-port continuation boundaries inside those test definitions.
- Format checking, canonical generated API checks, fresh source ZIP inspection, isolated extraction/rebuild and packaged CLI execution.
- Eight CLI/build integration groups and a BOM/CR browser file-input scenario.
- Two content-locked, upstream-labelled measured sample comparisons, separate from the 77-file synthetic corpus; no fixture bytes or parser source vendored.
- Explicit compatibility matrix, data-provenance document and reviewer reproduction guide.

### Verification

Tests and their limitations are recorded per code commit in [verification/HARDENING.md](verification/HARDENING.md). This is a development preview, not a Mooncakes publication or contest acceptance.

## 0.1.0-dev.2 — 2026-09-22

### Initial core

- One/two-port strict Touchstone S-parameter parsing and RI/MA/DB conversion.
- Line/column diagnostics, numerical range checks, bounded tokens and records.
- S-parameter lookup, magnitude/phase helpers, CSV export.
- Initial 46 MoonBit tests and three synthetic input fixtures, then eight checked JSON report tests (54 total at the offline-workbench milestone).
- JS and wasm-gc verification jobs with retained logs.
- Offline single HTML, shared MoonBit bridge, Node file CLI, deterministic RC/RLC demos, 77-file scikit-rf comparison and 15 browser scenarios.

### Corrections after real execution

- Corrected three exponent literals in tests; input-file decimal grammar was unchanged.
- Migrated Show derivation to Debug, made trait extensions explicit, marked internal types private and enabled --deny-warn.

Historical core and offline-workbench results are retained in [verification/STATUS.md](verification/STATUS.md). Earlier tests did not establish full Touchstone conformance or hardware accuracy.
