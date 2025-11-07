#!/bin/bash
# Pre-commit security check script
# Run this before pushing to GitHub

set -e

echo "🔍 Running security pre-commit checks..."
echo ""

# Check if sensitive files are staged
echo "1️⃣ Checking for sensitive files..."
SENSITIVE_FILES=(".env" "terraform.tfvars" "*.pem" "*.key" "terraform.tfstate")
FOUND_SENSITIVE=false

for pattern in "${SENSITIVE_FILES[@]}"; do
    if git ls-files --cached | grep -q "$pattern"; then
        echo "❌ FOUND: $pattern is staged for commit!"
        FOUND_SENSITIVE=true
    fi
done

if [ "$FOUND_SENSITIVE" = true ]; then
    echo ""
    echo "⚠️  CRITICAL: Sensitive files detected!"
    echo "Run: git rm --cached <filename>"
    exit 1
fi
echo "✅ No sensitive files staged"
echo ""

# Check for AWS keys in code
echo "2️⃣ Scanning for AWS access keys..."
if git diff --cached | grep -E "AKIA[0-9A-Z]{16}"; then
    echo "❌ AWS Access Key detected in staged changes!"
    exit 1
fi
echo "✅ No AWS keys found"
echo ""

# Check for Slack webhooks
echo "3️⃣ Scanning for Slack webhook URLs..."
if git diff --cached | grep -E "hooks\.slack\.com/services/T[A-Z0-9]{8,}/B[A-Z0-9]{8,}/[A-Za-z0-9]{24}"; then
    echo "❌ Real Slack webhook URL detected!"
    echo "   Only placeholders like TXXXXXXXX should be committed"
    exit 1
fi
echo "✅ No real webhook URLs found"
echo ""

# Verify .gitignore exists
echo "4️⃣ Checking .gitignore..."
if [ ! -f ".gitignore" ]; then
    echo "❌ .gitignore file missing!"
    exit 1
fi
echo "✅ .gitignore present"
echo ""

# Check if .env.example has placeholders only
echo "5️⃣ Verifying .env.example has placeholders..."
if [ -f ".env.example" ]; then
    if grep -q "T09S89P2WD6" .env.example; then
        echo "❌ Real webhook URL found in .env.example!"
        exit 1
    fi
    if grep -q "AKIA[0-9A-Z]" .env.example && ! grep -q "AKIAIOSFODNN7EXAMPLE" .env.example; then
        echo "❌ Real AWS key found in .env.example!"
        exit 1
    fi
fi
echo "✅ .env.example contains placeholders only"
echo ""

echo "✅ All security checks passed!"
echo "✅ Safe to commit and push to public repository"
echo ""
echo "📝 Final reminders:"
echo "   - Never share your .env file"
echo "   - Rotate keys if exposed"
echo "   - Review SECURITY.md for incident response"

