# Verification status

## Verified core — 2026-09-22

- Code commit: `133f6be4bc97710862253473c47a7e811a0297de`.
- [GitHub Actions run 35729074198](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35729074198), workflow `Verify SParamKit`, run number 3.
- Run started at 2026-09-22T12:45:02Z and completed successfully at 2026-09-22T12:45:22Z.
- Both job logs were read, including actual test summaries and example output.

| Target | Type check | Build | Tests | Built-in CSV example |
| --- | --- | --- | --- | --- |
| JS | Passed | Passed | 46 passed / 46 total / 0 failed | Passed |
| wasm-gc | Passed | Passed | 46 passed / 46 total / 0 failed | Passed |

All four MoonBit commands ran with `--deny-warn`; no MoonBit compiler warnings remained. These are the same 46 test cases executed on two backends, not 92 distinct cases. GitHub's action runtime did emit separate Node.js deprecation notices; those are not MoonBit compiler diagnostics.

### Environment

```text
moon 0.1.20260920 (914d7da 2026-09-20)
moonc v0.10.14+7d59c7ec9 (2026-09-18)
moonrun 0.1.20260920 (914d7da 2026-09-20)
Node.js v22.23.2
Ubuntu 24.04.5 GitHub-hosted runner
```

[JS job 106749848384](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35729074198/job/106749848384) reported `Total tests: 46, passed: 46, failed: 0.`

[wasm-gc job 106749848338](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35729074198/job/106749848338) reported `Total tests: 46, passed: 46, failed: 0.`

Per-command logs and `summary.tsv` were uploaded as `verification-js` and `verification-wasm-gc` artifacts, retained for 14 days by workflow configuration.

## Development trace

1. `b7e3104`: first source import; cloud toolchain installation succeeded. Library/demo built, but three test numeric literals produced parsing errors. No successful test result is claimed for this commit.
2. `e78cb09`: corrected numeric literal syntax and migrated diagnostic derivation from Show to Debug; both backends passed 46 tests, with remaining Debug method-promotion warnings.
3. `133f6be`: made Debug extensions explicit and enabled `--deny-warn`; both backends passed all checks again.

These results are from remote GitHub Actions. Earlier local execution was blocked because MoonBit was absent and the installer host failed DNS resolution; that local failure is not described as a passing local test.

## Not yet verified or implemented

- Independent scikit-rf cross-checks and representative measured instrument data.
- Full Touchstone conformance; the library intentionally supports only its documented strict subset.
- Formatting gate, package/archive verification, or Mooncakes publication.
- A file-input CLI and a browser visualization calling the MoonBit core.
- Windows execution of the supplied PowerShell helper.
- Organizer topic clearance or competition registration.

A successful unit-test run does not establish the above claims. Follow-up documentation-only commits do not expand the tested code scope.
