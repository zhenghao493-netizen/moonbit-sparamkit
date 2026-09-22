# Verification status

## Offline workbench verified — 2026-09-22

Verified code commit: `0b34674c33134c446d16128ccd043305e2e386d8`.
Documentation-only follow-up commits do not expand the code covered by these results.

- [Core workflow run 35732045283](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35732045283): success, both JS and wasm-gc.
- [Tool workflow run 35732045186](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35732045186): success, compiled bridge, Node file CLI, independent numerical comparison, and offline browser tests.
- Both unit verification archives, the runnable tool archive and the tool verification archive were downloaded and inspected. Reported counts below come from their actual logs/JSON, not test-definition counts.

| Target | Check | Build | Tests | Built-in CSV example |
| --- | --- | --- | --- | --- |
| JS | Passed | Passed | 54 passed / 54 total / 0 failed | Passed |
| wasm-gc | Passed | Passed | 54 passed / 54 total / 0 failed | Passed |

All core commands use `--deny-warn`. The same 54 unit cases run on two backends, not 108 independent cases. The bridge IIFE build emitted an informational notice that TypeScript declarations require ESM; the bridge built successfully and its runtime was exercised. GitHub action runtime deprecation notices are separate from MoonBit compiler diagnostics.

### Independent numerical comparison

`tools/crosscheck.py` generated 72 deterministic synthetic cases: 1/2 ports × RI/MA/DB × four frequency units × 25/50/75-ohm reference, with 17 frequencies per file, asymmetric two-port values, comments, scientific notation, CRLF, and continued records. Three existing repository samples and two analytic RC/RLC demonstrations brought the total to 77 files.

Actual result from `crosscheck.json`:

```json
{
  "status": "passed",
  "seed": 20260922,
  "scikit_rf": "1.8.0",
  "numpy": "2.2.6",
  "cases": 77,
  "complex_values": 4398,
  "max_abs_complex_error": 6.938893903907228e-16,
  "relative_tolerance": 1e-10,
  "absolute_tolerance": 1e-12
}
```

The comparison checks frequencies, reference impedance, port indexing, real/imaginary values, magnitudes, dB, phase modulo 360 degrees, and all exported CSV rows against scikit-rf. The reported maximum is complex-value absolute error over this corpus, not a universal error bound. All input files are synthetic; this does not establish hardware measurement accuracy, full standards conformance or arbitrary extreme-number compatibility.

### Offline browser tests

Actual `browser-tests.json`: `status=passed`, `mode=file`, `checks=15`.

Chromium opened the built single HTML using `file://`, running the actual compiled MoonBit core in a Blob worker. Checks covered startup with 291 synthetic two-port points; parameter and axis switching; pagination; full JSON/CSV downloads; invalidation after text edits; undefined zero-magnitude metrics; malformed-input diagnostics; real file-chooser input; oversized/invalid-UTF8 rejection; recovery; 390px responsive layout; and absence of page exceptions or network requests. Desktop and mobile-viewport screenshots are retained in the verification artifact.

Local development also exercised the DOM via an injected local document because the local browser policy blocks direct file and loopback navigation. Those local checks were not presented as a successful local file-navigation test. The cloud run above is the separate actual file-mode confirmation. No Android/iOS hardware or Safari test has been performed.

### Environment and downloadable evidence

```text
moon 0.1.20260920 (914d7da 2026-09-20)
moonc v0.10.14+7d59c7ec9 (2026-09-18)
moonrun 0.1.20260920 (914d7da 2026-09-20)
Node.js 22, Python 3.12, GitHub-hosted Ubuntu
scikit-rf 1.8.0, NumPy 2.2.6, SciPy 1.15.3, Playwright 1.55.0
```

Artifact names: `sparamkit-tool` and `sparamkit-tool-verification` (30-day retention); core `verification-js` and `verification-wasm-gc` (14-day retention). The verification archive contains per-file comparison results, browser scenario results, screenshots and command logs. Its preexisting STATUS.md snapshot describes the earlier stage; the machine-generated JSON and logs are the evidence for this new run, and this repository document supersedes that earlier snapshot.

Compiled `core.cjs` SHA256: `9ad2f8852af8ec3836bfcd54ff669cd5e5c21520bc4fe12cf8c8c3d2ab7759a0`.

Runnable artifact ZIP SHA256: `acdb394aa91d16cafaacd452b7b4835a074fb3cf4671bed25d8ebe1d74505622`.

Tool verification ZIP SHA256: `fe4b30588d5bfdda28372bc13546cc083e205af53a280728431af3a57189236c`.

## Development trace

1. `b7e3104`: imported core and 46 tests; cloud install succeeded, but test literal syntax needed fixes.
2. `e78cb09`: corrected literals and migrated debugging; 46 tests passed with remaining method-promotion warnings.
3. `133f6be`: explicit Debug extensions, `--deny-warn`, both backends passed 46 tests.
4. `4d2b1d2`: added shared checked JSON/CSV reports, eight tests and an actual MoonBit-compiled host bridge.
5. `0b34674`: offline workbench, Node file CLI, synthetic circuit demonstrations and independent numerical/browser CI.

## Remaining scope

- Representative measured instrument data and a full documented conformance matrix.
- Formatting gate, package/archive verification and Mooncakes publication.
- Windows execution, mobile hardware and broader browser compatibility.
- Organizer topic clearance and competition registration.

No GitHub Pages deployment or remote data service has been configured.
