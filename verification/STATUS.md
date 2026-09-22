# Verification status

Initial import, 2026-09-22: the previous local environment had no MoonBit executable; toolchain download failed at DNS resolution. No local MoonBit test result is claimed.

The repository now contains a workflow that runs real `moon check`, `moon build`, `moon test`, and the example for JS and wasm-gc. Inspect the Actions run for the exact commit. A queued workflow or source test count does not demonstrate success.

Generated logs and `summary.tsv` are uploaded as Actions artifacts, not treated as source. External scikit-rf comparison is still pending.
