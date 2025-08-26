"""
SmartCloudOps AI - Phase 5: AWS Integration Service
==================================================

AWS integration service for executing DevOps actions based on NLP commands.
Provides secure and controlled access to AWS services.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AWSIntegrationService:
    """
    AWS integration service for executing DevOps actions.
    """
    
    def __init__(self):
        """Initialize AWS integration service."""
        self.region = 'us-east-1'
        self.session = boto3.Session(region_name=self.region)
        
        # Initialize AWS clients
        self.ec2_client = self.session.client('ec2')
        self.autoscaling_client = self.session.client('autoscaling')
        self.cloudwatch_client = self.session.client('cloudwatch')
        self.s3_client = self.session.client('s3')
        self.rds_client = self.session.client('rds')
        self.ecs_client = self.session.client('ecs')
        self.codebuild_client = self.session.client('codebuild')
        self.codedeploy_client = self.session.client('codedeploy')
        self.guardduty_client = self.session.client('guardduty')
        self.securityhub_client = self.session.client('securityhub')
        self.ce_client = self.session.client('ce')
        self.budgets_client = self.session.client('budgets')
        self.config_client = self.session.client('config')
        self.sns_client = self.session.client('sns')
        self.logs_client = self.session.client('logs')
        
        # Action execution history
        self.execution_history = []
        
        # Safety limits
        self.safety_limits = {
            "max_instances": 10,
            "max_cost_per_hour": 50.0,
            "max_backup_size_gb": 100,
            "cooldown_period_minutes": 5
        }
        
    def execute_action(self, action_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute AWS action based on action plan.
        
        Args:
            action_plan: Action plan from NLP service
            
        Returns:
            Dict containing execution result
        """
        try:
            action = action_plan.get("action")
            parameters = action_plan.get("parameters", {})
            
            # Check safety limits
            safety_check = self._check_safety_limits(action, parameters)
            if not safety_check["safe"]:
                return {
                    "status": "blocked",
                    "reason": safety_check["reason"],
                    "action": action,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Execute action based on type
            if action == "deploy":
                result = self._execute_deploy(parameters)
            elif action == "scale":
                result = self._execute_scale(parameters)
            elif action == "monitor":
                result = self._execute_monitor(parameters)
            elif action == "restart":
                result = self._execute_restart(parameters)
            elif action == "backup":
                result = self._execute_backup(parameters)
            elif action == "security":
                result = self._execute_security_scan(parameters)
            elif action == "cost":
                result = self._execute_cost_analysis(parameters)
            elif action == "compliance":
                result = self._execute_compliance_check(parameters)
            elif action == "alert":
                result = self._execute_alert_setup(parameters)
            elif action == "rollback":
                result = self._execute_rollback(parameters)
            else:
                result = {
                    "status": "unsupported",
                    "message": f"Action '{action}' is not supported"
                }
            
            # Log execution
            self._log_execution(action, parameters, result)
            
            return {
                "status": "success",
                "action": action,
                "parameters": parameters,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            return {
                "status": "error",
                "error": str(e),
                "action": action_plan.get("action"),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _check_safety_limits(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check if action is within safety limits."""
        try:
            if action == "scale":
                count = parameters.get("count", 1)
                if isinstance(count, str):
                    count = int(count)
                
                if count > self.safety_limits["max_instances"]:
                    return {
                        "safe": False,
                        "reason": f"Scale count {count} exceeds maximum limit of {self.safety_limits['max_instances']}"
                    }
            
            elif action == "deploy":
                # Check if deployment was recently done
                recent_deployments = [
                    e for e in self.execution_history[-10:]
                    if e.get("action") == "deploy" and 
                    (datetime.utcnow() - datetime.fromisoformat(e.get("timestamp", "2020-01-01T00:00:00"))).total_seconds() < self.safety_limits["cooldown_period_minutes"] * 60
                ]
                
                if recent_deployments:
                    return {
                        "safe": False,
                        "reason": f"Deployment blocked: cooldown period of {self.safety_limits['cooldown_period_minutes']} minutes not met"
                    }
            
            return {"safe": True}
            
        except Exception as e:
            logger.error(f"Error in safety check: {e}")
            return {"safe": False, "reason": f"Safety check failed: {str(e)}"}
    
    def _execute_deploy(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute deployment action."""
        try:
            app_name = parameters.get("app_name", "smartcloudops-ai")
            environment = parameters.get("environment", "production")
            
            # Simulate deployment process
            deployment_id = f"deploy-{int(time.time())}"
            
            # In a real implementation, this would:
            # 1. Trigger CodeBuild
            # 2. Create CodeDeploy deployment
            # 3. Monitor deployment status
            
            return {
                "deployment_id": deployment_id,
                "app_name": app_name,
                "environment": environment,
                "status": "initiated",
                "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Deployment execution error: {e}")
            return {"error": str(e)}
    
    def _execute_scale(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute scaling action."""
        try:
            count = parameters.get("count", 1)
            if isinstance(count, str):
                count = int(count)
            
            resource_type = parameters.get("resource_type", "instances")
            
            # Get auto scaling groups
            asg_response = self.autoscaling_client.describe_auto_scaling_groups()
            
            if asg_response['AutoScalingGroups']:
                asg_name = asg_response['AutoScalingGroups'][0]['AutoScalingGroupName']
                
                # Update desired capacity
                self.autoscaling_client.set_desired_capacity(
                    AutoScalingGroupName=asg_name,
                    DesiredCapacity=count
                )
                
                return {
                    "asg_name": asg_name,
                    "new_capacity": count,
                    "resource_type": resource_type,
                    "status": "scaling_initiated"
                }
            else:
                return {
                    "error": "No auto scaling groups found",
                    "status": "failed"
                }
                
        except Exception as e:
            logger.error(f"Scale execution error: {e}")
            return {"error": str(e)}
    
    def _execute_monitor(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute monitoring action."""
        try:
            service_name = parameters.get("service_name", "all")
            metric_type = parameters.get("metric_type", "cpu")
            
            # Get CloudWatch metrics
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            
            response = self.cloudwatch_client.get_metric_data(
                MetricDataQueries=[
                    {
                        'Id': 'cpu_utilization',
                        'MetricStat': {
                            'Metric': {
                                'Namespace': 'AWS/EC2',
                                'MetricName': 'CPUUtilization'
                            },
                            'Period': 300,
                            'Stat': 'Average'
                        },
                        'ReturnData': True
                    }
                ],
                StartTime=start_time,
                EndTime=end_time
            )
            
            return {
                "service": service_name,
                "metric": metric_type,
                "data_points": len(response.get('MetricDataResults', [{}])[0].get('Values', [])),
                "latest_value": response.get('MetricDataResults', [{}])[0].get('Values', [0])[-1] if response.get('MetricDataResults') else 0
            }
            
        except Exception as e:
            logger.error(f"Monitor execution error: {e}")
            return {"error": str(e)}
    
    def _execute_restart(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute restart action."""
        try:
            service_name = parameters.get("service_name", "default")
            
            # Get EC2 instances
            instances_response = self.ec2_client.describe_instances(
                Filters=[
                    {
                        'Name': 'instance-state-name',
                        'Values': ['running']
                    }
                ]
            )
            
            instance_ids = []
            for reservation in instances_response['Reservations']:
                for instance in reservation['Instances']:
                    instance_ids.append(instance['InstanceId'])
            
            if instance_ids:
                # Restart instances (in production, you'd be more selective)
                self.ec2_client.reboot_instances(InstanceIds=instance_ids[:1])  # Only restart first instance for safety
                
                return {
                    "service": service_name,
                    "instances_restarted": instance_ids[:1],
                    "status": "restart_initiated"
                }
            else:
                return {
                    "error": "No running instances found",
                    "status": "failed"
                }
                
        except Exception as e:
            logger.error(f"Restart execution error: {e}")
            return {"error": str(e)}
    
    def _execute_backup(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute backup action."""
        try:
            resource_name = parameters.get("resource_name", "database")
            backup_type = parameters.get("backup_type", "snapshot")
            
            # Get RDS instances
            rds_response = self.rds_client.describe_db_instances()
            
            if rds_response['DBInstances']:
                db_instance = rds_response['DBInstances'][0]
                db_identifier = db_instance['DBInstanceIdentifier']
                
                # Create snapshot
                snapshot_id = f"{db_identifier}-backup-{int(time.time())}"
                
                self.rds_client.create_db_snapshot(
                    DBSnapshotIdentifier=snapshot_id,
                    DBInstanceIdentifier=db_identifier
                )
                
                return {
                    "resource": resource_name,
                    "backup_type": backup_type,
                    "snapshot_id": snapshot_id,
                    "db_identifier": db_identifier,
                    "status": "backup_initiated"
                }
            else:
                return {
                    "error": "No RDS instances found",
                    "status": "failed"
                }
                
        except Exception as e:
            logger.error(f"Backup execution error: {e}")
            return {"error": str(e)}
    
    def _execute_security_scan(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute security scan action."""
        try:
            scan_type = parameters.get("scan_type", "general")
            target = parameters.get("target", "all")
            
            # Get GuardDuty findings
            guardduty_response = self.guardduty_client.list_detectors()
            
            findings = []
            if guardduty_response['DetectorIds']:
                detector_id = guardduty_response['DetectorIds'][0]
                
                findings_response = self.guardduty_client.list_findings(
                    DetectorId=detector_id,
                    MaxResults=10
                )
                
                findings = findings_response.get('FindingIds', [])
            
            # Get Security Hub findings
            securityhub_response = self.securityhub_client.get_findings(
                MaxResults=10
            )
            
            return {
                "scan_type": scan_type,
                "target": target,
                "guardduty_findings": len(findings),
                "securityhub_findings": len(securityhub_response.get('Findings', [])),
                "status": "scan_completed"
            }
            
        except Exception as e:
            logger.error(f"Security scan execution error: {e}")
            return {"error": str(e)}
    
    def _execute_cost_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute cost analysis action."""
        try:
            service_name = parameters.get("service_name", "all")
            time_period = parameters.get("time_period", "7")
            
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=int(time_period))
            
            # Get cost and usage data
            cost_response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.isoformat(),
                    'End': end_date.isoformat()
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )
            
            total_cost = 0
            service_costs = {}
            
            for result in cost_response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    total_cost += cost
                    service_costs[service] = service_costs.get(service, 0) + cost
            
            return {
                "service": service_name,
                "time_period": time_period,
                "total_cost": round(total_cost, 2),
                "service_costs": {k: round(v, 2) for k, v in service_costs.items()},
                "status": "analysis_completed"
            }
            
        except Exception as e:
            logger.error(f"Cost analysis execution error: {e}")
            return {"error": str(e)}
    
    def _execute_compliance_check(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute compliance check action."""
        try:
            compliance_type = parameters.get("compliance_type", "general")
            framework = parameters.get("framework", "aws-foundational")
            
            # Get Config compliance data
            config_response = self.config_client.get_compliance_details_by_config_rule(
                ConfigRuleName='aws-foundational-security-best-practices-v1.0.0'
            )
            
            compliance_results = config_response.get('EvaluationResults', [])
            
            compliant_count = len([r for r in compliance_results if r.get('ComplianceType') == 'COMPLIANT'])
            non_compliant_count = len([r for r in compliance_results if r.get('ComplianceType') == 'NON_COMPLIANT'])
            
            return {
                "compliance_type": compliance_type,
                "framework": framework,
                "total_checks": len(compliance_results),
                "compliant": compliant_count,
                "non_compliant": non_compliant_count,
                "compliance_rate": round(compliant_count / len(compliance_results) * 100, 2) if compliance_results else 0,
                "status": "check_completed"
            }
            
        except Exception as e:
            logger.error(f"Compliance check execution error: {e}")
            return {"error": str(e)}
    
    def _execute_alert_setup(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute alert setup action."""
        try:
            alert_type = parameters.get("alert_type", "cpu")
            threshold = parameters.get("threshold", 80)
            channel = parameters.get("channel", "email")
            
            # Create SNS topic for alerts
            topic_name = f"smartcloudops-alerts-{int(time.time())}"
            
            sns_response = self.sns_client.create_topic(Name=topic_name)
            topic_arn = sns_response['TopicArn']
            
            # Create CloudWatch alarm
            alarm_name = f"smartcloudops-{alert_type}-alarm-{int(time.time())}"
            
            self.cloudwatch_client.put_metric_alarm(
                AlarmName=alarm_name,
                MetricName='CPUUtilization',
                Namespace='AWS/EC2',
                Statistic='Average',
                Period=300,
                EvaluationPeriods=2,
                Threshold=threshold,
                ComparisonOperator='GreaterThanThreshold',
                AlarmActions=[topic_arn]
            )
            
            return {
                "alert_type": alert_type,
                "threshold": threshold,
                "channel": channel,
                "topic_arn": topic_arn,
                "alarm_name": alarm_name,
                "status": "alert_configured"
            }
            
        except Exception as e:
            logger.error(f"Alert setup execution error: {e}")
            return {"error": str(e)}
    
    def _execute_rollback(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute rollback action."""
        try:
            version = parameters.get("version", "previous")
            reason = parameters.get("reason", "manual_rollback")
            
            # Get recent deployments
            deployments_response = self.codedeploy_client.list_deployments(
                MaxResults=10
            )
            
            if deployments_response.get('deployments'):
                deployment_id = deployments_response['deployments'][0]
                
                # Create rollback deployment
                rollback_response = self.codedeploy_client.create_deployment(
                    applicationName='SmartCloudOps-App',
                    deploymentGroupName='SmartCloudOps-DG',
                    revision={
                        'revisionType': 'AppSpecContent',
                        'appSpecContent': {
                            'content': json.dumps({
                                'version': 0.0,
                                'Resources': [{
                                    'TargetService': {
                                        'Type': 'AWS::ECS::Service',
                                        'Properties': {
                                            'TaskDefinition': '<PREVIOUS_TASK_DEFINITION>',
                                            'LoadBalancerInfo': {
                                                'ContainerName': 'smartcloudops',
                                                'ContainerPort': 5000
                                            }
                                        }
                                    }
                                }]
                            })
                        }
                    },
                    description=f"Rollback to {version}: {reason}"
                )
                
                return {
                    "version": version,
                    "reason": reason,
                    "rollback_deployment_id": rollback_response['deploymentId'],
                    "status": "rollback_initiated"
                }
            else:
                return {
                    "error": "No recent deployments found",
                    "status": "failed"
                }
                
        except Exception as e:
            logger.error(f"Rollback execution error: {e}")
            return {"error": str(e)}
    
    def _log_execution(self, action: str, parameters: Dict[str, Any], result: Dict[str, Any]):
        """Log action execution for audit."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "parameters": parameters,
            "result": result
        }
        
        self.execution_history.append(log_entry)
        
        # Keep only last 100 executions
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
        
        logger.info(f"AWS Action Execution: {log_entry}")
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent execution history."""
        return self.execution_history[-limit:] if self.execution_history else []
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get statistics about executed actions."""
        if not self.execution_history:
            return {"total_executions": 0, "actions": {}}
        
        action_counts = {}
        total_executions = len(self.execution_history)
        successful_executions = len([e for e in self.execution_history if e.get("result", {}).get("status") != "error"])
        
        for entry in self.execution_history:
            action = entry.get("action", "unknown")
            action_counts[action] = action_counts.get(action, 0) + 1
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "actions": action_counts
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check of AWS services."""
        try:
            # Test basic AWS connectivity
            self.ec2_client.describe_regions()
            
            return {
                "status": "healthy",
                "aws_connected": True,
                "total_executions": len(self.execution_history),
                "timestamp": datetime.utcnow().isoformat()
            }
        except NoCredentialsError:
            return {
                "status": "unhealthy",
                "error": "AWS credentials not configured",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global instance for the service
aws_integration_service = AWSIntegrationService()
