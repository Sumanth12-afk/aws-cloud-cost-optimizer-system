# Pre-commit security check script for Windows
# Run this before pushing to GitHub

Write-Host "🔍 Running security pre-commit checks..." -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0

# Check if sensitive files are staged
Write-Host "1️⃣ Checking for sensitive files..." -ForegroundColor Yellow
$SensitivePatterns = @(".env", "terraform.tfvars", "*.pem", "*.key", "terraform.tfstate")
$StagedFiles = git ls-files --cached

foreach ($pattern in $SensitivePatterns) {
    $matches = $StagedFiles | Where-Object { $_ -like $pattern }
    if ($matches) {
        Write-Host "❌ FOUND: $pattern is staged for commit!" -ForegroundColor Red
        $ErrorCount++
    }
}

if ($ErrorCount -eq 0) {
    Write-Host "✅ No sensitive files staged" -ForegroundColor Green
}
Write-Host ""

# Check for AWS keys in staged changes
Write-Host "2️⃣ Scanning for AWS access keys..." -ForegroundColor Yellow
$diff = git diff --cached
if ($diff -match "AKIA[0-9A-Z]{16}") {
    Write-Host "❌ AWS Access Key detected in staged changes!" -ForegroundColor Red
    $ErrorCount++
} else {
    Write-Host "✅ No AWS keys found" -ForegroundColor Green
}
Write-Host ""

# Check for Slack webhooks
Write-Host "3️⃣ Scanning for Slack webhook URLs..." -ForegroundColor Yellow
if ($diff -match "hooks\.slack\.com/services/T[0-9A-Z]{8}/B[0-9A-Z]{8}") {
    Write-Host "❌ Real Slack webhook URL detected!" -ForegroundColor Red
    Write-Host "   Only placeholders like TXXXXXXXX should be committed" -ForegroundColor Yellow
    $ErrorCount++
} else {
    Write-Host "✅ No real webhook URLs found" -ForegroundColor Green
}
Write-Host ""

# Verify .gitignore exists
Write-Host "4️⃣ Checking .gitignore..." -ForegroundColor Yellow
if (-not (Test-Path ".gitignore")) {
    Write-Host "❌ .gitignore file missing!" -ForegroundColor Red
    $ErrorCount++
} else {
    Write-Host "✅ .gitignore present" -ForegroundColor Green
}
Write-Host ""

# Check if .env.example has placeholders only
Write-Host "5️⃣ Verifying .env.example has placeholders..." -ForegroundColor Yellow
if (Test-Path ".env.example") {
    $envExample = Get-Content ".env.example" -Raw
    if ($envExample -match "T09S89P2WD6") {
        Write-Host "❌ Real webhook URL found in .env.example!" -ForegroundColor Red
        $ErrorCount++
    } elseif ($envExample -match "AKIA[0-9A-Z]" -and $envExample -notmatch "AKIAIOSFODNN7EXAMPLE") {
        Write-Host "❌ Real AWS key found in .env.example!" -ForegroundColor Red
        $ErrorCount++
    } else {
        Write-Host "✅ .env.example contains placeholders only" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️ .env.example not found" -ForegroundColor Yellow
}
Write-Host ""

# Final result
if ($ErrorCount -gt 0) {
    Write-Host "[FAIL] Security checks FAILED! Found $ErrorCount issues" -ForegroundColor Red
    Write-Host ""
    Write-Host "[WARNING] DO NOT COMMIT until all issues are resolved!" -ForegroundColor Red
    Write-Host ""
    Write-Host "To remove sensitive files from staging:" -ForegroundColor Yellow
    Write-Host "  git rm --cached FILENAME" -ForegroundColor Cyan
    exit 1
} else {
    Write-Host "[PASS] All security checks passed!" -ForegroundColor Green
    Write-Host "[SAFE] Ready to commit and push to public repository" -ForegroundColor Green
    Write-Host ""
    Write-Host "Final reminders:" -ForegroundColor Yellow
    Write-Host "   - Never share your .env file"
    Write-Host "   - Rotate keys if exposed"
    Write-Host "   - Review SECURITY.md for incident response"
}

