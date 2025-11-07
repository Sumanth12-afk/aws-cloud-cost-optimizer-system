import boto3
import json
import logging

logger = logging.getLogger()


class TaggingEnforcer:
    def __init__(self, region='us-east-1', required_tags=None):
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.rds_client = boto3.client('rds', region_name=region)
        self.required_tags = required_tags or ['Owner', 'Project', 'Environment']

    def check_ec2_tags(self):
        """Check EC2 instances for required tags"""
        non_compliant_resources = []

        try:
            response = self.ec2_client.describe_instances()

            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    instance_state = instance['State']['Name']
                    
                    if instance_state != 'terminated':
                        tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                        missing_tags = [tag for tag in self.required_tags if tag not in tags]
                        
                        if missing_tags:
                            non_compliant_resources.append({
                                'resource_type': 'EC2',
                                'resource_id': instance_id,
                                'resource_name': tags.get('Name', 'N/A'),
                                'missing_tags': missing_tags,
                                'existing_tags': tags
                            })

            logger.info(f"Found {len(non_compliant_resources)} non-compliant EC2 instances")
            return non_compliant_resources

        except Exception as e:
            logger.error(f"Error checking EC2 tags: {e}")
            return []

    def check_ebs_tags(self):
        """Check EBS volumes for required tags"""
        non_compliant_volumes = []

        try:
            response = self.ec2_client.describe_volumes()

            for volume in response['Volumes']:
                volume_id = volume['VolumeId']
                tags = {tag['Key']: tag['Value'] for tag in volume.get('Tags', [])}
                missing_tags = [tag for tag in self.required_tags if tag not in tags]
                
                if missing_tags:
                    non_compliant_volumes.append({
                        'resource_type': 'EBS',
                        'resource_id': volume_id,
                        'resource_name': tags.get('Name', 'N/A'),
                        'missing_tags': missing_tags,
                        'existing_tags': tags
                    })

            logger.info(f"Found {len(non_compliant_volumes)} non-compliant EBS volumes")
            return non_compliant_volumes

        except Exception as e:
            logger.error(f"Error checking EBS tags: {e}")
            return []

    def check_rds_tags(self):
        """Check RDS instances for required tags"""
        non_compliant_instances = []

        try:
            response = self.rds_client.describe_db_instances()

            for db_instance in response['DBInstances']:
                db_id = db_instance['DBInstanceIdentifier']
                db_arn = db_instance['DBInstanceArn']
                
                tags_response = self.rds_client.list_tags_for_resource(ResourceName=db_arn)
                tags = {tag['Key']: tag['Value'] for tag in tags_response.get('TagList', [])}
                missing_tags = [tag for tag in self.required_tags if tag not in tags]
                
                if missing_tags:
                    non_compliant_instances.append({
                        'resource_type': 'RDS',
                        'resource_id': db_id,
                        'resource_name': db_id,
                        'missing_tags': missing_tags,
                        'existing_tags': tags
                    })

            logger.info(f"Found {len(non_compliant_instances)} non-compliant RDS instances")
            return non_compliant_instances

        except Exception as e:
            logger.error(f"Error checking RDS tags: {e}")
            return []

    def get_all_non_compliant_resources(self):
        """Get all non-compliant resources across services"""
        all_non_compliant = []
        
        all_non_compliant.extend(self.check_ec2_tags())
        all_non_compliant.extend(self.check_ebs_tags())
        all_non_compliant.extend(self.check_rds_tags())
        
        return all_non_compliant

    def apply_default_tags(self, resource_type, resource_id, default_tags):
        """Apply default tags to non-compliant resource"""
        try:
            if resource_type == 'EC2':
                self.ec2_client.create_tags(
                    Resources=[resource_id],
                    Tags=[{'Key': k, 'Value': v} for k, v in default_tags.items()]
                )
            elif resource_type == 'EBS':
                self.ec2_client.create_tags(
                    Resources=[resource_id],
                    Tags=[{'Key': k, 'Value': v} for k, v in default_tags.items()]
                )
            elif resource_type == 'RDS':
                # Get RDS ARN
                response = self.rds_client.describe_db_instances(DBInstanceIdentifier=resource_id)
                db_arn = response['DBInstances'][0]['DBInstanceArn']
                
                self.rds_client.add_tags_to_resource(
                    ResourceName=db_arn,
                    Tags=[{'Key': k, 'Value': v} for k, v in default_tags.items()]
                )
            
            logger.info(f"Applied default tags to {resource_type} resource: {resource_id}")
            return True

        except Exception as e:
            logger.error(f"Error applying tags to {resource_type} {resource_id}: {e}")
            return False

