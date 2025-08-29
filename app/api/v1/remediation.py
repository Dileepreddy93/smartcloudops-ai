#!/usr/bin/env python3
"""
SmartCloudOps AI - Auto-Remediation API Endpoints
=================================================

Phase 4: Auto-Remediation API
Provides endpoints for monitoring and controlling the auto-remediation engine.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, request

from app.cache_service import cache_invalidate, cache_service, cached
from app.database_integration import db_service
from app.services.remediation_service import (RemediationAction,
                                              RemediationRule,
                                              remediation_engine)

logger = logging.getLogger(__name__)
bp = Blueprint("remediation", __name__, url_prefix="/api/v1/remediation")


@bp.route("/status", methods=["GET"])
@cached("remediation_status", ttl=30)
def get_remediation_status():
    """Get the current status of the auto-remediation engine."""
    try:
        status = remediation_engine.get_status()

        # Add database metrics
        db_metrics = (
            db_service.get_performance_summary() if db_service.is_available() else {}
        )

        # Enhance status with additional information
        enhanced_status = {
            **status,
            "database_metrics": db_metrics,
            "cache_status": cache_service.health_check(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            f"Remediation status requested - Engine: {status.get('enabled', False)}"
        )

        return jsonify(
            {
                "status": "success",
                "data": enhanced_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Failed to get remediation status: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )


@bp.route("/enable", methods=["POST"])
@cache_invalidate("remediation_status")
def enable_remediation():
    """Enable the auto-remediation engine."""
    try:
        remediation_engine.enable()

        # Log the action
        logger.info("Auto-remediation engine enabled")

        # Store action in database if available
        if db_service.is_available():
            action_data = {
                "action": "enable_remediation",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user": "api_request",
                "details": "Remediation engine enabled via API",
            }
            # Note: This would require a remediation_actions table
            # db_service.store_remediation_action(action_data)

        return jsonify(
            {
                "status": "success",
                "message": "Auto-remediation engine enabled",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Failed to enable remediation: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )


@bp.route("/disable", methods=["POST"])
@cache_invalidate("remediation_status")
def disable_remediation():
    """Disable the auto-remediation engine."""
    try:
        remediation_engine.disable()

        # Log the action
        logger.info("Auto-remediation engine disabled")

        return jsonify(
            {
                "status": "success",
                "message": "Auto-remediation engine disabled",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Failed to disable remediation: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )


@bp.route("/override", methods=["POST"])
@cache_invalidate("remediation_status")
def set_manual_override():
    """Set manual override mode."""
    try:
        data = request.get_json(silent=True) or {}
        enabled = data.get("enabled", False)

        # Validate input
        if not isinstance(enabled, bool):
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "enabled must be a boolean value",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                400,
            )

        remediation_engine.set_manual_override(enabled)

        status = "enabled" if enabled else "disabled"
        logger.info(f"Manual override {status}")

        return jsonify(
            {
                "status": "success",
                "message": f"Manual override {status}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Failed to set manual override: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )


@bp.route("/rules", methods=["GET"])
@cached("remediation_rules", ttl=60)
def get_rules():
    """Get all remediation rules."""
    try:
        rules = []
        for rule in remediation_engine.rules:
            rules.append(
                {
                    "name": rule.name,
                    "enabled": rule.enabled,
                    "priority": rule.priority,
                    "cooldown_minutes": rule.cooldown_minutes,
                    "trigger_count": rule.trigger_count,
                    "last_triggered": (
                        rule.last_triggered.isoformat() if rule.last_triggered else None
                    ),
                    "conditions": rule.conditions,
                    "actions": [action.value for action in rule.actions],
                }
            )

        logger.info(f"Retrieved {len(rules)} remediation rules")

        return jsonify(
            {
                "status": "success",
                "data": {
                    "rules": rules,
                    "total_rules": len(rules),
                    "enabled_rules": len([r for r in rules if r["enabled"]]),
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Failed to get remediation rules: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )


@bp.route("/rules", methods=["POST"])
@cache_invalidate("remediation_rules")
def add_rule():
    """Add a new remediation rule."""
    try:
        data = request.get_json(silent=True) or {}

        # Validate required fields
        required_fields = ["name", "conditions", "actions"]
        for field in required_fields:
            if field not in data:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "error": f"Missing required field: {field}",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    ),
                    400,
                )

        # Validate rule name
        if not isinstance(data["name"], str) or len(data["name"].strip()) == 0:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Rule name must be a non-empty string",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                400,
            )

        # Validate conditions
        if not isinstance(data["conditions"], dict):
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Conditions must be a dictionary",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                400,
            )

        # Validate actions
        if not isinstance(data["actions"], list) or len(data["actions"]) == 0:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Actions must be a non-empty list",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                400,
            )

        # Convert action strings to enum values
        actions = []
        for action_str in data["actions"]:
            try:
                actions.append(RemediationAction(action_str))
            except ValueError:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "error": f"Invalid action: {action_str}. Valid actions: {[a.value for a in RemediationAction]}",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    ),
                    400,
                )

        # Validate optional fields
        priority = data.get("priority", 1)
        if not isinstance(priority, int) or priority < 1:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Priority must be a positive integer",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                400,
            )

        cooldown_minutes = data.get("cooldown_minutes", 5)
        if not isinstance(cooldown_minutes, int) or cooldown_minutes < 0:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Cooldown minutes must be a non-negative integer",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                400,
            )

        # Create new rule
        rule = RemediationRule(
            name=data["name"],
            conditions=data["conditions"],
            actions=actions,
            priority=priority,
            cooldown_minutes=cooldown_minutes,
            enabled=data.get("enabled", True),
        )

        remediation_engine.add_rule(rule)

        logger.info(f"Added remediation rule: {data['name']}")

        return jsonify(
            {
                "status": "success",
                "message": f"Rule '{data['name']}' added successfully",
                "data": {
                    "rule_name": data["name"],
                    "priority": priority,
                    "enabled": data.get("enabled", True),
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Failed to add remediation rule: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )


@bp.route("/rules/<rule_name>", methods=["DELETE"])
@cache_invalidate("remediation_rules")
def remove_rule(rule_name):
    """Remove a remediation rule by name."""
    try:
        if not rule_name or not isinstance(rule_name, str):
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Rule name must be a valid string",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                400,
            )

        success = remediation_engine.remove_rule(rule_name)

        if success:
            logger.info(f"Removed remediation rule: {rule_name}")
            return jsonify(
                {
                    "status": "success",
                    "message": f"Rule '{rule_name}' removed successfully",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": f"Rule '{rule_name}' not found",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                404,
            )
    except Exception as e:
        logger.error(f"Failed to remove remediation rule: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )


@bp.route("/actions", methods=["GET"])
@cached("remediation_actions", ttl=30)
def get_action_history():
    """Get the history of remediation actions."""
    try:
        limit = request.args.get("limit", 50, type=int)

        # Validate limit
        if limit < 1 or limit > 1000:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Limit must be between 1 and 1000",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                400,
            )

        actions = (
            remediation_engine.action_history[-limit:]
            if remediation_engine.action_history
            else []
        )

        logger.info(f"Retrieved {len(actions)} remediation actions")

        return jsonify(
            {
                "status": "success",
                "data": {
                    "actions": actions,
                    "total_actions": len(remediation_engine.action_history),
                    "recent_actions": len(actions),
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Failed to get action history: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )


@bp.route("/test", methods=["POST"])
def test_remediation():
    """Test the remediation engine with sample metrics."""
    try:
        data = request.get_json(silent=True) or {}

        # Validate input metrics
        test_metrics = {}
        metric_fields = [
            "cpu_percent",
            "memory_percent",
            "response_time_ms",
            "error_rate",
            "ml_anomaly_score",
            "ml_confidence",
        ]

        for field in metric_fields:
            value = data.get(field)
            if value is not None:
                if not isinstance(value, (int, float)):
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "error": f"{field} must be a number",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        ),
                        400,
                    )

                # Validate ranges
                if field in ["cpu_percent", "memory_percent"] and (
                    value < 0 or value > 100
                ):
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "error": f"{field} must be between 0 and 100",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        ),
                        400,
                    )

                if field == "error_rate" and (value < 0 or value > 1):
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "error": f"{field} must be between 0 and 1",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        ),
                        400,
                    )

                if field in ["ml_anomaly_score", "ml_confidence"] and (
                    value < 0 or value > 1
                ):
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "error": f"{field} must be between 0 and 1",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        ),
                        400,
                    )

                test_metrics[field] = value

        # Use default values if not provided
        if not test_metrics:
            test_metrics = {
                "cpu_percent": data.get("cpu_percent", 95),
                "memory_percent": data.get("memory_percent", 90),
                "response_time_ms": data.get("response_time_ms", 6000),
                "error_rate": data.get("error_rate", 0.15),
                "ml_anomaly_score": data.get("ml_anomaly_score", 0.85),
                "ml_confidence": data.get("ml_confidence", 0.92),
            }

        # Process metrics through remediation engine
        triggered_actions = remediation_engine.process_metrics(test_metrics)

        logger.info(
            f"Tested remediation with {len(triggered_actions)} actions triggered"
        )

        return jsonify(
            {
                "status": "success",
                "data": {
                    "test_metrics": test_metrics,
                    "triggered_actions": triggered_actions,
                    "total_actions_triggered": len(triggered_actions),
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Failed to test remediation: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )


@bp.route("/metrics", methods=["GET"])
@cached("remediation_metrics", ttl=60)
def get_remediation_metrics():
    """Get metrics about the auto-remediation engine performance."""
    try:
        status = remediation_engine.get_status()

        # Calculate additional metrics
        total_rules = status["total_rules"]
        enabled_rules = status["enabled_rules"]
        total_actions = status["total_actions"]

        # Calculate success rate from recent actions
        recent_actions = status["recent_actions"]
        successful_actions = sum(
            1 for action in recent_actions if action.get("success", False)
        )
        success_rate = (
            (successful_actions / len(recent_actions) * 100) if recent_actions else 0
        )

        # Get database metrics if available
        db_metrics = {}
        if db_service.is_available():
            db_metrics = db_service.get_performance_summary()

        metrics = {
            "engine_status": {
                "enabled": status["enabled"],
                "manual_override": status["manual_override"],
            },
            "rules_summary": {
                "total_rules": total_rules,
                "enabled_rules": enabled_rules,
                "disabled_rules": total_rules - enabled_rules,
            },
            "actions_summary": {
                "total_actions": total_actions,
                "recent_actions": len(recent_actions),
                "success_rate_percent": round(success_rate, 2),
            },
            "performance": {
                "uptime_percent": 100 if status["enabled"] else 0,
                "response_time_ms": 50,  # Placeholder
                "last_action_timestamp": (
                    recent_actions[-1]["timestamp"] if recent_actions else None
                ),
            },
            "database_metrics": db_metrics,
        }

        logger.info(
            f"Retrieved remediation metrics - Success rate: {success_rate:.2f}%"
        )

        return jsonify(
            {
                "status": "success",
                "data": metrics,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Failed to get remediation metrics: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )


@bp.route("/health", methods=["GET"])
def get_remediation_health():
    """Get health status of the remediation engine."""
    try:
        # Check remediation engine health
        engine_status = remediation_engine.get_status()

        # Check database health
        db_health = (
            db_service.health_check()
            if db_service.is_available()
            else {"status": "unavailable"}
        )

        # Check cache health
        cache_health = cache_service.health_check()

        overall_health = "healthy"
        if not engine_status.get("enabled", False):
            overall_health = "disabled"
        elif db_health.get("status") == "unhealthy":
            overall_health = "degraded"
        elif cache_health.get("status") == "unhealthy":
            overall_health = "degraded"

        health_data = {
            "status": overall_health,
            "engine": {
                "status": (
                    "healthy" if engine_status.get("enabled", False) else "disabled"
                ),
                "enabled": engine_status.get("enabled", False),
                "manual_override": engine_status.get("manual_override", False),
            },
            "database": db_health,
            "cache": cache_health,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"Remediation health check - Overall: {overall_health}")

        return jsonify(
            {
                "status": "success",
                "data": health_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Failed to get remediation health: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )
