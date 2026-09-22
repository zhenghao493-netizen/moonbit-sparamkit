# Cross-platform delivery — development preview 0.1.0-dev.5

Verified 2026-09-22. Reviewed implementation: `d88ea1fefe1d94ebbedf260bcc1b59f67621d0c9`. PR checkout: `97ce117fbc0df97ba23980ec7305948491e0bae1`. [PR #3](https://github.com/zhenghao493-netizen/moonbit-sparamkit/pull/3) was merged as `8809a198ae41c1a2cf09cc2f84af41f32d02d1b9` after all four PR workflows succeeded. GitHub's comparison returned no changed files between tested PR checkout and merge. Later documentation-only commits do not expand this tested implementation.

## Changes

The MoonBit parser, numerical implementation and its 86 unit cases were unchanged. This iteration addresses delivery and host behaviour within the submitted scope:

- Clear the file chooser after selecting a file so that the same file can be selected again after edits.
- Allow only the current input generation to unlock the analysis button. An older request completing must not make a newer, pending analysis appear finished.
- Disable duplicate CSV requests while an export is pending; discard its output when input changes. Clear stale plot explanatory text when invalidating results.
- Use explicit UTF-8 reads/writes for the HTML builder and UTF-8 decoding in host integration tests, with LF checkout policy.
- Include version/build identification, manifest.json and verify_download.py in the runnable package. The manifest records SHA256 for all 11 delivered payload files; it is not a digital signature or an authenticity guarantee.

## Actual cloud results

[Cross-platform run 35748629478](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35748629478) completed successfully. All four platform evidence archives were downloaded; their actual browser-tests.json, host-tests.json and encoding/toolchain logs were inspected.

| Platform / actual engine | Offline browser scenarios | Host/integrity groups |
| --- | --- | --- |
| Linux / Chromium 152.0.7977.0 | 22 passed, file mode | 14 passed |
| Linux / Playwright Firefox 141.0 | 22 passed, file mode | 14 passed |
| Linux / Playwright WebKit 26.0 | 22 passed, file mode | 14 passed |
| Windows / Chromium 140.0.7339.16 | 22 passed, file mode | 14 passed |

Linux Chromium used the runner-provided executable selected by the test helper; the other reported versions likewise come from actual browser.version values. Playwright 1.55.0 drives these tests. These are repeated executions of the same 22 browser scenarios and 14 host groups, not 88 or 56 distinct tests. Each browser run includes 390px layout and checks for no page exceptions or HTTP(S) requests.

The asynchronous scenarios temporarily hold and reorder worker transport. They do not substitute fake parsed values: every released request still runs the actual compiled MoonBit core. They cover older completion during a newer pending request, out-of-order completion, and discard of pending CSV after text edits. Additional coverage includes same-file reselection and Unicode drag/drop/download filenames.

### Windows and package reconstruction

The Windows runner logged `default encoding: cp1252 UTF8 mode: 0`. PowerShell tools/verify.ps1 succeeded. The actual package-check.json reports 49 source files and successful isolated extraction/rebuild, with logs explicitly reporting `Total tests: 86, passed: 86, failed: 0.` for both JS and wasm-gc. Chinese/spaced paths and Chinese error messages round-trip correctly in the host tests. This is a hosted Windows test, not the user's personal computer.

[Core run 35748629480](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35748629480) and [Linux source-package run 35748629490](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35748629490) also succeeded. Source-package verification checks formatting, generated interfaces, archive paths and a fresh reconstruction. The unchanged 86-case suite is not counted again as newly added cases.

### Numerical regression and usable artifact

[Tool run 35748629493](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35748629493) passed. Its downloaded JSON evidence records:

- scikit-rf 1.8.0: 77 synthetic files / 4398 complex values; maximum absolute complex difference 6.938893903907228e-16.
- Two provenance-locked public examples / 141 complex values; maximum absolute complex difference 5.551115123125783e-17.
- 14 host/integrity groups and 22 actual file-mode Chromium scenarios.

The synthetic corpus and public examples are the existing corpora, not new laboratory measurements. Differences only describe the tested values, not universal error bounds or instrument accuracy. See TEST_DATA.md and previous verification records for provenance and limits.

All edited runtime and test files in the downloaded source package match the locally checked copies byte-for-byte. The runnable package's manifest was also independently rechecked after download: all 11 listed files matched. Windows and Linux source ZIPs can have different archive hashes; no cross-platform byte-identical ZIP claim is made.

## Exact delivered identities

- Linux source ZIP `ttxiangshang-sparamkit-0.1.0-dev.5.zip`: SHA256 `d3d8e0b753d5729c4a0ef9525507d02bcfad1bb15c0ae7c56e6833486a85b960`.
- Tool artifact ID `10704008250`: ZIP SHA256 `987be896edeba171162059023c0c6e5135d7f4965da4765251d4a4d4d3f91dbe`.
- Compiled core.cjs: SHA256 `af2c3c38071827385902ff84b28f0361a018571bc93878e789b620f902668a71`, unchanged from dev.4.
- Tool evidence artifact ID `10704118076`: ZIP SHA256 `4b50fb048e5d69e4a314306f7557fc777a419024338f6defd3244a8e79344a8f`.
- Platform artifact IDs: Windows `10703868151`; Linux Chromium `10703928387`; Firefox `10704152876`; WebKit `10703758254`.

Artifact retention is 30 days. The bundled manifest intentionally contains the tested PR checkout SHA rather than a later merge or documentation SHA. Those commits have the same tested implementation. Earlier Markdown snapshots in evidence archives remain historical; actual JSON/logs and this record identify this iteration.

## Remaining boundaries

No Mooncakes publication, GitHub Pages deployment or private application contact upload was performed. No external human user trial, Android/iOS physical-device run, macOS or branded Safari validation is claimed. Playwright WebKit is not Safari (see the official Playwright browser documentation). Tests run with controlled synthetic/public examples and do not certify arbitrary instruments, vendor formats or metrology accuracy. The submitted one/two-port scope is unchanged.
