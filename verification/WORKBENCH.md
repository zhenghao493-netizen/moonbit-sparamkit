# Workbench readouts — 0.1.0-dev.6

Implementation: `9c327df8809c0249659bbe40c4123da8c4196a6b`.
Tested PR checkout: `fbd1daee90b35c20fa33b88eb40cc58612e0be86`.
[PR #4](https://github.com/zhenghao493-netizen/moonbit-sparamkit/pull/4) merged as `dfaf0ce97433b4f9a7f4b523124576171f068018`; the comparison with the tested checkout returned no changed files.

## Changes

The workbench now shows frequency, real/imaginary components, magnitude, dB and phase for a selected original sample. Pointer selection follows the displayed linear or logarithmic axis. A native slider supports keyboard navigation; switching S parameters preserves the selected frequency, and clicking the plot reveals its table page.

A diagnostic button selects the corresponding field in the source editor. BOM, CR line endings and Unicode comments are covered by the browser test. Changing the input clears the old selection and diagnostic.

Parameter values are cached. Moving the readout and paging the table update only the small readout/cursor/table elements, rather than recreating the full plot paths. The test checks that the existing curve DOM node is retained.

## CI results

| Check | Result | Run |
| --- | --- | --- |
| Core JS / wasm-gc | 86/86 tests per target; format, check, build and example passed | [35754163818](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35754163818) |
| Source archive | 52 files; fresh extraction, both target suites, bridge, workbench and CLI rebuilt | [35754163684](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35754163684) |
| Numerical and host regression | 77 synthetic files / 4,398 complex values; two pinned public files / 141 values; 14 host groups passed | [35754163816](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35754163816) |
| Platform matrix | 30 offline browser scenarios and 14 host groups passed in each environment below | [35754163673](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35754163673) |

Actual browser versions from the downloaded reports: Linux Chromium 152.0.7977.0, Firefox 141.0, Playwright WebKit 26.0; Windows Chromium 140.0.7339.16. Each ran the same 30 scenarios using file://, including 390px layout, errors, exports and asynchronous state changes. WebKit coverage is not a Safari hardware test.

Eight scenarios were added to the previous 22-case browser suite. The new large-file cases import 20,000 two-port samples, select the final point, check complete JSON output and all 80,000 CSV parameter rows, then verify that a 20,001-point input is rejected with SampleLimit. Readout values are compared with the MoonBit JSON report. These are deterministic test inputs, not measurements of general performance.

The MoonBit numerical implementation and its 86-case suite are unchanged. The compiled core is byte-identical to dev.5. Local core/host/package checks and injected-document Chromium tests also passed; the file-mode results above come from CI.

## Artifacts

Downloaded package, tool and four platform report archives were inspected. All edited code/test files in the source archive match the locally checked files. All 11 payload files in the tool manifest matched their SHA256 entries.

- Source ZIP: `ttxiangshang-sparamkit-0.1.0-dev.6.zip`; SHA256 `0949152da1f665cc7dba67482c8acd1d8d41718f49b28f462191ce873e3e360e`.
- Tool artifact: `10706039266`; ZIP SHA256 `6374ed85589fdce38700c788bbe028d4af0295590fcd1b6908f05c4c4fd1b331`.
- Tool report artifact: `10706024254`; ZIP SHA256 `094380cc78b40375f2ad434f700508f45c430d282a420bfcb9e383ea1075893f`.
- Core SHA256: `af2c3c38071827385902ff84b28f0361a018571bc93878e789b620f902668a71`.

The artifact manifest identifies the tested PR checkout. This verification note is a later documentation-only addition. Usage is described in [WORKBENCH.md](../docs/WORKBENCH.md); format support remains as documented in [COMPATIBILITY.md](../docs/COMPATIBILITY.md).
