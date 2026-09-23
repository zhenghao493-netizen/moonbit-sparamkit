# Changelog

## 0.1.0-dev.7

- Add CLI `--output` / `-o` to save JSON or CSV as UTF-8 without overwriting existing files.
- Reject repeated options and support dash-leading filenames after `--`.
- Bound input reads even if a file grows after its size check; clean up partial output on write failure.
- Add 10 public-API black-box tests and CLI file-output/failure-path checks.
- Verify direct file export again when rebuilding the source package.

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
