param(
  [string]$TestsPath = "backend/tests"
)

# Set required env var for tests
$env:EMAIL_VERIFICATION_REQUIRED = "true"
Write-Host "EMAIL_VERIFICATION_REQUIRED=$env:EMAIL_VERIFICATION_REQUIRED"

# Run pytest
python -m pytest $TestsPath -q
