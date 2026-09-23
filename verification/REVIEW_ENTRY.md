# Reviewer entry and documentation — 0.1.0-rc.3

Verified 2026-09-23. Implementation: `336d5c904e50af17a3369b3a380972ae8a86b961`; tested PR checkout: `1707a54596fd6c0bed9636b44ad0316175894019`.

[PR #10](https://github.com/zhenghao493-netizen/moonbit-sparamkit/pull/10) merged as `b961b16b6b84b94d794ddcd62f628739fa8bf879`. Comparison with the tested checkout returned no changed files. This record is a later documentation-only addition.

## Changes

The submission bundle now opens at its root `index.html`. The page links to the offline workbench, five-minute demonstration route, source documentation, architecture guide and current reports. Its result table is generated from the bundled reports and core test logs, rather than fixed test counts.

The source ZIP contained a broken relative link from docs/ACCEPTANCE.md to the excluded CI workflow. That link now points to the repository. The new documentation check validates local targets in README/docs and copies the actual README and LIBRARY.md code blocks into fresh workspaces. Both examples are checked, built and run on JS and wasm-gc, including magnitude and CSV output checks. This also runs after source-package extraction.

The architecture guide describes module responsibilities, file-to-result data flow, port indexing, impedance handling, diagnostics, asynchronous state and numeric choices. The MoonBit core, public API and workbench implementation are unchanged.

## Results

Results below were read from the downloaded submission's JSON reports and logs.

| Check | Result |
| --- | --- |
| Core JS / wasm-gc | 104/104 tests per backend |
| Documentation targets | 13 current Markdown documents, 50 local links checked |
| Published code examples | Two examples, each checked/built/run on both backends |
| New reviewer page | Four file-mode checks passed; 14 local targets exist |
| Reviewer navigation | Keyboard activation opens the bundled workbench and its 291-point example |
| Reviewer layout | 390px layout passed; no page exceptions or HTTP(S) requests |
| Existing browser/worker checks | 30 interaction scenarios and eight recovery scenarios passed, plus numeric-browser coverage |
| Source ZIP | 78 files; isolated rebuild and identical repackaged content |
| Unified submission | All 25 command stages passed |
| Downloaded ZIP | Independently extracted; all 138 payload file hashes matched |

All 13 edited source files matched the locally checked copies. A local negative check replaced a README API call with a nonexistent method; compilation correctly rejected it. The original example was then restored and passed. The link check covers inline local targets, not remote URL availability or heading anchors. Local layout inspection used an injected document; actual file-navigation evidence is from CI.

## Runs and artifacts

All five PR workflows passed: [core](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35812809747), [package](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35812809727), [tool](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35812809771), [platforms](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35812809763), and [submission](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35812809697).

Submission artifact `10730022718` contains `SParamKit-0.1.0-rc.3-submission.zip`.

- Submission ZIP SHA256: `5df833a1120e009b388a665eb4634781c5ab1ce8b1cde84e0ed7e828e7fb1555`.
- Source ZIP SHA256: `bc071193b18dcf21140776d24ee43eae9e1d9cff21b9fefa4cf0090374e16705`.
- Compiled core SHA256: `bbca727057836d2a741f57d57cee80b0b3a8a25e52603493f9d4c8ac1f35cc56`, unchanged from rc.2.

After extracting the full bundle, open `SParamKit-0.1.0-rc.3/index.html`. The standalone workbench remains at `workbench/index.html`. The submission artifact has 90-day retention and can be regenerated with `tools/prepare_submission.py`.
