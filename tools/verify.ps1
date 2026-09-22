$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
if (-not (Get-Command moon -ErrorAction SilentlyContinue)) {
  throw "MoonBit is not installed; no tests have run."
}
moon version --all
if ($LASTEXITCODE -ne 0) { throw "moon version failed" }
foreach ($target in @("wasm-gc", "js")) {
  moon check --target $target
  if ($LASTEXITCODE -ne 0) { throw "moon check failed for $target" }
  moon test --target $target
  if ($LASTEXITCODE -ne 0) { throw "moon test failed for $target" }
}
moon run cmd/main --target js
if ($LASTEXITCODE -ne 0) { throw "demo failed" }
