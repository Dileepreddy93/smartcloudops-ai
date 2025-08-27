"""
SmartCloudOps AI - Phase 5: ChatOps API Routes
=============================================

API endpoints for NLP-enhanced ChatOps functionality.
"""

from datetime import datetime

from flask import Blueprint, jsonify, request

from app.services.aws_integration_service import aws_integration_service
from app.services.nlp_chatops_service import nlp_chatops_service

# Create blueprint
phase5_bp = Blueprint("phase5", __name__, url_prefix="/api/v1/chatops")


@phase5_bp.route("/process", methods=["POST"])
def process_chatops_command():
    """
    Process natural language ChatOps command.

    Expected JSON payload:
    {
        "command": "deploy the app to production",
        "user_id": "user123",
        "channel": "slack"
    }
    """
    try:
        data = request.get_json()

        if not data or "command" not in data:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Command is required",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ),
                400,
            )

        command = data["command"]
        user_id = data.get("user_id", "anonymous")
        channel = data.get("channel", "api")

        # Process command through NLP service
        nlp_result = nlp_chatops_service.process_command(command)

        if nlp_result["status"] == "error":
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Failed to process command",
                        "error": nlp_result["error"],
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ),
                500,
            )

        # Execute action if confidence is high enough
        execution_result = None
        if nlp_result["confidence"] > 0.7:
            execution_result = aws_integration_service.execute_action(
                nlp_result["action_plan"]
            )

        return jsonify(
            {
                "status": "success",
                "command": command,
                "user_id": user_id,
                "channel": channel,
                "nlp_result": nlp_result,
                "execution_result": execution_result,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Internal server error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            500,
        )


@phase5_bp.route("/intents", methods=["GET"])
def get_supported_intents():
    """Get list of supported ChatOps intents."""
    try:
        intents = list(nlp_chatops_service.devops_intents.keys())

        return jsonify(
            {
                "status": "success",
                "intents": intents,
                "total_intents": len(intents),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Failed to get intents",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            500,
        )


@phase5_bp.route("/history", methods=["GET"])
def get_command_history():
    """Get recent command history."""
    try:
        limit = request.args.get("limit", 10, type=int)
        history = nlp_chatops_service.get_command_history(limit)

        return jsonify(
            {
                "status": "success",
                "history": history,
                "total_commands": len(history),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Failed to get command history",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            500,
        )


@phase5_bp.route("/statistics", methods=["GET"])
def get_chatops_statistics():
    """Get ChatOps statistics and analytics."""
    try:
        nlp_stats = nlp_chatops_service.get_intent_statistics()
        aws_stats = aws_integration_service.get_execution_statistics()

        return jsonify(
            {
                "status": "success",
                "nlp_statistics": nlp_stats,
                "aws_statistics": aws_stats,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Failed to get statistics",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            500,
        )


@phase5_bp.route("/execute", methods=["POST"])
def execute_action():
    """
    Execute a specific action directly.

    Expected JSON payload:
    {
        "action": "deploy",
        "parameters": {
            "app_name": "smartcloudops-ai",
            "environment": "production"
        }
    }
    """
    try:
        data = request.get_json()

        if not data or "action" not in data:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Action is required",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ),
                400,
            )

        action = data["action"]
        parameters = data.get("parameters", {})

        # Create action plan
        action_plan = {"action": action, "parameters": parameters}

        # Execute action
        result = aws_integration_service.execute_action(action_plan)

        return jsonify(
            {
                "status": "success",
                "action": action,
                "parameters": parameters,
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Failed to execute action",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            500,
        )


@phase5_bp.route("/executions", methods=["GET"])
def get_execution_history():
    """Get recent AWS execution history."""
    try:
        limit = request.args.get("limit", 10, type=int)
        history = aws_integration_service.get_execution_history(limit)

        return jsonify(
            {
                "status": "success",
                "history": history,
                "total_executions": len(history),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Failed to get execution history",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            500,
        )


@phase5_bp.route("/health", methods=["GET"])
def health_check():
    """Health check for Phase 5 services."""
    try:
        nlp_health = nlp_chatops_service.health_check()
        aws_health = aws_integration_service.health_check()

        overall_status = "healthy"
        if nlp_health["status"] != "healthy" or aws_health["status"] != "healthy":
            overall_status = "unhealthy"

        return jsonify(
            {
                "status": "success",
                "overall_status": overall_status,
                "nlp_service": nlp_health,
                "aws_service": aws_health,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Health check failed",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            500,
        )


@phase5_bp.route("/test", methods=["POST"])
def test_command():
    """
    Test command processing without execution.

    Expected JSON payload:
    {
        "command": "scale servers to 3"
    }
    """
    try:
        data = request.get_json()

        if not data or "command" not in data:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Command is required",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ),
                400,
            )

        command = data["command"]

        # Process command through NLP service only
        nlp_result = nlp_chatops_service.process_command(command)

        return jsonify(
            {
                "status": "success",
                "command": command,
                "nlp_result": nlp_result,
                "execution_simulated": False,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Failed to test command",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            500,
        )


@phase5_bp.route("/safety-limits", methods=["GET"])
def get_safety_limits():
    """Get current safety limits configuration."""
    try:
        limits = aws_integration_service.safety_limits

        return jsonify(
            {
                "status": "success",
                "safety_limits": limits,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Failed to get safety limits",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            500,
        )


@phase5_bp.route("/safety-limits", methods=["PUT"])
def update_safety_limits():
    """
    Update safety limits configuration.

    Expected JSON payload:
    {
        "max_instances": 15,
        "cooldown_period_minutes": 10
    }
    """
    try:
        data = request.get_json()

        if not data:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Safety limits data is required",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ),
                400,
            )

        # Update safety limits
        for key, value in data.items():
            if key in aws_integration_service.safety_limits:
                aws_integration_service.safety_limits[key] = value

        return jsonify(
            {
                "status": "success",
                "message": "Safety limits updated",
                "safety_limits": aws_integration_service.safety_limits,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Failed to update safety limits",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            500,
        )
