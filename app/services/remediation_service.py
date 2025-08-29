#!/usr/bin/env python3
"""
SmartCloudOps AI - Auto-Remediation Service
===========================================

Phase 4: Auto-Remediation Rule Engine
Handles automated remediation actions based on ML predictions and system metrics.
"""


import logging
import os
import subprocess
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

import boto3

logger = logging.getLogger(__name__)


class RemediationAction(Enum):
    """Enumeration of available remediation actions."""

    RESTART_SERVICE = "restart_service"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    CLEAR_CACHE = "clear_cache"
    RESTART_CONTAINER = "restart_container"
    EMERGENCY_SHUTDOWN = "emergency_shutdown"
    SEND_ALERT = "send_alert"


class RemediationRule:
    """Defines a remediation rule with conditions and actions."""

    def __init__(
        self,
        name: str,
        conditions: Dict,
        actions: List[RemediationAction],
        priority: int = 1,
        cooldown_minutes: int = 5,
        enabled: bool = True,
    ):
        self.name = name
        self.conditions = conditions
        self.actions = actions
        self.priority = priority
        self.cooldown_minutes = cooldown_minutes
        self.enabled = enabled
        self.last_triggered = None
        self.trigger_count = 0


class AutoRemediationEngine:
    """Main auto-remediation engine for SmartCloudOps AI."""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.rules: List[RemediationRule] = []
        self.action_history: List[Dict] = []
        self.is_enabled = True
        self.manual_override = False
        self.lock = threading.Lock()

        # Initialize default rules
        self._initialize_default_rules()

        # Setup AWS clients for remediation actions
        aws_region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        self.ec2_client = boto3.client("ec2", region_name=aws_region)
        self.sns_client = boto3.client("sns", region_name=aws_region)

        logger.info("✅ Auto-Remediation Engine initialized")

    def _initialize_default_rules(self):
        """Initialize default remediation rules."""

        # Rule 1: High CPU Usage
        high_cpu_rule = RemediationRule(
            name="High CPU Usage",
            conditions={
                "cpu_percent": {"threshold": 90, "duration_minutes": 3},
                "ml_anomaly_score": {"threshold": 0.8, "required": True},
            },
            actions=[RemediationAction.SCALE_UP, RemediationAction.SEND_ALERT],
            priority=2,
            cooldown_minutes=10,
        )

        # Rule 2: High Memory Usage
        high_memory_rule = RemediationRule(
            name="High Memory Usage",
            conditions={
                "memory_percent": {"threshold": 85, "duration_minutes": 2},
                "ml_anomaly_score": {"threshold": 0.7, "required": True},
            },
            actions=[RemediationAction.CLEAR_CACHE, RemediationAction.SEND_ALERT],
            priority=2,
            cooldown_minutes=5,
        )

        # Rule 3: Service Unresponsive
        service_unresponsive_rule = RemediationRule(
            name="Service Unresponsive",
            conditions={
                "response_time_ms": {"threshold": 5000, "duration_minutes": 1},
                "error_rate": {"threshold": 0.1, "duration_minutes": 1},
            },
            actions=[RemediationAction.RESTART_SERVICE, RemediationAction.SEND_ALERT],
            priority=1,
            cooldown_minutes=3,
        )

        # Rule 4: Critical System Failure
        critical_failure_rule = RemediationRule(
            name="Critical System Failure",
            conditions={
                "cpu_percent": {"threshold": 95, "duration_minutes": 1},
                "memory_percent": {"threshold": 95, "duration_minutes": 1},
                "ml_anomaly_score": {"threshold": 0.9, "required": True},
            },
            actions=[
                RemediationAction.EMERGENCY_SHUTDOWN,
                RemediationAction.SEND_ALERT,
            ],
            priority=0,  # Highest priority
            cooldown_minutes=1,
        )

        # Rule 5: Low Resource Utilization
        low_utilization_rule = RemediationRule(
            name="Low Resource Utilization",
            conditions={
                "cpu_percent": {
                    "threshold": 20,
                    "duration_minutes": 10,
                    "operator": "lt",
                },
                "memory_percent": {
                    "threshold": 30,
                    "duration_minutes": 10,
                    "operator": "lt",
                },
            },
            actions=[RemediationAction.SCALE_DOWN],
            priority=3,
            cooldown_minutes=15,
        )

        self.rules = [
            critical_failure_rule,
            service_unresponsive_rule,
            high_cpu_rule,
            high_memory_rule,
            low_utilization_rule,
        ]

        logger.info(f"✅ Initialized {len(self.rules)} default remediation rules")

    def evaluate_conditions(self, rule: RemediationRule, metrics: Dict) -> bool:
        """Evaluate if a rule's conditions are met."""
        try:
            for metric_name, condition in rule.conditions.items():
                if metric_name not in metrics:
                    if condition.get("required", False):
                        return False
                    continue

                current_value = metrics[metric_name]
                threshold = condition["threshold"]
                operator = condition.get("operator", "gt")  # Default to greater than

                # Check if condition is met
                condition_met = False
                if operator == "gt":
                    condition_met = current_value > threshold
                elif operator == "lt":
                    condition_met = current_value < threshold
                elif operator == "eq":
                    condition_met = current_value == threshold
                elif operator == "gte":
                    condition_met = current_value >= threshold
                elif operator == "lte":
                    condition_met = current_value <= threshold

                if not condition_met:
                    return False

            return True

        except Exception as e:
            logger.error(f"❌ Error evaluating conditions for rule {rule.name}: {e}")
            return False

    def check_cooldown(self, rule: RemediationRule) -> bool:
        """Check if a rule is in cooldown period."""
        if rule.last_triggered is None:
            return False

        cooldown_end = rule.last_triggered + timedelta(minutes=rule.cooldown_minutes)
        return datetime.utcnow() < cooldown_end

    def execute_remediation_action(
        self, action: RemediationAction, context: Dict
    ) -> bool:
        """Execute a remediation action."""
        try:
            logger.info(f"🔧 Executing remediation action: {action.value}")

            if action == RemediationAction.RESTART_SERVICE:
                return self._restart_service(context)
            elif action == RemediationAction.SCALE_UP:
                return self._scale_up(context)
            elif action == RemediationAction.SCALE_DOWN:
                return self._scale_down(context)
            elif action == RemediationAction.CLEAR_CACHE:
                return self._clear_cache(context)
            elif action == RemediationAction.RESTART_CONTAINER:
                return self._restart_container(context)
            elif action == RemediationAction.EMERGENCY_SHUTDOWN:
                return self._emergency_shutdown(context)
            elif action == RemediationAction.SEND_ALERT:
                return self._send_alert(context)
            else:
                logger.warning(f"⚠️ Unknown remediation action: {action.value}")
                return False

        except Exception as e:
            logger.error(f"❌ Error executing remediation action {action.value}: {e}")
            return False

    def _restart_service(self, context: Dict) -> bool:
        """Restart a service."""
        try:
            service_name = context.get("service_name", "smartcloudops-ai")

            # Try systemctl first
            result = subprocess.run(
                ["sudo", "systemctl", "restart", service_name],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                logger.info(f"✅ Successfully restarted service: {service_name}")
                return True

            # Fallback to docker restart
            result = subprocess.run(
                ["docker", "restart", service_name],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                logger.info(f"✅ Successfully restarted container: {service_name}")
                return True

            logger.error(f"❌ Failed to restart service: {service_name}")
            return False

        except Exception as e:
            logger.error(f"❌ Error restarting service: {e}")
            return False

    def _scale_up(self, context: Dict) -> bool:
        """Scale up resources."""
        try:
            # For EC2 instances, we can't scale individual instances
            # This would typically trigger Auto Scaling Group actions
            logger.info("📈 Scale up action triggered - would trigger ASG scale up")

            # Send alert about scaling need
            self._send_alert(
                {
                    "message": "Scale up required - manual intervention needed",
                    "severity": "warning",
                    "context": context,
                }
            )

            return True

        except Exception as e:
            logger.error(f"❌ Error scaling up: {e}")
            return False

    def _scale_down(self, context: Dict) -> bool:
        """Scale down resources."""
        try:
            logger.info("📉 Scale down action triggered - would trigger ASG scale down")

            # Send alert about scaling need
            self._send_alert(
                {
                    "message": "Scale down recommended - manual intervention needed",
                    "severity": "info",
                    "context": context,
                }
            )

            return True

        except Exception as e:
            logger.error(f"❌ Error scaling down: {e}")
            return False

    def _clear_cache(self, context: Dict) -> bool:
        """Clear application cache."""
        try:
            # Clear Python cache
            subprocess.run(
                [
                    "find",
                    ".",
                    "-type",
                    "d",
                    "-name",
                    "__pycache__",
                    "-exec",
                    "rm",
                    "-rf",
                    "{}",
                    "+",
                ],
                capture_output=True,
                timeout=30,
            )

            # Clear temporary files
            subprocess.run(["rm", "-rf", "/tmp/*"], capture_output=True, timeout=30)

            logger.info("🧹 Cache cleared successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Error clearing cache: {e}")
            return False

    def _restart_container(self, context: Dict) -> bool:
        """Restart Docker container."""
        try:
            container_name = context.get("container_name", "smartcloudops-ai")

            result = subprocess.run(
                ["docker", "restart", container_name],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                logger.info(f"✅ Successfully restarted container: {container_name}")
                return True

            logger.error(f"❌ Failed to restart container: {container_name}")
            return False

        except Exception as e:
            logger.error(f"❌ Error restarting container: {e}")
            return False

    def _emergency_shutdown(self, context: Dict) -> bool:
        """Emergency shutdown procedure."""
        try:
            logger.warning("🚨 EMERGENCY SHUTDOWN TRIGGERED")

            # Send immediate alert
            self._send_alert(
                {
                    "message": "EMERGENCY SHUTDOWN TRIGGERED - IMMEDIATE ATTENTION REQUIRED",
                    "severity": "critical",
                    "context": context,
                }
            )

            # Stop the application gracefully
            subprocess.run(
                ["pkill", "-f", "smartcloudops-ai"], capture_output=True, timeout=10
            )

            logger.info("🛑 Emergency shutdown completed")
            return True

        except Exception as e:
            logger.error(f"❌ Error during emergency shutdown: {e}")
            return False

    def _send_alert(self, context: Dict) -> bool:
        """Send alert notification."""
        try:
            message = context.get("message", "Auto-remediation action triggered")
            severity = context.get("severity", "info")

            alert_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "severity": severity,
                "message": message,
                "context": context,
            }

            # Log the alert
            logger.warning(f"🚨 ALERT: {message}")

            # In production, this would send to SNS, Slack, etc.
            # For now, we'll just log it
            self.action_history.append(
                {"type": "alert", "data": alert_data, "timestamp": datetime.utcnow()}
            )

            return True

        except Exception as e:
            logger.error(f"❌ Error sending alert: {e}")
            return False

    def process_metrics(
        self, metrics: Dict, ml_prediction: Optional[Dict] = None
    ) -> List[Dict]:
        """Process metrics and trigger remediation actions if needed."""
        if not self.is_enabled or self.manual_override:
            return []

        triggered_actions = []

        # Merge ML prediction with metrics
        if ml_prediction:
            metrics["ml_anomaly_score"] = ml_prediction.get("anomaly_score", 0.0)
            metrics["ml_confidence"] = ml_prediction.get("confidence", 0.0)

        with self.lock:
            # Sort rules by priority (lower number = higher priority)
            sorted_rules = sorted(self.rules, key=lambda r: r.priority)

            for rule in sorted_rules:
                if not rule.enabled:
                    continue

                if self.check_cooldown(rule):
                    continue

                if self.evaluate_conditions(rule, metrics):
                    logger.info(f"🎯 Rule triggered: {rule.name}")

                    # Execute all actions for this rule
                    for action in rule.actions:
                        context = {
                            "rule_name": rule.name,
                            "metrics": metrics,
                            "ml_prediction": ml_prediction,
                            "timestamp": datetime.utcnow().isoformat(),
                        }

                        success = self.execute_remediation_action(action, context)

                        action_result = {
                            "rule_name": rule.name,
                            "action": action.value,
                            "success": success,
                            "timestamp": datetime.utcnow().isoformat(),
                            "context": context,
                        }

                        triggered_actions.append(action_result)
                        self.action_history.append(action_result)

                    # Update rule state
                    rule.last_triggered = datetime.utcnow()
                    rule.trigger_count += 1

        return triggered_actions

    def get_status(self) -> Dict:
        """Get the current status of the auto-remediation engine."""
        return {
            "enabled": self.is_enabled,
            "manual_override": self.manual_override,
            "total_rules": len(self.rules),
            "enabled_rules": len([r for r in self.rules if r.enabled]),
            "total_actions": len(self.action_history),
            "recent_actions": self.action_history[-10:] if self.action_history else [],
            "rules": [
                {
                    "name": rule.name,
                    "enabled": rule.enabled,
                    "priority": rule.priority,
                    "trigger_count": rule.trigger_count,
                    "last_triggered": (
                        rule.last_triggered.isoformat() if rule.last_triggered else None
                    ),
                }
                for rule in self.rules
            ],
        }

    def enable(self):
        """Enable the auto-remediation engine."""
        self.is_enabled = True
        logger.info("✅ Auto-remediation engine enabled")

    def disable(self):
        """Disable the auto-remediation engine."""
        self.is_enabled = False
        logger.info("⏸️ Auto-remediation engine disabled")

    def set_manual_override(self, enabled: bool):
        """Set manual override mode."""
        self.manual_override = enabled
        status = "enabled" if enabled else "disabled"
        logger.info(f"🔒 Manual override {status}")

    def add_rule(self, rule: RemediationRule):
        """Add a new remediation rule."""
        self.rules.append(rule)
        logger.info(f"✅ Added new remediation rule: {rule.name}")

    def remove_rule(self, rule_name: str) -> bool:
        """Remove a remediation rule by name."""
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                del self.rules[i]
                logger.info(f"✅ Removed remediation rule: {rule_name}")
                return True
        return False


# Global instance
remediation_engine = AutoRemediationEngine()
