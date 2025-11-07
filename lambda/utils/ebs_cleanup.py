import boto3
from datetime import datetime, timedelta
import logging

logger = logging.getLogger()


class EBSCleanup:
    def __init__(self, region='us-east-1'):
        self.ec2_client = boto3.client('ec2', region_name=region)

    def get_unattached_volumes(self):
        """Detect unattached EBS volumes"""
        unattached_volumes = []

        try:
            response = self.ec2_client.describe_volumes(
                Filters=[{'Name': 'status', 'Values': ['available']}]
            )

            for volume in response['Volumes']:
                volume_id = volume['VolumeId']
                size = volume['Size']
                volume_type = volume['VolumeType']
                create_time = volume['CreateTime']
                
                estimated_savings = self.estimate_ebs_savings(size, volume_type)
                
                unattached_volumes.append({
                    'volume_id': volume_id,
                    'size_gb': size,
                    'volume_type': volume_type,
                    'create_time': create_time.isoformat(),
                    'estimated_monthly_savings': estimated_savings,
                    'tags': {tag['Key']: tag['Value'] for tag in volume.get('Tags', [])}
                })

            logger.info(f"Found {len(unattached_volumes)} unattached EBS volumes")
            return unattached_volumes

        except Exception as e:
            logger.error(f"Error detecting unattached EBS volumes: {e}")
            return []

    def get_old_snapshots(self, days=90):
        """Detect old EBS snapshots"""
        old_snapshots = []
        cutoff_date = datetime.now(datetime.now().astimezone().tzinfo) - timedelta(days=days)

        try:
            response = self.ec2_client.describe_snapshots(OwnerIds=['self'])

            for snapshot in response['Snapshots']:
                snapshot_id = snapshot['SnapshotId']
                start_time = snapshot['StartTime']

                if start_time < cutoff_date:
                    volume_size = snapshot['VolumeSize']
                    estimated_savings = self.estimate_snapshot_savings(volume_size)
                    
                    old_snapshots.append({
                        'snapshot_id': snapshot_id,
                        'volume_id': snapshot.get('VolumeId', 'N/A'),
                        'size_gb': volume_size,
                        'start_time': start_time.isoformat(),
                        'age_days': (datetime.now(datetime.now().astimezone().tzinfo) - start_time).days,
                        'estimated_monthly_savings': estimated_savings,
                        'tags': {tag['Key']: tag['Value'] for tag in snapshot.get('Tags', [])}
                    })

            logger.info(f"Found {len(old_snapshots)} old snapshots (>{days} days)")
            return old_snapshots

        except Exception as e:
            logger.error(f"Error detecting old snapshots: {e}")
            return []

    def estimate_ebs_savings(self, size_gb, volume_type):
        """Estimate monthly cost savings for EBS volume"""
        # Pricing per GB/month
        pricing_per_gb = {
            'gp2': 0.10,
            'gp3': 0.08,
            'io1': 0.125,
            'io2': 0.125,
            'st1': 0.045,
            'sc1': 0.015
        }
        
        price_per_gb = pricing_per_gb.get(volume_type, 0.10)
        return round(size_gb * price_per_gb, 2)

    def estimate_snapshot_savings(self, size_gb):
        """Estimate monthly cost savings for snapshot"""
        # Snapshot pricing per GB/month
        return round(size_gb * 0.05, 2)

    def delete_volume(self, volume_id):
        """Delete EBS volume"""
        try:
            self.ec2_client.delete_volume(VolumeId=volume_id)
            logger.info(f"Deleted EBS volume: {volume_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting volume {volume_id}: {e}")
            return False

    def delete_snapshot(self, snapshot_id):
        """Delete EBS snapshot"""
        try:
            self.ec2_client.delete_snapshot(SnapshotId=snapshot_id)
            logger.info(f"Deleted snapshot: {snapshot_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting snapshot {snapshot_id}: {e}")
            return False

