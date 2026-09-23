# Changelog

## 0.1.0-dev.8

- Calculate dB in log space to avoid intermediate magnitude overflow and subnormal rounding loss.
- Retain the finite dB readout when a derived linear magnitude is outside the Double range.
- Add eight numeric regression tests and a 100-digit Decimal reference corpus on JS and wasm-gc.
- Check JSON and CSV agreement for extreme finite values and include numeric verification in source-package reconstruction.

## 0.1.0-dev.7

- Accept piped UTF-8 input with `- --ports 1|2`.
- Add `--output` / `-o` for writing a new CSV or JSON file without overwriting existing files.
- Bound file and stdin reads, reject duplicate options, and handle closed output pipes.
- Add `--version` and literal input paths after `--`.
- Test CLI workflows and independent MoonBit workspace consumers during source-package reconstruction.
- Add command-line and library integration guides.

## 0.1.0-dev.6

- Add linked frequency readouts for magnitude and phase plots, with mouse, slider and keyboard selection.
- Keep the selected frequency when switching S parameters; clicking a curve reveals the matching table page.
- Add a diagnostic shortcut that selects the failing text field.
- Cache the selected parameter's data and avoid rebuilding plots when paging or moving the readout.
- Test complete 20,000-point JSON/CSV exports and rejection at 20,001 points.
- Read the expected package version from moon.mod in host tests.

## 0.1.0-dev.5 — 2026-09-22

- Fix repeat selection of the same file, stale analysis completion and pending CSV exports.
- Use explicit UTF-8 encoding in build scripts and host tests.
- Add version/build identifiers, a file manifest and an offline integrity checker.
- Add Linux Chromium, Firefox and WebKit tests, plus Windows Chromium and PowerShell verification.

## 0.1.0-dev.4 — 2026-09-22

- Check recognized Port Impedance declarations against the common reference impedance.
- Reject conflicting, complex or incomplete declarations with positioned diagnostics.
- Add 14 core tests, bringing the suite to 86 cases.

## 0.1.0-dev.3 — 2026-09-22

- Support CR and mixed line endings, with accurate diagnostic positions.
- Accept one initial BOM and reject embedded or repeated markers.
- Reject builds with a missing compiled bridge instead of reusing stale output.
- Add 18 compatibility tests, source-package reconstruction and generated API checks.
- Add provenance-locked comparisons for two public scikit-rf examples.

## 0.1.0-dev.2 — 2026-09-22

- Implement one/two-port Touchstone S-parameter parsing, RI/MA/DB conversion, diagnostics and CSV/JSON export.
- Add the offline browser workbench, shared MoonBit bridge, Node CLI and synthetic RC/RLC examples.
- Add 54 MoonBit tests, a 77-file scikit-rf comparison corpus and browser interaction tests.

Detailed test runs are recorded in [verification/](verification/).
