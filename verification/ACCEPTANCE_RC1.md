# Acceptance bundle — 0.1.0-rc.1

Verified 2026-09-23. Implementation: `36e33ac7b45923ed041dcf5d583268cbbe768f72`; tested PR checkout: `8b160fff7229ce091e67ca51a4e8596ea2d0e987`.

[PR #8](https://github.com/zhenghao493-netizen/moonbit-sparamkit/pull/8) merged as `ecdc5f06091ecc71f7e8b1258e7903b5225a4b57`. Comparison with the tested checkout returned no changed files. This record is a documentation-only follow-up.

## Delivery

The candidate keeps the submitted one/two-port Touchstone scope and existing MoonBit API and numerical implementation. It adds a feature-to-code/test checklist, a five-minute demonstration route and `tools/prepare_submission.py`.

The script runs 22 command stages, then creates one ZIP containing the offline workbench, independently rebuildable source, current test reports, command logs and screenshots. A failed stage removes the candidate output rather than leaving an old successful ZIP. The submission workflow retains its artifact for 90 days.

The runtime builder now refuses unrelated files, directories and symlinks in `dist/` without deleting local results. Ten regression scenarios cover contaminated output and recovery. Source packages retain their ignore policies; after testing an isolated extraction, the package check creates another archive and compares every member path and byte.

## Fresh submission results

All results below were read from the downloaded submission, not inferred from test definitions.

| Check | Result |
| --- | --- |
| MoonBit JS / wasm-gc | 104/104 tests per backend; format, check, build and example passed |
| Independent consumer | Five public API cases per backend passed |
| CLI | 24 checks passed on the submission's Linux runner |
| File-I/O faults | Six checks passed |
| Runtime packaging | Ten checks passed, no skips |
| Host and integrity | 14 groups passed |
| Numerical boundaries | 100-digit Decimal reference comparison passed on both backends |
| scikit-rf synthetic corpus | 77 files / 4,398 complex values passed |
| Pinned public files | Two files / 141 complex values passed |
| Browser | 30 file-mode scenarios plus the numeric-browser scenario passed |
| Source archive | 72 files; isolated rebuild passed; repackaged source paths and bytes matched |
| Delivered ZIP | Extracted and independently verified: all 123 payload file hashes matched |

The backend runs use the same test cases. The original synthetic and public corpora are retained; this iteration did not collect additional laboratory measurements. Platform-specific coverage remains recorded by the separate platform workflow.

## Workflow runs

All five PR workflows completed successfully:

- [Core: 35804947635](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35804947635)
- [Source package: 35804947624](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35804947624)
- [Tool: 35804947664](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35804947664)
- [Cross-platform: 35804947675](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35804947675)
- [Submission: 35804947667](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35804947667)

## Artifact identities

Submission artifact `10726494695` contains `SParamKit-0.1.0-rc.1-submission.zip`.

- Inner submission ZIP SHA256: `9b7a1e75f9768e1734eca59ce7044e26280c1ba229c9a5a23612ef135ede6427`.
- Source ZIP SHA256: `9ffec2c3f097386c5330bf9897e342e4ea7fb325a56e8ef4ac3a1e6d846970a1`.
- Compiled core SHA256: `bbca727057836d2a741f57d57cee80b0b3a8a25e52603493f9d4c8ac1f35cc56`.

Every source file in the downloaded archive matched the reviewed working copy. The manifests identify the tested PR checkout, not this later documentation commit. Rebuilds after documentation changes will have different source and submission hashes.

Open `workbench/index.html` after extracting the submission ZIP. The feature checklist is in `source/docs/SUBMISSION.md`, reproduction commands in `source/docs/ACCEPTANCE.md`, and this run's evidence in `reports/`.

The candidate is ready for the documented demonstration and technical review. Mooncakes publication and organizer assessment are separate; format support remains in [COMPATIBILITY.md](../docs/COMPATIBILITY.md).
