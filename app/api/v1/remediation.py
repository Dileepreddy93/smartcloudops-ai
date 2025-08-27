#!/usr/bin/env python3
"""
SmartCloudOps AI - Auto-Remediation API Endpoints
=================================================

Phase 4: Auto-Remediation API
Provides endpoints for monitoring and controlling the auto-remediation engine.
"""

from datetime import datetime

from flask import Blueprint, jsonify, request

from app.services.remediation_service import (RemediationAction,
                                              RemediationRule,
                                              remediation_engine)

bp = Blueprint("remediation", __name__, url_prefix="/api/v1/remediation")


@bp.route("/status", methods=["GET"])
def get_remediation_status():
    """Get the current status of the auto-remediation engine."""
    try:
        status = remediation_engine.get_status()
        return jsonify(
            {
                "status": "success",
                "data": status,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            500,
        )


@bp.route("/enable", methods=["POST"])
def enable_remediation():
    """Enable the auto-remediation engine."""
    try:
        remediation_engine.enable()
        return jsonify(
            {
                "status": "success",
                "message": "Auto-remediation engine enabled",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            500,
        )


@bp.route("/disable", methods=["POST"])
def disable_remediation():
    """Disable the auto-remediation engine."""
    try:
        remediation_engine.disable()
        return jsonify(
            {
                "status": "success",
                "message": "Auto-remediation engine disabled",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            500,
        )


@bp.route("/override", methods=["POST"])
def set_manual_override():
    """Set manual override mode."""
    try:
        data = request.get_json(silent=True) or {}
        enabled = data.get("enabled", False)

        remediation_engine.set_manual_override(enabled)

        status = "enabled" if enabled else "disabled"
        return jsonify(
            {
                "status": "success",
                "message": f"Manual override {status}",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            500,
        )


@bp.route("/rules", methods=["GET"])
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

        return jsonify(
            {
                "status": "success",
                "data": {"rules": rules, "total_rules": len(rules)},
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            500,
        )


@bp.route("/rules", methods=["POST"])
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
                            "timestamp": datetime.utcnow().isoformat(),
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
                            "error": f"Invalid action: {action_str}",
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    ),
                    400,
                )

        # Create new rule
        rule = RemediationRule(
            name=data["name"],
            conditions=data["conditions"],
            actions=actions,
            priority=data.get("priority", 1),
            cooldown_minutes=data.get("cooldown_minutes", 5),
            enabled=data.get("enabled", True),
        )

        remediation_engine.add_rule(rule)

        return jsonify(
            {
                "status": "success",
                "message": f"Rule '{data['name']}' added successfully",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            500,
        )


@bp.route("/rules/<rule_name>", methods=["DELETE"])
def remove_rule(rule_name):
    """Remove a remediation rule by name."""
    try:
        success = remediation_engine.remove_rule(rule_name)

        if success:
            return jsonify(
                {
                    "status": "success",
                    "message": f"Rule '{rule_name}' removed successfully",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": f"Rule '{rule_name}' not found",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ),
                404,
            )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            500,
        )


@bp.route("/actions", methods=["GET"])
def get_action_history():
    """Get the history of remediation actions."""
    try:
        limit = request.args.get("limit", 50, type=int)
        actions = (
            remediation_engine.action_history[-limit:]
            if remediation_engine.action_history
            else []
        )

        return jsonify(
            {
                "status": "success",
                "data": {
                    "actions": actions,
                    "total_actions": len(remediation_engine.action_history),
                    "recent_actions": len(actions),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            500,
        )


@bp.route("/test", methods=["POST"])
def test_remediation():
    """Test the remediation engine with sample metrics."""
    try:
        data = request.get_json(silent=True) or {}

        # Sample metrics for testing
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

        return jsonify(
            {
                "status": "success",
                "data": {
                    "test_metrics": test_metrics,
                    "triggered_actions": triggered_actions,
                    "total_actions_triggered": len(triggered_actions),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            500,
        )


@bp.route("/metrics", methods=["GET"])
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
        }

        return jsonify(
            {
                "status": "success",
                "data": metrics,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            500,
        )
