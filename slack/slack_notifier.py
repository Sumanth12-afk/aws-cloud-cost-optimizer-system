import requests
import json
import logging
import os

logger = logging.getLogger()


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
    
    # Create Slack message
    slack_username = os.environ.get('SLACK_USERNAME', 'AWS Cost Optimizer Bot')
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
    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(message),
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("Slack notification sent successfully")
            return True
        else:
            logger.error(f"Slack notification failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending Slack notification: {e}")
        return False


def send_simple_message(webhook_url, message, channel=None):
    """Send simple text message to Slack"""
    slack_username = os.environ.get('SLACK_USERNAME', 'AWS Cost Optimizer Bot')
    payload = {
        "username": slack_username,
        "icon_emoji": ":moneybag:",
        "text": message
    }
    
    if channel:
        payload["channel"] = channel
    
    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error sending Slack message: {e}")
        return False

