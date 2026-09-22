#!/usr/bin/env bash
# Validate the project, retaining all target logs even if one target fails.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2
mkdir -p verification
: > verification/summary.tsv
printf 'step\texit_code\n' >> verification/summary.tsv
if ! command -v moon >/dev/null 2>&1; then
  printf '%s\n' 'BLOCKED: MoonBit executable is not installed. No MoonBit test was run.' | tee verification/environment.log >&2
  printf 'environment\t2\n' >> verification/summary.tsv
  exit 2
fi
case "${1:-all}" in
  all) targets=(wasm-gc js) ;;
  wasm-gc|js) targets=("$1") ;;
  *) printf '%s\n' 'Usage: bash tools/verify.sh [all|wasm-gc|js]' >&2; exit 2 ;;
esac
failed=0
run_check() {
  local label="$1"
  shift
  printf '\n=== %s ===\n' "$label"
  "$@" 2>&1 | tee "verification/$label.log"
  local code=${PIPESTATUS[0]}
  printf '%s\t%s\n' "$label" "$code" >> verification/summary.tsv
  if [[ "$code" -ne 0 ]]; then failed=1; fi
}
printf 'UTC %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" | tee verification/environment.log
run_check version moon version --all
run_check format moon fmt --check
for target in "${targets[@]}"; do
  run_check "check-$target" moon check --target "$target" --deny-warn
  run_check "build-$target" moon build --target "$target" --deny-warn
  run_check "test-$target" moon test --target "$target" --deny-warn
  run_check "demo-$target" moon run cmd/main --target "$target" --deny-warn
done
if [[ "$failed" -ne 0 ]]; then
  printf '%s\n' 'FAILED: at least one check failed. Inspect verification/summary.tsv.'
else
  printf '%s\n' 'All requested commands returned exit code 0. Inspect the test logs for counts.'
fi
exit "$failed"
