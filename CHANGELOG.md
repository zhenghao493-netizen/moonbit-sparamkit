# Changelog

## 0.1.0-dev.2 — 2026-09-22

### Added

- One/two-port strict Touchstone S-parameter parsing and RI/MA/DB conversion.
- Line/column diagnostics, numerical range checks, bounded tokens and records.
- S-parameter lookup, magnitude/phase helpers, CSV export.
- 46 MoonBit test cases and three synthetic input fixtures.
- JS and wasm-gc verification jobs with retained logs.

### Fixed after real CI execution

- Corrected three MoonBit exponent literals in tests; input-file decimal grammar was not changed.
- Replaced deprecated Show derivation with Debug, made trait extensions explicit, and marked internal parser types private.
- Updated the example's diagnostic output and enabled `--deny-warn` for checks, builds, tests and examples.

### Verified

Code commit `133f6be4bc97710862253473c47a7e811a0297de` passed GitHub Actions [run 35729074198](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35729074198): 46/46 tests on each of JS and wasm-gc, plus checks, builds and the built-in example. This is remote verification, not a claim of local toolchain execution or complete Touchstone conformance. See [verification/STATUS.md](verification/STATUS.md).
