# Impedance metadata guard — verified development preview

Date: 2026-09-22. Version: `0.1.0-dev.4`.

Tested implementation: `581eebc71334d02923a75ed89e9e92265d26ed94`.
[PR #2](https://github.com/zhenghao493-netizen/moonbit-sparamkit/pull/2) merged as `99d67457eaca240a47a9cf8780cc9eeb63a31bac` after all three PR workflows succeeded. This documentation-only follow-up does not expand the tested code scope.

## Finding and fix

The dev.3 compiled core accepted an input with header `# Hz S RI R 50` and a later `! Port Impedance 75 0` declaration, reporting `reference_ohms=50`. Its documented policy was to ignore vendor metadata, which still allowed misleading output.

The MoonBit parser now checks recognized standalone `Port Impedance` declarations after the option line. Only same-line real/imaginary pairs for all ports, with real parts exactly equal to header R and zero imaginary parts, are accepted. Conflicts, malformed declarations, complex references and ambiguous placement return positioned `UnsupportedMetadata` diagnostics. The browser clears stale impedance/curves and disables export on this error. No S values are renormalized or modified.

This is a deliberately narrow guard, not general HFSS import. Unknown vendor labels can still remain ordinary comments. Reserved-label prose and unsupported placement may be rejected. See [the compatibility contract](../docs/COMPATIBILITY.md).

## Actual verification results

| Layer | Result |
| --- | --- |
| Core JS | Format, type check, build, 86/86 unit tests and built-in example passed with strict compiler checks |
| Core wasm-gc | Format, type check, build, 86/86 unit tests and built-in example passed with strict compiler checks |
| Source package | 47 files; format/generated API checks; isolated extraction, both target check/build/test runs, bridge build, HTML generation and actual 291-point file CLI passed |
| Synthetic independent comparison | 77 files / 4398 complex values, scikit-rf 1.8.0; maximum absolute complex difference 6.938893903907228e-16 |
| Provenance-locked public examples | 2 unchanged files / 141 complex values; maximum absolute complex difference 5.551115123125783e-17 |
| Node CLI and build protection | 10 scenario groups passed, including JSON/CSV refusal of conflicting metadata |
| Offline Chromium UI | 17 checks passed in actual file:// mode, including new metadata rejection, recovery and 390px layout |

The same 86 unit cases run on both backends; these are not 172 distinct cases. Fourteen cases were added to the dev.3 suite. Error maxima apply only to the recorded corpus, not arbitrary data or measurement accuracy.

Workflow evidence:

- [Core PR run 35743699556](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35743699556)
- [Source package PR run 35743699555](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35743699555)
- [Tool PR run 35743699539](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35743699539)

The actual package-check.json, crosscheck.json, measured-files.json, host-tests.json and browser-tests.json were downloaded and inspected. The isolated package log reports `Total tests: 86, passed: 86, failed: 0.` for both targets. Code, test and configuration files in the downloaded source archive match locally tested files; the compiled core also matches byte-for-byte.

Local official MoonBit execution passed both unit suites, strict checks, host groups and package reconstruction. Local browser file navigation was blocked by environment policy; it is not claimed as a passing local browser test. The actual file-mode browser result above is from GitHub Actions. The JS IIFE build prints a TypeScript-declaration availability notice; this is not a failing compiler diagnostic.

## Artifact identities

- Source ZIP `ttxiangshang-sparamkit-0.1.0-dev.4.zip`: SHA256 `aa9a2a796c72462068b1a75230d5646e67129df82197a51f79020fc4ff6ec8dc`.
- Tool artifact `10700089544`: ZIP SHA256 `caf92043fb27984d151428ea249900b2f0ba5018ff3edf0f625b02126ff81067`.
- Tool evidence artifact `10702220107`: ZIP SHA256 `fc0e7464fe22083f0500a5901325dc6850bc336516c1bcf63cd377417596efae`.
- Package evidence artifact `10701456274`: ZIP SHA256 `7f5356f4b6a8ade0cec882859a237e7c2f623af9f9924da7c4612324871e95f2`.
- Compiled core.cjs: SHA256 `af2c3c38071827385902ff84b28f0361a018571bc93878e789b620f902668a71`.

These hashes identify exact tested artifacts, not later documentation-only rebuilds. Workflow attachments have 30-day retention; source scripts allow rebuilding after expiry. Older Markdown status snapshots in archives are historical; machine-generated logs/JSON and this document identify the new results.

## Direction and remaining limits

The project remains the bounded MoonBit data-processing core plus offline tool described in [DIRECTION_REVIEW.md](../docs/DIRECTION_REVIEW.md). This engineering assessment is not organizer topic approval, a uniqueness guarantee or evidence of external adoption. No Mooncakes publication, Pages deployment, competition form submission or private contact upload was performed.

Priorities remain independent user trials, reproducible delivery and participant confirmation of signup/topic review. Android/iOS hardware, Safari and arbitrary vendor metadata are not validated. The two public examples are upstream-labelled measurements, not measurements collected by this project.
