import json
import os
import logging
from datetime import datetime
import boto3
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.ec2_cleanup import EC2Cleanup
from utils.rds_cleanup import RDSCleanup
from utils.ebs_cleanup import EBSCleanup
from utils.tagging_enforcer import TaggingEnforcer

# Configure logging
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logger = logging.getLogger()
logger.setLevel(getattr(logging, log_level))


def lambda_handler(event, context):
    """Main Lambda handler for cost optimization"""
    logger.info("Starting AWS Cost Optimization scan...")
    
    # Get configuration from environment
    region = os.environ.get('AWS_REGION', 'us-east-1')
    report_bucket = os.environ.get('REPORT_BUCKET', 'aws-cost-optimizer-reports')
    idle_ec2_days = int(os.environ.get('IDLE_EC2_DAYS', 7))
    idle_rds_days = int(os.environ.get('IDLE_RDS_DAYS', 7))
    auto_terminate = os.environ.get('AUTO_TERMINATE', 'false').lower() == 'true'
    cost_threshold = float(os.environ.get('COST_THRESHOLD', 50))
    required_tags = os.environ.get('REQUIRED_TAGS', 'Owner,Project,Environment').split(',')
    slack_webhook = os.environ.get('SLACK_WEBHOOK_URL', '')
    
    # Initialize cleanup modules
    ec2_cleanup = EC2Cleanup(region=region)
    rds_cleanup = RDSCleanup(region=region)
    ebs_cleanup = EBSCleanup(region=region)
    tagging_enforcer = TaggingEnforcer(region=region, required_tags=required_tags)
    
    # Collect cost optimization opportunities
    report = {
        'scan_date': datetime.now().isoformat(),
        'region': region,
        'configuration': {
            'idle_ec2_days': idle_ec2_days,
            'idle_rds_days': idle_rds_days,
            'auto_terminate': auto_terminate,
            'cost_threshold': cost_threshold,
            'required_tags': required_tags
        },
        'findings': {},
        'summary': {}
    }
    
    # Scan for idle EC2 instances
    logger.info("Scanning for idle EC2 instances...")
    idle_ec2 = ec2_cleanup.get_idle_instances(idle_days=idle_ec2_days)
    report['findings']['idle_ec2_instances'] = idle_ec2
    
    # Scan for idle RDS instances
    logger.info("Scanning for idle RDS instances...")
    idle_rds = rds_cleanup.get_idle_instances(idle_days=idle_rds_days)
    report['findings']['idle_rds_instances'] = idle_rds
    
    # Scan for unattached EBS volumes
    logger.info("Scanning for unattached EBS volumes...")
    unattached_volumes = ebs_cleanup.get_unattached_volumes()
    report['findings']['unattached_ebs_volumes'] = unattached_volumes
    
    # Scan for old snapshots
    logger.info("Scanning for old EBS snapshots...")
    old_snapshots = ebs_cleanup.get_old_snapshots(days=90)
    report['findings']['old_snapshots'] = old_snapshots
    
    # Check tag compliance
    logger.info("Checking tag compliance...")
    non_compliant_resources = tagging_enforcer.get_all_non_compliant_resources()
    report['findings']['non_compliant_resources'] = non_compliant_resources
    
    # Calculate total potential savings
    total_savings = 0
    total_savings += sum(item['estimated_monthly_savings'] for item in idle_ec2)
    total_savings += sum(item['estimated_monthly_savings'] for item in idle_rds)
    total_savings += sum(item['estimated_monthly_savings'] for item in unattached_volumes)
    total_savings += sum(item['estimated_monthly_savings'] for item in old_snapshots)
    
    # Generate summary
    report['summary'] = {
        'total_estimated_monthly_savings': round(total_savings, 2),
        'idle_ec2_count': len(idle_ec2),
        'idle_rds_count': len(idle_rds),
        'unattached_volumes_count': len(unattached_volumes),
        'old_snapshots_count': len(old_snapshots),
        'non_compliant_resources_count': len(non_compliant_resources),
        'actions_taken': []
    }
    
    # Perform cleanup actions if auto_terminate is enabled
    if auto_terminate:
        logger.info("Auto-terminate is enabled. Performing cleanup actions...")
        
        # Terminate idle EC2 instances
        for instance in idle_ec2:
            if ec2_cleanup.terminate_instance(instance['instance_id']):
                report['summary']['actions_taken'].append(
                    f"Terminated EC2 instance: {instance['instance_id']}"
                )
        
        # Stop idle RDS instances
        for db_instance in idle_rds:
            if rds_cleanup.stop_instance(db_instance['db_instance_id']):
                report['summary']['actions_taken'].append(
                    f"Stopped RDS instance: {db_instance['db_instance_id']}"
                )
        
        # Delete unattached volumes
        for volume in unattached_volumes:
            if ebs_cleanup.delete_volume(volume['volume_id']):
                report['summary']['actions_taken'].append(
                    f"Deleted EBS volume: {volume['volume_id']}"
                )
        
        # Delete old snapshots
        for snapshot in old_snapshots:
            if ebs_cleanup.delete_snapshot(snapshot['snapshot_id']):
                report['summary']['actions_taken'].append(
                    f"Deleted snapshot: {snapshot['snapshot_id']}"
                )
    else:
        report['summary']['actions_taken'].append("Report-only mode: No resources terminated")
    
    # Save report to S3
    report_key = f"reports/cost-optimization-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.json"
    save_report_to_s3(report, report_bucket, report_key)
    
    # Send Slack notification if webhook configured
    if slack_webhook and total_savings >= cost_threshold:
        send_slack_notification(report, slack_webhook, report_bucket, report_key)
    
    logger.info(f"Cost optimization scan complete. Total potential savings: ${total_savings:.2f}/month")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Cost optimization scan completed',
            'total_savings': total_savings,
            'report_location': f"s3://{report_bucket}/{report_key}"
        })
    }


def save_report_to_s3(report, bucket, key):
    """Save cost optimization report to S3"""
    try:
        s3_client = boto3.client('s3')
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(report, indent=2),
            ContentType='application/json'
        )
        logger.info(f"Report saved to s3://{bucket}/{key}")
    except Exception as e:
        logger.error(f"Error saving report to S3: {e}")


def send_slack_notification(report, webhook_url, bucket, report_key):
    """Send Slack notification with cost optimization summary"""
    try:
        # Import slack notifier - use requests directly for Lambda compatibility
        import requests
        
        def send_cost_alert(webhook_url, total_savings, idle_ec2_count, idle_rds_count, 
                           unattached_volumes_count, old_snapshots_count, non_compliant_count,
                           actions_taken, report_url):
            """Send formatted cost optimization alert to Slack"""
            
            # Determine urgency emoji based on savings amount
            if total_savings >= 500:
                urgency_emoji = "🚨"
                urgency_text = "CRITICAL"
            elif total_savings >= 200:
                urgency_emoji = "⚠️"
                urgency_text = "HIGH"
            elif total_savings >= 50:
                urgency_emoji = "💡"
                urgency_text = "MEDIUM"
            else:
                urgency_emoji = "✅"
                urgency_text = "LOW"
            
            # Build actions summary
            actions_summary = "\n".join([f"  • {action}" for action in actions_taken[:5]])
            if len(actions_taken) > 5:
                actions_summary += f"\n  • ... and {len(actions_taken) - 5} more actions"
            
            slack_username = os.environ.get('SLACK_USERNAME', 'AWS Cost Optimizer Bot')
            
            # Create Slack message
            message = {
                "username": slack_username,
                "icon_emoji": ":moneybag:",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{urgency_emoji} AWS Cost Optimization Report",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Priority Level:*\n{urgency_text}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Estimated Monthly Savings:*\n💰 ${total_savings:.2f}"
                            }
                        ]
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Resource Findings:*"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"🖥️ *Idle EC2 Instances:*\n{idle_ec2_count}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"🗄️ *Idle RDS Instances:*\n{idle_rds_count}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"💾 *Unattached EBS Volumes:*\n{unattached_volumes_count}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"📸 *Old Snapshots (>90 days):*\n{old_snapshots_count}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"🏷️ *Non-Compliant Resources:*\n{non_compliant_count}"
                            }
                        ]
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Actions Taken:*\n{actions_summary}"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"📊 <{report_url}|View Full Report in S3>"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": "💡 *Tip:* Enable auto-terminate mode to automatically clean up idle resources"
                            }
                        ]
                    }
                ]
            }
            
            # Send to Slack
            response = requests.post(
                webhook_url,
                data=json.dumps(message),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            return response.status_code == 200
        
        summary = report['summary']
        send_cost_alert(
            webhook_url=webhook_url,
            total_savings=summary['total_estimated_monthly_savings'],
            idle_ec2_count=summary['idle_ec2_count'],
            idle_rds_count=summary['idle_rds_count'],
            unattached_volumes_count=summary['unattached_volumes_count'],
            old_snapshots_count=summary['old_snapshots_count'],
            non_compliant_count=summary['non_compliant_resources_count'],
            actions_taken=summary['actions_taken'],
            report_url=f"https://s3.console.aws.amazon.com/s3/object/{bucket}?prefix={report_key}"
        )
        logger.info("Slack notification sent successfully")
    except Exception as e:
        logger.error(f"Error sending Slack notification: {e}")


# Example report schema (for reference, not created as file)
"""
{
  "scan_date": "2025-11-07T10:30:00",
  "region": "us-east-1",
  "configuration": {
    "idle_ec2_days": 7,
    "idle_rds_days": 7,
    "auto_terminate": false,
    "cost_threshold": 50,
    "required_tags": ["Owner", "Project", "Environment"]
  },
  "findings": {
    "idle_ec2_instances": [
      {
        "instance_id": "i-1234567890abcdef0",
        "instance_type": "t3.medium",
        "stopped_date": "2025-10-25T08:15:00",
        "days_stopped": 13,
        "estimated_monthly_savings": 29.95,
        "tags": {"Name": "test-instance"}
      }
    ],
    "idle_rds_instances": [],
    "unattached_ebs_volumes": [],
    "old_snapshots": [],
    "non_compliant_resources": []
  },
  "summary": {
    "total_estimated_monthly_savings": 450.75,
    "idle_ec2_count": 5,
    "idle_rds_count": 2,
    "unattached_volumes_count": 8,
    "old_snapshots_count": 12,
    "non_compliant_resources_count": 15,
    "actions_taken": ["Report-only mode: No resources terminated"]
  }
}
"""

