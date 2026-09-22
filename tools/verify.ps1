$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
if (-not (Get-Command moon -ErrorAction SilentlyContinue)) {
  throw "MoonBit is not installed; no tests have run."
}
moon version --all
if ($LASTEXITCODE -ne 0) { throw "moon version failed" }
moon fmt --check
if ($LASTEXITCODE -ne 0) { throw "moon fmt failed" }
foreach ($target in @("wasm-gc", "js")) {
  moon check --target $target --deny-warn
  if ($LASTEXITCODE -ne 0) { throw "moon check failed for $target" }
  moon build --target $target --deny-warn
  if ($LASTEXITCODE -ne 0) { throw "moon build failed for $target" }
  moon test --target $target --deny-warn
  if ($LASTEXITCODE -ne 0) { throw "moon test failed for $target" }
  moon run cmd/main --target $target --deny-warn
  if ($LASTEXITCODE -ne 0) { throw "demo failed for $target" }
}
