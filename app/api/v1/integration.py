#!/usr/bin/env python3
"""
SmartCloudOps AI - ML-Remediation Integration API
=================================================

Phase 4: Integration API
Provides endpoints for monitoring and controlling the ML-Remediation integration.
"""

import time
from datetime import datetime

from flask import Blueprint, jsonify, request

from app.services.integration_service import integration_service

bp = Blueprint("integration", __name__, url_prefix="/api/v1/integration")


@bp.route("/status", methods=["GET"])
def get_integration_status():
    """Get the current status of the ML-Remediation integration."""
    try:
        status = integration_service.get_status()
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


@bp.route("/start", methods=["POST"])
def start_integration():
    """Start the ML-Remediation integration monitoring."""
    try:
        integration_service.start_monitoring()
        return jsonify(
            {
                "status": "success",
                "message": "ML-Remediation integration started",
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


@bp.route("/stop", methods=["POST"])
def stop_integration():
    """Stop the ML-Remediation integration monitoring."""
    try:
        integration_service.stop_monitoring()
        return jsonify(
            {
                "status": "success",
                "message": "ML-Remediation integration stopped",
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
def get_recent_metrics():
    """Get recent metrics and ML predictions."""
    try:
        limit = request.args.get("limit", 10, type=int)
        metrics = integration_service.get_recent_metrics(limit)

        return jsonify(
            {
                "status": "success",
                "data": {"metrics": metrics, "total_metrics": len(metrics)},
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


@bp.route("/trigger", methods=["POST"])
def trigger_manual_remediation():
    """Manually trigger remediation with provided metrics."""
    try:
        data = request.get_json(silent=True) or {}

        # Use provided metrics or collect current ones
        if "metrics" in data:
            metrics = data["metrics"]
        else:
            metrics = integration_service._collect_system_metrics()

        # Trigger remediation
        triggered_actions = integration_service.trigger_manual_remediation(metrics)

        return jsonify(
            {
                "status": "success",
                "data": {
                    "metrics": metrics,
                    "triggered_actions": triggered_actions,
                    "total_actions": len(triggered_actions),
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


@bp.route("/config", methods=["GET"])
def get_integration_config():
    """Get the current integration configuration."""
    try:
        config = {
            "monitoring_interval": integration_service.monitoring_interval,
            "confidence_threshold": integration_service.confidence_threshold,
            "buffer_size": integration_service.buffer_size,
        }

        return jsonify(
            {
                "status": "success",
                "data": config,
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


@bp.route("/config", methods=["PUT"])
def update_integration_config():
    """Update the integration configuration."""
    try:
        data = request.get_json(silent=True) or {}

        # Validate configuration
        if "monitoring_interval" in data and data["monitoring_interval"] < 5:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Monitoring interval must be at least 5 seconds",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ),
                400,
            )

        if "confidence_threshold" in data and not (
            0 <= data["confidence_threshold"] <= 1
        ):
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Confidence threshold must be between 0 and 1",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ),
                400,
            )

        if "buffer_size" in data and data["buffer_size"] < 1:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Buffer size must be at least 1",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ),
                400,
            )

        # Update configuration
        integration_service.update_config(data)

        return jsonify(
            {
                "status": "success",
                "message": "Integration configuration updated",
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
def test_integration():
    """Test the integration with sample data."""
    try:
        data = request.get_json(silent=True) or {}

        # Generate test metrics
        test_metrics = {
            "cpu_percent": data.get("cpu_percent", 95),
            "memory_percent": data.get("memory_percent", 90),
            "disk_percent": data.get("disk_percent", 85),
            "response_time_ms": data.get("response_time_ms", 6000),
            "error_rate": data.get("error_rate", 0.15),
            "network_bytes_sent": data.get("network_bytes_sent", 5000),
            "network_bytes_recv": data.get("network_bytes_recv", 8000),
            "memory_available_gb": data.get("memory_available_gb", 0.5),
            "disk_free_gb": data.get("disk_free_gb", 2.0),
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Test ML prediction
        ml_prediction = integration_service._get_ml_prediction(test_metrics)

        # Test remediation
        triggered_actions = integration_service.trigger_manual_remediation(test_metrics)

        return jsonify(
            {
                "status": "success",
                "data": {
                    "test_metrics": test_metrics,
                    "ml_prediction": ml_prediction,
                    "triggered_actions": triggered_actions,
                    "total_actions": len(triggered_actions),
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


@bp.route("/health", methods=["GET"])
def get_integration_health():
    """Get comprehensive health status of the integration."""
    try:
        # Get integration status
        integration_status = integration_service.get_status()

        # Get remediation engine status
        from app.services.remediation_service import remediation_engine

        remediation_status = remediation_engine.get_status()

        # Calculate health metrics
        health_metrics = {
            "integration_running": integration_status["is_running"],
            "remediation_enabled": remediation_status["enabled"],
            "manual_override": remediation_status["manual_override"],
            "total_rules": remediation_status["total_rules"],
            "enabled_rules": remediation_status["enabled_rules"],
            "recent_actions": len(remediation_status["recent_actions"]),
            "last_prediction": integration_status["last_prediction"] is not None,
            "buffer_health": integration_status["buffer_size"] > 0,
        }

        # Convert boolean values to integers for calculation
        health_values = [
            1 if integration_status["is_running"] else 0,
            1 if remediation_status["enabled"] else 0,
            (
                0 if remediation_status["manual_override"] else 1
            ),  # Manual override is good
            1 if remediation_status["total_rules"] > 0 else 0,
            1 if remediation_status["enabled_rules"] > 0 else 0,
            1 if len(remediation_status["recent_actions"]) >= 0 else 0,  # Always true
            1 if integration_status["last_prediction"] is not None else 0,
            1 if integration_status["buffer_size"] > 0 else 0,
        ]

        # Determine overall health
        health_score = sum(health_values) / len(health_values) * 100

        health_status = (
            "healthy"
            if health_score >= 80
            else "degraded" if health_score >= 50 else "unhealthy"
        )

        return jsonify(
            {
                "status": "success",
                "data": {
                    "health_status": health_status,
                    "health_score": round(health_score, 2),
                    "health_metrics": health_metrics,
                    "integration_status": integration_status,
                    "remediation_status": remediation_status,
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
