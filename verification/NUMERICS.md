# Numeric boundaries — 0.1.0-dev.9

Verified 2026-09-23. Implementation: `73ab2904de6abca25206543c7303548aa0dbbc54`.
Tested PR checkout: `73ad43ac060e175ea67ddf477d277f45be4c920c`.
[PR #7](https://github.com/zhenghao493-netizen/moonbit-sparamkit/pull/7) merged as `77167d4661c5e65b0f6bb17a1b91e4e15031bc76`; comparison with the tested checkout returned no changed files.

## Fix

The previous dB implementation took a logarithm of an already rounded linear magnitude. This lost about 3.0103 dB when both components were the minimum positive binary64 value, and returned null when finite components produced an overflowing linear magnitude.

The revised calculation uses scaled components and logarithms, without constructing that intermediate magnitude. Zero and nonfinite components retain their existing optional-value behaviour. JSON can now retain a finite dB value even when the linear magnitude is represented as null. CSV still exports the original parsed real/imaginary components. Public API signatures, report fields and parsing syntax are unchanged; the formula is documented in [NUMERICS.md](../docs/NUMERICS.md).

| Input components | Previous dB | Corrected dB, rounded |
| --- | --- | --- |
| `1.7e308`, `1.7e308` | null | 6167.619278384205 |
| `5e-324`, `5e-324` | -6466.124306862316 | -6463.114006905676 |

These are numerical stress inputs, not measured RF data. Before the change, six of the eight new unit tests failed. The corrected reference harness recorded 68 failed checks across repeated layouts and backends before the fix and zero afterward.

The branch also retains the file-I/O safeguards, six fault scenarios and ten public-API tests from PR #6, which landed during development. Those changes are recorded separately in [FILE_IO.md](FILE_IO.md).

## Reference calculation

`tools/test_numeric.py` uses 1,024 finite-component pairs: fixed boundary cases plus deterministic random binary64 values (seed 20260923). The same pairs appear in one-port and two-port files and run on both JS and wasm-gc.

Python Decimal uses 100-digit precision to calculate `10 * log10(re² + im²)` from the exact binary64 component values. The reference does not reuse the production scaled-log formula. Checks also cover magnitude, phase, frequency/port indexing, raw-component JSON/CSV round trips, and agreement between the compiled CLI and the current source.

Both backends passed with a maximum absolute dB difference of **9.094947017729282e-13**, below the **1e-10 dB** test tolerance. Each backend checks 2,048 parameter occurrences across the two layouts; these are repetitions of the 1,024 input pairs. The reported maximum applies to this corpus.

## CI results

All four PR workflows completed successfully:

| Layer | Result | Workflow |
| --- | --- | --- |
| Core | 104/104 tests per backend, including ten public-API tests; format, strict checks, build and example passed | [35802740631](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35802740631) |
| Source archive | 65 files; fresh reconstruction, both core suites, both five-case external consumers, CLI, file-fault and numeric checks passed | [35802740576](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35802740576) |
| Tool | Decimal reference, scikit-rf/public-file comparisons, host/CLI/fault tests and browser checks passed | [35802740697](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35802740697) |
| Platforms | Linux Chromium, Firefox, Playwright WebKit and Windows Chromium passed the 30 existing file-mode scenarios plus the new numeric readout/export scenario | [35802740664](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35802740664) |

Existing regressions passed again: 77 synthetic files / 4,398 complex values, two pinned public examples / 141 values, 14 host groups and six file-fault scenarios. CLI tests passed 24 scenarios on Linux and 23 on Windows, with the POSIX FIFO scenario explicitly skipped on Windows. Windows source-package reconstruction also passed both numeric targets and both external-consumer suites.

The focused browser scenario checks overflow, subnormal and zero-value readouts, finite plot coordinates, and matching JSON/CSV downloads. All four environments used file mode. Actual reported engine versions: Linux Chromium 152.0.7977.0, Firefox 141.0, Playwright WebKit 26.0; Windows Chromium 140.0.7339.16. This does not add a physical-device Safari test.

## Artifact checks

Source, package, tool and four platform report archives were downloaded and inspected. Edited implementation and test files matched the locally checked copies. All 11 runtime payload hashes matched the manifest. The downloaded CLI also passed a direct stdin check of the large, subnormal and zero examples above.

- Source ZIP `ttxiangshang-sparamkit-0.1.0-dev.9.zip`: SHA256 `15937451d9fd352923190e7d19e21345e7b6668bd9afb527e98e6180fee34ec0`.
- Tool artifact `10726393076`: ZIP SHA256 `7f59140e863e7839a0e046cd3670ceccc85af2ac81bf5b99bef780139e443d63`.
- Tool report artifact `10726727535`: ZIP SHA256 `34e35e7dad4defe0e61d58aa3635fa6c4ca783882af3c6dedf22bc72512c1d21`.
- Compiled core SHA256: `bbca727057836d2a741f57d57cee80b0b3a8a25e52603493f9d4c8ac1f35cc56`.

The manifest identifies the tested PR checkout. This record is a later documentation-only addition; source-package hashes identify the exact archived version above.
