# Security Best Practices

## 🔒 Protecting Sensitive Information

This project requires sensitive credentials. Follow these guidelines to keep them secure.

## Required Secrets

### 1. AWS Credentials
- Never commit AWS access keys to git
- Use IAM roles when running on AWS Lambda (recommended)
- For local testing, use AWS CLI profiles or environment variables
- Rotate access keys every 90 days

### 2. Slack Webhook URL
- Keep webhook URLs private
- Regenerate if accidentally exposed
- Use environment variables, not hardcoded values

## Setup Instructions

### Step 1: Environment Variables (Local Development)

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your actual credentials
# NEVER commit .env to git (already in .gitignore)
```

### Step 2: Terraform Variables

```bash
# In terraform/ directory
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
# NEVER commit terraform.tfvars to git (already in .gitignore)
```

### Step 3: Verify .gitignore

Before committing, ensure these files are NOT tracked:
```bash
git status

# Should NOT see:
# - .env
# - terraform/terraform.tfvars
# - terraform/terraform.tfstate
# - Any *.pem or *.key files
```

## Production Deployment

### Recommended: Use AWS Secrets Manager

Instead of environment variables, use AWS Secrets Manager for production:

```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage
secrets = get_secret('prod/cost-optimizer/config')
slack_webhook = secrets['slack_webhook_url']
```

### Alternative: Parameter Store

```python
import boto3

ssm = boto3.client('ssm')
response = ssm.get_parameter(Name='/prod/slack/webhook', WithDecryption=True)
webhook_url = response['Parameter']['Value']
```

## IAM Best Practices

### Least Privilege Policy
The Lambda function uses minimal required permissions:
- EC2: Read and limited write (only for cost optimization)
- RDS: Read and stop (no delete in production)
- S3: Write only to specific bucket
- CloudWatch: Logs only

### Separate Environments
Create separate IAM roles for:
- Development: Read-only access
- Staging: Read + stop resources
- Production: Full cost optimization access

## Accidental Exposure Response

### If AWS Keys Are Exposed:
1. Immediately delete the key in AWS Console (IAM → Users → Security Credentials)
2. Create new access key
3. Update .env file
4. Rotate all related secrets
5. Check CloudTrail for unauthorized access

### If Slack Webhook Is Exposed:
**ACT IMMEDIATELY - Anyone can spam your channel!**

1. **Revoke the webhook:**
   - Go to https://api.slack.com/apps
   - Select your app
   - Go to "Incoming Webhooks"
   - Delete the compromised webhook
   - Click "Add New Webhook to Workspace"
   - Copy the NEW webhook URL

2. **Update all configurations:**
   ```bash
   # Update local .env
   vim .env
   
   # Update Terraform
   terraform apply -var="slack_webhook_url=NEW_WEBHOOK_URL"
   
   # Update Lambda environment variables
   aws lambda update-function-configuration \
     --function-name aws-cost-optimizer \
     --environment "Variables={SLACK_WEBHOOK_URL=NEW_WEBHOOK_URL,...}"
   ```

3. **Check for abuse:**
   - Review Slack channel history for spam
   - Check workspace audit logs (Admin only)
   - Monitor for unusual messages

4. **If webhook was in git history:**
   - Revoke webhook FIRST
   - Then clean git history (see below)

### If Git Committed Secrets:
```bash
# Remove from history (use with caution)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (coordinate with team)
git push origin --force --all
```

## Security Scanning

### Pre-commit Hook (Recommended)

Install git-secrets:
```bash
# Install git-secrets
brew install git-secrets  # macOS
# or download from: https://github.com/awslabs/git-secrets

# Initialize
cd aws-cloud-cost-optimizer
git secrets --install
git secrets --register-aws
```

### GitHub Secret Scanning
- Enabled automatically for public repos
- Configure alerts in repo settings

## Audit Checklist

Before making repository public:
- [ ] `.env` is in `.gitignore` and not committed
- [ ] `terraform.tfvars` is in `.gitignore` and not committed
- [ ] Terraform state files are not committed
- [ ] No AWS keys in code or commit history
- [ ] No Slack webhooks in code or commit history
- [ ] `.env.example` contains only placeholders
- [ ] `terraform.tfvars.example` contains only placeholders
- [ ] README has no sensitive information
- [ ] All secrets use environment variables or secret managers

## Continuous Security

### Monthly:
- Review IAM permissions
- Check CloudTrail logs
- Audit S3 bucket access

### Quarterly:
- Rotate AWS access keys
- Review Slack app permissions
- Update dependencies (`pip list --outdated`)

## Contact

For security concerns, please create a private issue or contact the maintainer directly.

