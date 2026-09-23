# Public API and file I/O — 0.1.0-dev.8

Verified 2026-09-23. Implementation: `a261b013fe6b60ad04b2949e88a4f9ba4eb2ddfc`; tested PR checkout: `d2e2b8c53f45996ed1f50040a54c29eeaa02b8c4`.
[PR #6](https://github.com/zhenghao493-netizen/moonbit-sparamkit/pull/6) merged as `c75fcd9cbcaf158989cc5723dcd817e2d1615e7f`. Comparison with the tested checkout returned no changed files.

## Fix and regression coverage

The CLI opened a new output file and then called `fstatSync` outside its cleanup block. Injecting a metadata-read error reproduced an unclosed output handle on dev.7 (`outputClosed: false`). Moving that call inside the guarded block makes the same test close the handle (`outputClosed: true`). If file identity cannot be established, the error path closes the handle but leaves the empty file rather than deleting an uncertain path.

`tools/test_file_faults.py` adds six scenarios using temporary files and the compiled MoonBit core: short reads, input growth after a size check, input read failure, output metadata failure, partial write failure, and preservation of a replacement created by another writer. The growing-input test reads at most 2,097,153 bytes, using buffers no larger than 65,536 bytes. The partial-write test removes its own incomplete file; the replacement test keeps the other writer's file.

`api_test.mbt` adds ten public-interface tests: the README example, source enums and fields, index bounds, sample budgets, diagnostic fields, caller-created complex values, optional zero metrics, JSON fields, CSV consistency and impedance-conflict errors. These run without access to private parser helpers. The five separate-workspace tests introduced by PR #5 remain in place.

## Results

All four PR workflows passed:

| Layer | Result | Workflow |
| --- | --- | --- |
| Core | 96/96 on JS and wasm-gc; formatting, strict checks, build and example passed | [35801843850](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35801843850) |
| Source package | 60 files; fresh extraction, both 96-case suites, five external-consumer tests per backend, CLI and six file-fault cases passed | [35801843826](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35801843826) |
| Numerical regression | 77 synthetic files / 4,398 complex values and two pinned public examples / 141 values passed | [35801843922](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35801843922) |
| Platforms | Results below | [35801843739](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35801843739) |

| Environment | File faults | CLI scenarios | Host groups | Offline browser scenarios |
| --- | --- | --- | --- | --- |
| Linux / Chromium | 6 passed | 24 passed | 14 passed | 30 passed |
| Linux / Firefox | 6 passed | 24 passed | 14 passed | 30 passed |
| Linux / Playwright WebKit | 6 passed | 24 passed | 14 passed | 30 passed |
| Windows / Chromium | 6 passed | 23 passed; POSIX FIFO skipped | 14 passed | 30 passed |

The same suites are repeated across environments. Browser runs used file mode. The Windows source-package reconstruction also passed both external-consumer suites. The numerical implementation, browser interaction code, report schema and existing stdin/output contracts were unchanged.

## Artifacts

The source package, tool package, tool results and all four platform reports were downloaded and inspected. Edited files in the source ZIP matched the locally checked copies. All 11 runtime payload hashes matched the manifest; the downloaded CLI also passed `--help` and `--version` checks.

- Source ZIP SHA256: `e1d42cba8d4d24b274fcb5d26b9da770ab09ef7f0c0c03ece44e79e6e18899a7`.
- Tool artifact `10726735763`, ZIP SHA256: `7acf6d0d8cbc1ade19603f2236af58308f5938cbf4028143ae53f9051f92f1da`.
- Tool results artifact `10725793005`, ZIP SHA256: `93776b10afc66c252dffdeae6419c3f3dd462466fe0cab0cb616075c5ed60fd0`.
- Compiled core SHA256: `af2c3c38071827385902ff84b28f0361a018571bc93878e789b620f902668a71`, unchanged from dev.7.

The runtime manifest identifies the tested PR checkout. This record is a later documentation-only addition. Commands and integration examples are in [CLI.md](../docs/CLI.md) and [LIBRARY.md](../docs/LIBRARY.md).
