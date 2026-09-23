# CLI and library integration — 0.1.0-dev.7

Implementation: `aaccf1f9ebee22b2f0be253c7c7fa06980e122f0`.
Tested PR checkout: `bdb1a07a345660c715e228312079ed6eccd5979c`.
[PR #5](https://github.com/zhenghao493-netizen/moonbit-sparamkit/pull/5) merged as `056db9e19b3c0d4379b3be52c2016862ecd6c205`; comparison with the tested checkout returned no changed files.

## Changes

The CLI accepts piped UTF-8 input through `- --ports 1|2` and can create result files with `--output` / `-o`. Output files are opened exclusively after successful parsing, preserving existing files and the input path. Default stdout JSON diagnostics remain compatible; diagnostics go to stderr when a file output is selected.

File reads use one descriptor and bounded chunks. POSIX named-pipe paths are rejected without waiting for a writer. Argument validation covers duplicate options, missing values and literal filenames after `--`; a closed output pipe returns an I/O error rather than an uncaught exception.

A separate MoonBit workspace application now exercises the public library interface. It imports the local library module and runs five tests for parsing, asymmetric port queries, diagnostics and sample limits, exports, and undefined zero metrics. This is a local source-dependency test, not a Mooncakes registry installation.

## Results

| Check | Result | Workflow |
| --- | --- | --- |
| Core JS / wasm-gc | 86/86 tests per target, formatting, check, build and example | [35800171654](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35800171654) |
| Source archive | 57 files; fresh extraction, both core suites, CLI tests and external consumer rebuilt | [35800171636](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35800171636) |
| Numerical regression | 77 synthetic files / 4,398 complex values and two pinned public examples / 141 values passed | [35800171649](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35800171649) |
| Platform matrix | Results below | [35800171665](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35800171665) |

| Environment | New CLI scenarios | Existing host groups | Offline browser scenarios |
| --- | --- | --- | --- |
| Linux / Chromium | 24 passed | 14 passed | 30 passed |
| Linux / Firefox | 24 passed | 14 passed | 30 passed |
| Linux / Playwright WebKit | 24 passed | 14 passed | 30 passed |
| Windows / Chromium | 23 passed; POSIX FIFO skipped | 14 passed | 30 passed |

The symlink-output check passed on both operating systems. The FIFO scenario is unavailable on Windows and is recorded in the report's skipped list. All browser runs used file mode. Browser and host scenarios are repeated across environments, not counted as distinct cases.

The extracted-package tests on both Linux and Windows also passed the standalone application's five API cases on JS and wasm-gc, then ran its two-frequency JSON example. These five cases are separate from the unchanged 86-case library suite. The MoonBit numerical core and browser interaction implementation were not changed in this iteration.

## Downloaded artifacts

The package, tool and four platform report archives were downloaded and their JSON results inspected. Edited source files matched the locally tested copies. All 11 runtime payload hashes matched the manifest. The downloaded CLI was additionally exercised with --version, --help and stdin-to-file CSV export.

- Source ZIP: `ttxiangshang-sparamkit-0.1.0-dev.7.zip`; SHA256 `61bdceef85a9a59e400ea33994e70a8d4f77b3768e8528f32ab41a0fc59056a8`.
- Tool artifact: `10725637436`; ZIP SHA256 `14ad8b72e06deb015a0d11d6080d14c66af3783816926618f1fa760db2c16741`.
- Tool report artifact: `10725617352`; ZIP SHA256 `ede83e3f1054dcd66039d1dae19f12a0f402596e76acd98c11ff75caca9d9597`.
- Compiled core SHA256: `af2c3c38071827385902ff84b28f0361a018571bc93878e789b620f902668a71`, unchanged from dev.6.

The runtime manifest identifies the tested PR checkout. This record is a later documentation-only addition. Usage examples are in [CLI.md](../docs/CLI.md) and [LIBRARY.md](../docs/LIBRARY.md).
