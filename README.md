# AWS Cloud Cost Optimization & Auto-Governance System

Production-grade system to detect and clean idle/untagged AWS resources, enforce governance policies, and send cost-savings alerts via Slack.

## 🎯 Features

- **Cost Detection**: Idle EC2, RDS instances, unattached EBS volumes, old snapshots
- **Tag Governance**: Enforce required tags across resources
- **Automated Cleanup**: Optional auto-termination of idle resources
- **Slack Alerts**: Rich formatted notifications with cost estimates
- **Daily Scanning**: Automated via EventBridge cron schedule
- **S3 Reports**: JSON reports stored in S3 for audit trail

## 🏗️ Architecture

```
EventBridge (Daily) → Lambda Function → Boto3 SDK
                          ↓
    ┌─────────────────────┼─────────────────────┐
    ↓                     ↓                     ↓
  EC2/EBS              RDS               Tag Compliance
    ↓                     ↓                     ↓
    └─────────────────────┼─────────────────────┘
                          ↓
                    S3 Report + Slack Alert
```

## 📋 Prerequisites

- AWS Account with appropriate permissions
- Slack Workspace with Incoming Webhooks
- Terraform >= 1.0
- Python 3.11+ (for local testing)

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/aws-cloud-cost-optimizer
cd aws-cloud-cost-optimizer
```

> **⚠️ BEFORE PUSHING TO YOUR PUBLIC REPO:**
> 1. Read `BEFORE_PUSH_CHECKLIST.md`
> 2. Run security check: `.\pre-commit-check.ps1` (Windows) or `./pre-commit-check.sh` (Linux/Mac)
> 3. Verify no secrets are exposed!

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your credentials (see SECURITY.md)
```

Required variables:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `SLACK_WEBHOOK_URL`

### 3. Configure Terraform

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 4. Deploy Infrastructure

```bash
terraform init
terraform plan
terraform apply
```

### 5. Verify Deployment

```bash
# Check Lambda function
aws lambda invoke --function-name aws-cost-optimizer output.json

# Check logs
aws logs tail /aws/lambda/aws-cost-optimizer --follow
```

## ⚙️ Configuration

### Cost Optimization Thresholds

Edit in `.env` or Terraform variables:

```bash
IDLE_EC2_DAYS=7          # Days before EC2 considered idle
IDLE_RDS_DAYS=7          # Days before RDS considered idle
COST_THRESHOLD=50        # Minimum $ to trigger alert
AUTO_TERMINATE=false     # Set true to auto-delete resources
```

### Tag Policy

Edit `config/policy.json`:

```json
{
  "required_tags": ["Owner", "Project", "Environment"]
}
```

### Schedule

Edit cron expression in `terraform/variables.tf`:

```hcl
schedule_expression = "cron(0 9 * * ? *)"  # Daily at 9 AM UTC
```

## 📊 Slack Notifications

Alerts include:
- 💰 Total estimated monthly savings
- 🖥️ Idle EC2 instance count
- 🗄️ Idle RDS instance count
- 💾 Unattached EBS volumes
- 📸 Old snapshots (>90 days)
- 🏷️ Non-compliant resources
- 🔗 Link to detailed S3 report

## 🔒 Security

**⚠️ CRITICAL: Webhook URLs are SECRET credentials!**

**NEVER expose in public repositories:**
- ❌ Slack Webhook URLs
- ❌ AWS Access Keys
- ❌ `.env` files
- ❌ `terraform.tfvars` files

**What happens if webhook is exposed:**
- Anyone can spam your Slack channel
- Could be used for phishing attacks
- Must regenerate immediately if leaked

**Protection measures:**
- ✅ `.gitignore` pre-configured to exclude secrets
- ✅ Use `.env.example` with placeholders only
- ✅ Real credentials go in `.env` (never committed)
- ✅ Use IAM roles for production (no keys needed)

See [SECURITY.md](SECURITY.md) for comprehensive guidelines and incident response.

## 📁 Project Structure

```
aws-cloud-cost-optimizer/
├── terraform/              # Infrastructure as Code
│   ├── main.tf            # S3, CloudWatch, EventBridge
│   ├── iam.tf             # Least-privilege IAM policies
│   ├── lambda.tf          # Lambda deployment
│   ├── variables.tf       # Configuration variables
│   └── outputs.tf         # Terraform outputs
├── lambda/                # Lambda function code
│   ├── main.py            # Main handler
│   ├── requirements.txt   # Python dependencies
│   └── utils/             # Cleanup modules
│       ├── ec2_cleanup.py
│       ├── rds_cleanup.py
│       ├── ebs_cleanup.py
│       └── tagging_enforcer.py
├── slack/                 # Slack integration
│   └── slack_notifier.py
├── config/                # Policies
│   └── policy.json
├── .env.example           # Environment template
├── .gitignore             # Security exclusions
└── SECURITY.md            # Security guidelines
```

## 🧪 Local Testing

```bash
# Install dependencies
cd lambda
pip install -r requirements.txt

# Set environment variables
export $(cat ../.env | xargs)

# Test Lambda function
python -c "from main import lambda_handler; lambda_handler({}, None)"
```

## 📈 Estimated Costs

AWS costs for this solution:
- Lambda: ~$0.20/month (5-min runs daily)
- S3: ~$0.10/month (reports storage)
- CloudWatch Logs: ~$0.50/month
- **Total: ~$1/month**

Potential savings: **$100-$5000+/month** depending on infrastructure waste.

## 🛠️ Customization

### Add New Resource Types

1. Create new cleanup module in `lambda/utils/`
2. Import in `lambda/main.py`
3. Add IAM permissions in `terraform/iam.tf`

### Custom Notification Channels

Extend `slack/slack_notifier.py` or add:
- Email via SNS
- Microsoft Teams
- PagerDuty

## 🐛 Troubleshooting

### Lambda Timeout
Increase in `terraform/variables.tf`:
```hcl
lambda_timeout = 600  # 10 minutes
```

### IAM Permission Errors
Check CloudWatch Logs:
```bash
aws logs tail /aws/lambda/aws-cost-optimizer --follow
```

### Slack Webhook Not Working
Test webhook:
```bash
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test message"}' \
  YOUR_WEBHOOK_URL
```

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Never commit sensitive data
4. Submit pull request

## ⚠️ Disclaimer

**USE WITH CAUTION**: Setting `AUTO_TERMINATE=true` will delete AWS resources. Always test in a non-production environment first.

## 📧 Support

For issues and questions:
- Open a GitHub issue
- Review `SECURITY.md` for security concerns
- Check CloudWatch Logs for errors

---

**Made with ❤️ for DevOps Engineers**

