# Compatibility and packaging verification

Development preview `0.1.0-dev.3`, verified 2026-09-22. This supersedes the remaining-work list of the historical offline-workbench snapshot in STATUS.md where explicitly stated below.

## Verified and merged code

Reviewed code: `18c9fffbc47b067625789e420022e116d3a419f2`.
[PR #1](https://github.com/zhenghao493-netizen/moonbit-sparamkit/pull/1) merged as `da2b975d1e9afde9f8fd312eb3ab69c42b27ff10` after the PR workflows succeeded. This documentation-only follow-up does not change the tested implementation.

| Verification layer | Actual result and evidence |
| --- | --- |
| Core JS / wasm-gc | Formatting, type check, build, 72/72 tests per target and built-in example; --deny-warn; [PR run 35740478225](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35740478225) |
| Fresh source package | 44 files; generated API and format checks; isolated extraction, both target checks/builds/tests (72/72 each), bridge, HTML and 291-point file CLI rebuilt; [push run 35740424489](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35740424489), [PR run 35740478544](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35740478544) |
| Synthetic scikit-rf comparison | 77 files / 4398 complex values; maximum absolute complex difference 6.938893903907228e-16 |
| Provenance-locked public examples | 2 files / 141 complex values; maximum absolute complex difference 5.551115123125783e-17 |
| Node CLI and build protection | 8 scenario groups passed, including 7 error-path cases in one group |
| Chromium offline UI | 16 checks passed in actual file:// mode, including BOM and pure-CR file input and 390px viewport |

The last four rows are from [tool PR run 35740478157](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35740478157). Its actual JSON/log artifact was downloaded and inspected, as was the push package-verification artifact. The archived core source files were compared to the locally tested files with no differences. The same 72 unit cases run on both backends, not 144 distinct tests. Repeated successful workflows are not extra independent test cases.

## Public example results

The two files remain unchanged inside the pinned scikit-rf 1.8.0 test dependency; they are not copied into this repository or its offline app. Git blob identities are checked before numerical comparison. The reference implementation also confirms every frequency/port uses real 50-ohm impedance with zero imaginary part.

| File | Samples / ports | Complex values | Maximum absolute complex difference |
| --- | --- | --- | --- |
| ring slot measured.s1p | 101 / 1 | 101 | 0 |
| ind.s2p | 10 / 2 | 40 | 5.551115123125783e-17 |

SHA256:

- ring slot measured.s1p: `d916949bdcce147e2d246d9674469042f35bc7b79a3e0683b64b5bf9aad20f4d`
- ind.s2p: `b0fba0a8ee8dda4f470f1e45d0481434e7fa07447e68156c9ee3e8e2db44bac3`

“Measured” is the upstream author's classification, not a new measurement collected by this project. The inductor file contains an SP1.SP export header; acquisition hardware and uncertainty were not independently established. See [TEST_DATA.md](../docs/TEST_DATA.md). These comparisons test public-file compatibility, not instrument accuracy or universal standards compliance. Error maxima apply only to their recorded datasets.

## Package and runtime evidence

- Source ZIP: `ttxiangshang-sparamkit-0.1.0-dev.3.zip`, produced by the push package run above; SHA256 `a7bd95c67648ec902b28abaae69c157dbc5d224ae150eeb969a5cf58e32b932b`.
- Offline tool artifact: `sparamkit-tool`, ID `10699463155`, from tool PR run above; ZIP SHA256 `306598f959f7e0f0051e9fa0281756b870030749c00c86dd2510942570791b28`.
- Tool evidence artifact: `sparamkit-tool-verification`, ID `10698713493`; ZIP SHA256 `df073ccc0dea3005edf0dbb9d85791bdb8dde04cd4e8610d7605ba7ab0abcc9d`.
- Compiled `core.cjs` SHA256: `163ec39fbfdea0084c39eb49bc3011f91d1040f85abeef6d7714905fae4078d7`.

Checksums identify those exact archives; later documentation-only builds can produce different source ZIP hashes. Downloaded archives were checked against the values above. Tool/source/evidence artifacts retain 30 days; source scripts allow rebuilding after expiry. The evidence archive may contain an earlier Markdown status snapshot; its machine-generated JSON/logs and this document provide the updated results.

Source-package checks reject unsafe paths, duplicates, unexpected symlinks, build/cache directories, generated logs and credential-like filenames; required source/API/docs/assets and license are checked. This is a packaging hygiene check, not a comprehensive secret scanner. A freshly extracted package is compiled and exercised rather than merely listed. No `moon publish` was run.

## Changes and development trace

- Added 18 regression tests covering pure/mixed line endings, initial/embedded/repeated BOM, physical source columns, 24 option-category permutations, eight two-port continuation positions, signed zero and resource limits.
- Added compatibility matrix with explicit stricter policies and encoding/continuation extensions; do not describe it as complete format certification.
- Builder fails when the expected compiled bridge is absent rather than reusing old dist/core.cjs.
- Official formatting and generated interfaces were applied. Initial standalone formatting gates on unformatted commit `60074ea5ad663bad75b100c46d757000c101a992` failed as intended, and the failure remains in history. Normalization commit `46fe7a79f014eb5b1daab0d48454e407a52748c1` was checked before the final cleaned review commit above.
- The temporary write-enabled setup/normalization workflow was removed before merge. Permanent verification workflows are read-only.

## Environment and remaining scope

Official toolchain: moon 0.1.20260920, moonc v0.10.14+7d59c7ec9; GitHub-hosted Ubuntu, Node.js 22, Python 3.12; scikit-rf 1.8.0, NumPy 2.2.6, SciPy 1.15.3, Playwright 1.55.0.

The same official toolchain was also executed locally for 72/72 JS and wasm-gc tests, format checking, fresh-package reconstruction and eight host groups. Local browser file navigation is blocked by environment policy; successful actual file-mode browser tests are from the cloud, not that local attempt.

Still not covered: arbitrary vendor impedance comments, full Touchstone 2.0/noise/multiport formats, physical Android/iOS and Safari, Windows execution, instrument-wide compatibility or measurement certification. No Mooncakes publication, GitHub Pages deployment, organizer clearance or competition registration is claimed. Public documents contain no private contact data.
