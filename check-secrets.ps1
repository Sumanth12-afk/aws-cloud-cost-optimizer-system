# Simple Security Check for Git Commits
# Run before pushing to GitHub

Write-Host ""
Write-Host "=== Security Pre-Commit Check ===" -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0

# Check 1: Sensitive files
Write-Host "[1] Checking for sensitive files in staging..." -ForegroundColor Yellow
$StagedFiles = git ls-files --cached 2>$null

if ($StagedFiles -match "\.env$") {
    Write-Host "    [FAIL] .env file is staged!" -ForegroundColor Red
    $ErrorCount++
}
if ($StagedFiles -match "terraform\.tfvars$") {
    Write-Host "    [FAIL] terraform.tfvars is staged!" -ForegroundColor Red
    $ErrorCount++
}
if ($StagedFiles -match "\.tfstate") {
    Write-Host "    [FAIL] terraform state file is staged!" -ForegroundColor Red
    $ErrorCount++
}

if ($ErrorCount -eq 0) {
    Write-Host "    [PASS] No sensitive files found" -ForegroundColor Green
}
Write-Host ""

# Check 2: AWS Keys (exclude AWS example keys)
Write-Host "[2] Scanning for AWS access keys..." -ForegroundColor Yellow
$diff = git diff --cached 2>$null
$awsMatches = $diff | Select-String -Pattern "AKIA[0-9A-Z]{16}" | Where-Object { $_.Line -notmatch "AKIAIOSFODNN7EXAMPLE" }
if ($awsMatches) {
    Write-Host "    [FAIL] Real AWS Access Key detected!" -ForegroundColor Red
    $ErrorCount++
} else {
    Write-Host "    [PASS] No real AWS keys found" -ForegroundColor Green
}
Write-Host ""

# Check 3: Slack Webhooks (exclude placeholders with X's)
Write-Host "[3] Scanning for Slack webhook URLs..." -ForegroundColor Yellow
$webhookMatches = $diff | Select-String -Pattern "hooks\.slack\.com/services/T[0-9A-Z]{8}/B[0-9A-Z]{8}" | Where-Object { $_.Line -notmatch "TXXXXXXXX|BXXXXXXXX|XXX" -and $_.Line -notmatch "check-secrets|pre-commit-check" }
if ($webhookMatches) {
    Write-Host "    [FAIL] Real Slack webhook detected!" -ForegroundColor Red
    $ErrorCount++
} else {
    Write-Host "    [PASS] No real webhooks found" -ForegroundColor Green
}
Write-Host ""

# Check 4: .gitignore
Write-Host "[4] Checking .gitignore..." -ForegroundColor Yellow
if (Test-Path ".gitignore") {
    Write-Host "    [PASS] .gitignore exists" -ForegroundColor Green
} else {
    Write-Host "    [FAIL] .gitignore missing!" -ForegroundColor Red
    $ErrorCount++
}
Write-Host ""

# Check 5: .env.example placeholders
Write-Host "[5] Verifying .env.example..." -ForegroundColor Yellow
if (Test-Path ".env.example") {
    $envExample = Get-Content ".env.example" -Raw
    # Check for actual webhook URLs (not placeholders with X's)
    $realWebhook = $envExample | Select-String -Pattern "hooks\.slack\.com/services/T[0-9A-Z]{8}/B[0-9A-Z]{8}/[A-Za-z0-9]{24}" | Where-Object { $_ -notmatch "TXXXXXXXX|BXXXXXXXX|XXX" }
    if ($realWebhook) {
        Write-Host "    [FAIL] Real webhook in .env.example!" -ForegroundColor Red
        $ErrorCount++
    } else {
        Write-Host "    [PASS] Only placeholders found" -ForegroundColor Green
    }
} else {
    Write-Host "    [WARN] .env.example not found" -ForegroundColor Yellow
}
Write-Host ""

# Final Result
Write-Host "==============================" -ForegroundColor Cyan
if ($ErrorCount -gt 0) {
    Write-Host "RESULT: FAILED ($ErrorCount issues)" -ForegroundColor Red
    Write-Host ""
    Write-Host "DO NOT PUSH until issues are fixed!" -ForegroundColor Red
    Write-Host "To unstage files: git rm --cached FILENAME" -ForegroundColor Yellow
    Write-Host ""
    exit 1
} else {
    Write-Host "RESULT: PASSED" -ForegroundColor Green
    Write-Host ""
    Write-Host "Safe to push to public repository!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Reminders:" -ForegroundColor Yellow
    Write-Host "  - Keep .env file private" -ForegroundColor White
    Write-Host "  - Rotate exposed credentials immediately" -ForegroundColor White
    Write-Host "  - See SECURITY.md for guidelines" -ForegroundColor White
    Write-Host ""
}

