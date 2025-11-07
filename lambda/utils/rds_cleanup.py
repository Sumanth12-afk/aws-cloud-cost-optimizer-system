import boto3
from datetime import datetime, timedelta
import logging

logger = logging.getLogger()


class RDSCleanup:
    def __init__(self, region='us-east-1'):
        self.rds_client = boto3.client('rds', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)

    def get_idle_instances(self, idle_days=7):
        """Detect RDS instances with low connections for specified days"""
        idle_instances = []

        try:
            response = self.rds_client.describe_db_instances()

            for db_instance in response['DBInstances']:
                db_id = db_instance['DBInstanceIdentifier']
                db_status = db_instance['DBInstanceStatus']

                if db_status == 'available':
                    # Check CloudWatch metrics for database connections
                    avg_connections = self.get_average_connections(db_id, idle_days)
                    
                    if avg_connections < 1:  # Less than 1 average connection
                        estimated_savings = self.estimate_rds_savings(db_instance)
                        
                        tags_response = self.rds_client.list_tags_for_resource(
                            ResourceName=db_instance['DBInstanceArn']
                        )
                        
                        idle_instances.append({
                            'db_instance_id': db_id,
                            'db_instance_class': db_instance['DBInstanceClass'],
                            'engine': db_instance['Engine'],
                            'status': db_status,
                            'avg_connections': avg_connections,
                            'estimated_monthly_savings': estimated_savings,
                            'tags': {tag['Key']: tag['Value'] for tag in tags_response.get('TagList', [])}
                        })

            logger.info(f"Found {len(idle_instances)} idle RDS instances")
            return idle_instances

        except Exception as e:
            logger.error(f"Error detecting idle RDS instances: {e}")
            return []

    def get_average_connections(self, db_id, days=7):
        """Get average database connections over specified period"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)

            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='DatabaseConnections',
                Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # 1 day
                Statistics=['Average']
            )

            if response['Datapoints']:
                avg = sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])
                return round(avg, 2)
            return 0.0

        except Exception as e:
            logger.warning(f"Could not get CloudWatch metrics for {db_id}: {e}")
            return 0.0

    def estimate_rds_savings(self, db_instance):
        """Estimate monthly cost savings for RDS instance"""
        instance_class = db_instance['DBInstanceClass']
        
        # Simplified pricing estimates (USD/month)
        pricing_map = {
            'db.t2.micro': 14.60, 'db.t2.small': 29.20, 'db.t2.medium': 58.40,
            'db.t3.micro': 13.87, 'db.t3.small': 27.74, 'db.t3.medium': 55.48,
            'db.m5.large': 138.24, 'db.m5.xlarge': 276.48,
            'db.r5.large': 201.60, 'db.r5.xlarge': 403.20
        }
        
        return pricing_map.get(instance_class, 100.0)

    def stop_instance(self, db_id):
        """Stop RDS instance"""
        try:
            self.rds_client.stop_db_instance(DBInstanceIdentifier=db_id)
            logger.info(f"Stopped RDS instance: {db_id}")
            return True
        except Exception as e:
            logger.error(f"Error stopping RDS instance {db_id}: {e}")
            return False

    def delete_instance(self, db_id, skip_final_snapshot=False):
        """Delete RDS instance"""
        try:
            self.rds_client.delete_db_instance(
                DBInstanceIdentifier=db_id,
                SkipFinalSnapshot=skip_final_snapshot,
                FinalDBSnapshotIdentifier=f"{db_id}-final-snapshot" if not skip_final_snapshot else None
            )
            logger.info(f"Deleted RDS instance: {db_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting RDS instance {db_id}: {e}")
            return False

