# ✅ Before Pushing to Public GitHub - Security Checklist

## 🚨 Critical: Run This Before Making Repo Public!

### Step 1: Run Security Check Script

**Windows:**
```powershell
.\pre-commit-check.ps1
```

**Linux/Mac:**
```bash
chmod +x pre-commit-check.sh
./pre-commit-check.sh
```

---

## 📋 Manual Verification Checklist

### ✅ Files That MUST Have Placeholder Values Only:

- [ ] `.env.example` - Check webhook URL
- [ ] `terraform/terraform.tfvars.example` - Check webhook URL
- [ ] `README.md` - No real credentials in examples
- [ ] `SECURITY.md` - No real credentials in examples

### ❌ Files That MUST NOT Be Committed:

- [ ] `.env` (your actual credentials)
- [ ] `terraform/terraform.tfvars` (your actual credentials)
- [ ] `terraform/terraform.tfstate` (may contain secrets)
- [ ] Any `.pem` or `.key` files

### ✅ Files That MUST Exist:

- [ ] `.gitignore` (configured to exclude secrets)
- [ ] `SECURITY.md` (security documentation)
- [ ] `README.md` (setup instructions)
- [ ] `LICENSE` (MIT license)

---

## 🔍 Quick Visual Inspection

### Check .env.example:
```bash
cat .env.example | grep SLACK_WEBHOOK_URL
```
**Should show:** `TXXXXXXXX/BXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXX` (placeholders)
**Should NOT show:** Real webhook with actual IDs

### Check terraform.tfvars.example:
```bash
cat terraform/terraform.tfvars.example | grep slack_webhook_url
```
**Should show:** Placeholder webhook URL

### Verify .gitignore works:
```bash
git status
```
**Should NOT see:**
- `.env`
- `terraform.tfvars`
- `*.tfstate`

---

## 🔐 Security Test

### Test 1: Check Staged Files
```bash
git add .
git status
```

Should NOT see:
- `.env`
- `terraform/terraform.tfvars`
- `terraform/terraform.tfstate`
- Any `.pem` or `.key` files

### Test 2: Search for Secrets in Staged Content
```bash
# Check for AWS keys
git diff --cached | grep -E "AKIA[0-9A-Z]{16}"

# Check for real Slack webhooks
git diff --cached | grep -E "hooks.slack.com/services/T[0-9A-Z]{8,}/B[0-9A-Z]{8,}/[A-Za-z0-9]{24}"
```

Both should return: **NO RESULTS**

---

## 🚀 Safe to Push If:

✅ Security check script passed
✅ Manual checklist completed
✅ No sensitive files in `git status`
✅ `.env.example` has placeholders only
✅ `terraform.tfvars.example` has placeholders only
✅ No secrets in `git diff --cached`

---

## ⚠️ If You Find Exposed Secrets:

### Option 1: Not Yet Committed
```bash
# Remove from staging
git rm --cached .env
git rm --cached terraform/terraform.tfvars
```

### Option 2: Already Committed (Not Pushed)
```bash
# Reset last commit
git reset HEAD~1
# Remove sensitive files
git rm --cached .env
# Recommit
git commit -m "Initial commit"
```

### Option 3: Already Pushed to GitHub
1. **IMMEDIATELY** rotate all exposed credentials:
   - AWS: Delete access keys, create new ones
   - Slack: Revoke webhook, generate new one
2. Force push cleaned history (see `SECURITY.md`)
3. Consider making repo private temporarily

---

## 📝 Initial Commit Message Template

```
Initial commit: AWS Cloud Cost Optimizer

Production-grade cost optimization system with:
- Automated detection of idle EC2, RDS, EBS resources
- Tag compliance enforcement
- Slack notifications
- Daily scheduled scanning via EventBridge
- Terraform infrastructure as code

Security: All sensitive credentials excluded via .gitignore
```

---

## 🎯 After Pushing

### Update Repository Settings:
1. Go to GitHub repo → Settings → Security
2. Enable "Secret scanning"
3. Enable "Dependabot alerts"
4. Add branch protection rules for `main`

### Add Repository Secrets (for GitHub Actions if needed):
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `SLACK_WEBHOOK_URL`

**Never put these in code or .env files in the repo!**

---

## ✅ Final Confirmation

Before running `git push`:

```bash
echo "I have verified:"
echo "✅ No real AWS credentials in code"
echo "✅ No real Slack webhook URLs in code"
echo "✅ .env is excluded by .gitignore"
echo "✅ terraform.tfvars is excluded by .gitignore"
echo "✅ Security check script passed"
echo "✅ All placeholder values verified"
```

If all above are true, you're safe to push! 🎉

