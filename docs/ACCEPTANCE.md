# Reviewer reproduction guide

Development preview, not a submitted/accepted contest result and not a published Mooncakes release.

## 1. Core tests and formatting

Install the official MoonBit toolchain and Node.js 22. From repository root:

```bash
bash tools/verify.sh
```

This runs `moon fmt --check` and check/build/test/example for JS and wasm-gc with `--deny-warn`. Logs remain available when a command fails. The same unit tests run on both targets; their counts must not be added as distinct test cases.

## 2. Offline tool and CLI

```bash
moon build bridge --target js --release --deny-warn
python tools/build_web.py
node dist/cli.cjs dist/samples/synthetic_notch.s2p --format json
python tools/test_host.py
```

Open `dist/index.html`. The tool does not require a server or online model. Select a sample, switch parameters, edit the text to confirm old results are invalidated, and export both formats. Parsing and conversion run in the compiled MoonBit core.

## 3. Source package, clean extraction and API

```bash
python tools/check_package.py
```

Requires Python 3.11+ and Node.js. This creates a fresh `moon package --list` archive, checks paths/required assets/license, excludes build caches and generated logs, extracts to a temporary directory and reruns both target suites. It then rebuilds the bridge/workbench and executes the packaged file CLI. It also verifies formatting and committed generated public interfaces. No account login or `moon publish` is invoked.

## 4. Independent numerical and UI checks

```bash
python -m pip install scikit-rf==1.8.0 numpy==2.2.6 scipy==1.15.3 playwright==1.55.0
python -m playwright install chromium
python tools/crosscheck.py
python tools/test_measured.py
python tools/test_browser.py
```

Linux browser tests may additionally require Playwright system dependencies. CI installs these. Measured-fixture provenance and qualifications are in [TEST_DATA.md](TEST_DATA.md); supported, restricted and extended behaviours are in [COMPATIBILITY.md](COMPATIBILITY.md).

## Boundaries to retain in any submission

No full Touchstone certification, no instrument-control/calibration/de-embedding implementation, no arbitrary vendor impedance metadata support, no physical Android/iOS or Safari validation, and no Mooncakes publication. Organizer topic clearance and registration are separate from engineering tests. Do not add personal contact details to this public repository.
