# Include the minus sign in negative constant pattern locations

Fixes #188, confirmed in https://github.com/moonbitlang/parser/issues/188#issuecomment-5809735774.

For a pattern such as `-1`, Handrolled and CST lowering record a span covering only `1`, while MoonYacc covers the complete signed pattern.

This change captures the Handrolled start position before consuming `MINUS`, and uses the complete CST pattern node location when lowering the constant. Literal values and AST field structure are unchanged.

Seven regression tests compare source slices and the full location-aware AST across all three entry points. They cover integer and floating forms, whitespace after the sign, ranges, alternatives, nested constructors, and a positive control.

## Verification

Tested the complete mail patch on `c1174741f8fd5c9b827af7b9148884413e5ebfdd`, independently of #189, using moonc `v0.10.14+7d59c7ec9` / moon `0.1.20260920`.

- New tests compile with `--deny-warn` before the implementation is changed.
- Original implementation: six assertion failures and one passing positive control.
- This patch: the same seven tests pass, as do `moon fmt --check` and `moon check --deny-warn`.
- Full suite: wasm 2845/2845, wasm-gc 2842/2842, JS 2842/2842, native 2847/2847.

[Standalone execution and original logs](https://github.com/zhenghao493-netizen/moonbit-sparamkit/actions/runs/35976306257).

The patch only changes two implementation files and one regression file. It contains no #189 changes, reference snapshot updates, generated-parser edits, or CI modifications.

```bash
moon update
moon fmt --check
moon check --deny-warn
moon test test/manual_test/negative_pattern_loc_test.mbt --target js --deny-warn
moon test --target all
```

Location expectations come from source slices and agreement between the three entry points. `mooninfo` checks syntax eligibility but exports null locations in this toolchain. The maintainer has separately confirmed the issue in the OCaml implementation.
