# Include the minus sign in negative constant pattern locations

Fixes #188, confirmed in https://github.com/moonbitlang/parser/issues/188#issuecomment-5809735774.

For a pattern such as `-1`, Handrolled and CST lowering currently record a span covering only `1`. MoonYacc covers the complete signed pattern.

This change captures the Handrolled start position before consuming `MINUS`, and uses the complete CST pattern node location when lowering the constant. Literal values and AST field structure are unchanged.

Seven regression tests compare source slices and the full location-aware AST across all three entry points. They cover integer and floating forms, whitespace after the sign, ranges, alternatives, nested constructors, and a positive control. Against the unmodified base, six assertions fail and the positive control passes; with the patch, all seven pass.

The patch is limited to two implementation files and one regression file. It contains no #189 changes, reference snapshot updates, generated-parser edits, or CI modifications.

## Reproduction

Base: `c1174741f8fd5c9b827af7b9148884413e5ebfdd`.
Toolchain: `moonc v0.10.14+7d59c7ec9` / `moon 0.1.20260920`.

```bash
moon update
moon fmt --check
moon check --deny-warn
moon test test/manual_test/negative_pattern_loc_test.mbt --target js --deny-warn
moon test --target all
```

The focused tests use source slices and agreement between the three entry points for locations; `mooninfo` validates syntax eligibility but does not provide location values in this toolchain. The maintainer has separately confirmed the issue in the OCaml implementation.

Standalone full-suite execution is recorded by https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35976306257. Its results must be read from the completed run before posting this description as a PR.
