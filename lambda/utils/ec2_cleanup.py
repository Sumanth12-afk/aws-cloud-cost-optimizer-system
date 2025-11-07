import boto3
from datetime import datetime, timedelta
import logging

logger = logging.getLogger()


class EC2Cleanup:
    def __init__(self, region='us-east-1'):
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)

    def get_idle_instances(self, idle_days=7):
        """Detect EC2 instances stopped for more than specified days"""
        idle_instances = []
        stopped_threshold = datetime.now() - timedelta(days=idle_days)

        try:
            response = self.ec2_client.describe_instances(
                Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}]
            )

            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    state_transition = instance.get('StateTransitionReason', '')
                    
                    # Extract stop time from state transition reason
                    if 'User initiated' in state_transition:
                        try:
                            # Parse stop date from state transition
                            stop_time_str = state_transition.split('(')[1].split(')')[0]
                            stop_time = datetime.strptime(stop_time_str, '%Y-%m-%d %H:%M:%S %Z')
                            
                            if stop_time < stopped_threshold:
                                estimated_savings = self.estimate_ec2_savings(instance)
                                idle_instances.append({
                                    'instance_id': instance_id,
                                    'instance_type': instance['InstanceType'],
                                    'stopped_date': stop_time.isoformat(),
                                    'days_stopped': (datetime.now() - stop_time).days,
                                    'estimated_monthly_savings': estimated_savings,
                                    'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                                })
                        except Exception as e:
                            logger.warning(f"Could not parse stop time for {instance_id}: {e}")
            
            logger.info(f"Found {len(idle_instances)} idle EC2 instances")
            return idle_instances

        except Exception as e:
            logger.error(f"Error detecting idle EC2 instances: {e}")
            return []

    def estimate_ec2_savings(self, instance):
        """Estimate monthly cost savings for terminated instance"""
        instance_type = instance['InstanceType']
        
        # Simplified pricing estimates (USD/month) - should use AWS Pricing API in production
        pricing_map = {
            't2.micro': 8.64, 't2.small': 17.28, 't2.medium': 34.56,
            't3.micro': 7.49, 't3.small': 14.98, 't3.medium': 29.95,
            'm5.large': 69.12, 'm5.xlarge': 138.24, 'm5.2xlarge': 276.48,
            'c5.large': 61.20, 'c5.xlarge': 122.40
        }
        
        return pricing_map.get(instance_type, 50.0)

    def terminate_instance(self, instance_id):
        """Terminate EC2 instance"""
        try:
            self.ec2_client.terminate_instances(InstanceIds=[instance_id])
            logger.info(f"Terminated EC2 instance: {instance_id}")
            return True
        except Exception as e:
            logger.error(f"Error terminating instance {instance_id}: {e}")
            return False

    def stop_instance(self, instance_id):
        """Stop EC2 instance"""
        try:
            self.ec2_client.stop_instances(InstanceIds=[instance_id])
            logger.info(f"Stopped EC2 instance: {instance_id}")
            return True
        except Exception as e:
            logger.error(f"Error stopping instance {instance_id}: {e}")
            return False

