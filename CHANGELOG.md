# Changelog

## 0.1.0 — 2026-09-23

- Freeze the reviewed one/two-port Touchstone implementation for the competition delivery.
- Align package, README, compatibility and consumer-example versions.
- Add a five-minute demonstration script and technical walkthrough.
- Publish a tagged GitHub release containing the fully checked submission bundle, standalone workbench and SHA256 checksums.
- Retain the RC3 runtime, public API and 104 core tests unchanged.

## 0.1.0-rc.3

- Add an offline review homepage to the submission bundle, linking the workbench, demonstration route and current reports.
- Compile the README and library-guide examples verbatim on JS and wasm-gc, both from the checkout and the extracted source package.
- Fix the CI configuration link in the offline source documentation and validate local documentation targets.
- Add an architecture guide covering the shared MoonBit core and main data flow.
- Keep the public API, numerical implementation and 104 core tests unchanged.

## 0.1.0-rc.2

- Recover from worker startup, message and timeout failures without reloading the workbench.
- Release failed worker URLs and pending deadlines; ignore delayed errors from retired workers.
- Add eight fault-injection scenarios to browser, platform and submission checks.
- Keep the MoonBit core and its 104 tests unchanged.

## 0.1.0-rc.1

- Assemble a single acceptance bundle with the offline workbench, rebuildable source, feature checklist, current reports and screenshots.
- Add `tools/prepare_submission.py` to run the complete acceptance suite and verify the delivered ZIP.
- Limit runtime packaging to named project assets. Reject unrelated files, directories and symlinks without deleting local results.
- Add ten packaging regression scenarios and run them again after source-package extraction.
- Preserve ignore rules in the source archive and verify that a tested extraction repackages to the same file set and bytes.
- Keep the MoonBit core API, numerical implementation and 104 existing tests unchanged.

## 0.1.0-dev.9

- Calculate dB in log space to avoid intermediate magnitude overflow and subnormal rounding loss.
- Retain the finite dB readout when a derived linear magnitude is outside the Double range.
- Add eight numeric regression tests and a 100-digit Decimal reference corpus on JS and wasm-gc.
- Check JSON and CSV agreement for extreme finite values and include numeric verification in source-package reconstruction.

## 0.1.0-dev.8

- Close the output handle when file metadata lookup fails before writing.
- Add six file-I/O fault tests covering short reads, growing input, read/metadata/write errors and replacement-file preservation.
- Run fault tests on each supported platform and again after source-package extraction.
- Add ten black-box tests for the public MoonBit interface, bringing the in-package suite to 96 tests.

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
