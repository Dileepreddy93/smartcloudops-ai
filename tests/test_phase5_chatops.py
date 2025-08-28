"""
SmartCloudOps AI - Phase 5: ChatOps Tests
========================================

Comprehensive test suite for NLP-enhanced ChatOps functionality.
Optimized for resource efficiency and test stability.
"""


import json
from unittest.mock import patch

import pytest


class TestNLPEnhancedChatOps:
    """Test cases for NLP Enhanced ChatOps service."""

    def test_initialization(self, nlp_service):
        """Test NLP service initialization."""
        assert nlp_service is not None
        assert hasattr(nlp_service, "nlp")
        assert hasattr(nlp_service, "devops_intents")
        assert len(nlp_service.devops_intents) > 0

    def test_preprocess_input(self, nlp_service):
        """Test input preprocessing."""
        test_cases = [
            ("Deploy the APP!", "deploy the app"),
            ("  Scale   servers   to   3  ", "scale servers to 3"),
            ("Check logs of EC2", "check logs of ec2"),
            ("Restart the service", "restart the service"),
        ]

        for input_text, expected in test_cases:
            result = nlp_service._preprocess_input(input_text)
            assert result == expected

    def test_detect_intent_pattern_matching(self, nlp_service):
        """Test intent detection using pattern matching."""
        test_cases = [
            ("deploy the app", "deploy"),
            ("scale servers to 3", "scale"),
            ("show logs of ec2", "monitor"),
            ("restart the service", "restart"),
            ("create backup of database", "backup"),
            ("check security vulnerabilities", "security"),
            ("show cost report", "cost"),
            ("check compliance", "compliance"),
            ("set up alert", "alert"),
            ("rollback to previous version", "rollback"),
        ]

        for command, expected_intent in test_cases:
            intent = nlp_service._detect_intent(command)
            assert intent == expected_intent

    def test_extract_entities(self, nlp_service):
        """Test entity extraction."""
        # Test with scale command
        text = "scale servers to 5"
        intent = "scale"
        entities = nlp_service._extract_entities(text, intent)

        assert "numbers" in entities
        assert "5" in entities["numbers"]

    def test_generate_action_plan(self, nlp_service):
        """Test action plan generation."""
        # Test deploy action
        intent = "deploy"
        entities = {"app_name": "smartcloudops", "environment": "production"}

        action_plan = nlp_service._generate_action_plan(intent, entities)

        assert action_plan["action"] == "deploy"
        assert action_plan["parameters"] == entities
        assert "aws_operations" in action_plan
        assert "safety_checks" in action_plan
        assert "estimated_time" in action_plan

    def test_calculate_confidence(self, nlp_service):
        """Test confidence calculation."""
        intent = "deploy"
        entities = {"app_name": "test", "environment": "prod"}

        confidence = nlp_service._calculate_confidence(intent, entities)

        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be higher with entities

    def test_process_command_success(self, nlp_service):
        """Test successful command processing."""
        command = "deploy the app to production"

        result = nlp_service.process_command(command)

        assert result["status"] == "success"
        assert result["original_input"] == command
        assert "intent" in result
        assert "entities" in result
        assert "action_plan" in result
        assert "confidence" in result
        assert "timestamp" in result

    def test_process_command_error(self, nlp_service):
        """Test command processing with error."""
        # Mock spaCy to raise an error
        with patch.object(nlp_service, "nlp", side_effect=Exception("NLP Error")):
            result = nlp_service.process_command("test command")

            assert result["status"] == "error"
            assert "error" in result
            assert "NLP Error" in result["error"]

    def test_get_command_history(self, nlp_service):
        """Test command history retrieval."""
        # Add some test commands
        nlp_service.process_command("deploy app")
        nlp_service.process_command("scale to 3")

        history = nlp_service.get_command_history(limit=5)

        assert len(history) <= 5
        assert all("timestamp" in entry for entry in history)

    def test_get_intent_statistics(self, nlp_service):
        """Test intent statistics."""
        # Add some test commands
        nlp_service.process_command("deploy app")
        nlp_service.process_command("scale to 3")
        nlp_service.process_command("deploy app")

        stats = nlp_service.get_intent_statistics()

        assert "total_commands" in stats
        assert "intents" in stats
        assert "success_rate" in stats
        assert stats["total_commands"] >= 3

    def test_health_check(self, nlp_service):
        """Test health check functionality."""
        health = nlp_service.health_check()

        assert "status" in health
        assert "timestamp" in health
        assert health["status"] in ["healthy", "unhealthy"]


class TestAWSIntegrationService:
    """Test cases for AWS Integration service."""

    def test_initialization(self, aws_service):
        """Test AWS service initialization."""
        assert aws_service is not None
        assert hasattr(aws_service, "safety_limits")
        assert len(aws_service.safety_limits) > 0

    def test_check_safety_limits_scale_safe(self, aws_service):
        """Test safety limits check for safe scale operation."""
        action = "scale"
        parameters = {"count": 5}

        result = aws_service._check_safety_limits(action, parameters)

        assert result["safe"] is True

    def test_check_safety_limits_scale_unsafe(self, aws_service):
        """Test safety limits check for unsafe scale operation."""
        action = "scale"
        parameters = {"count": 15}  # Exceeds max_instances limit

        result = aws_service._check_safety_limits(action, parameters)

        assert result["safe"] is False
        assert "exceeds maximum limit" in result["reason"]

    def test_check_safety_limits_deploy_safe(self, aws_service):
        """Test safety limits check for safe deploy operation."""
        action = "deploy"
        parameters = {}

        result = aws_service._check_safety_limits(action, parameters)

        assert result["safe"] is True

    def test_execute_deploy(self, aws_service):
        """Test deploy action execution."""
        parameters = {"app_name": "test-app", "environment": "staging"}

        result = aws_service._execute_deploy(parameters)

        assert "deployment_id" in result
        assert result["app_name"] == "test-app"
        assert result["environment"] == "staging"
        assert result["status"] == "initiated"

    def test_execute_scale(self, aws_service):
        """Test scale action execution."""
        parameters = {"count": 3, "resource_type": "instances"}

        # Mock AWS client responses
        with patch.object(aws_service.autoscaling_client, "describe_auto_scaling_groups") as mock_describe:
            mock_describe.return_value = {"AutoScalingGroups": [{"AutoScalingGroupName": "test-asg"}]}

            with patch.object(aws_service.autoscaling_client, "set_desired_capacity"):
                result = aws_service._execute_scale(parameters)

                assert result["asg_name"] == "test-asg"
                assert result["new_capacity"] == 3
                assert result["status"] == "scaling_initiated"

    def test_execute_monitor(self, aws_service):
        """Test monitor action execution."""
        parameters = {"service_name": "ec2", "metric_type": "cpu"}

        # Mock AWS client responses
        with patch.object(aws_service.cloudwatch_client, "get_metric_data") as mock_metrics:
            mock_metrics.return_value = {"MetricDataResults": [{"Values": [75.5, 80.2, 65.1]}]}

            result = aws_service._execute_monitor(parameters)

            assert result["service"] == "ec2"
            assert result["metric"] == "cpu"
            assert result["data_points"] == 3
            assert result["latest_value"] == 65.1

    def test_execute_action_success(self, aws_service):
        """Test successful action execution."""
        action_plan = {
            "action": "deploy",
            "parameters": {"app_name": "test-app", "environment": "production"},
        }

        result = aws_service.execute_action(action_plan)

        assert result["status"] == "success"
        assert result["action"] == "deploy"
        assert "result" in result
        assert "timestamp" in result

    def test_execute_action_blocked(self, aws_service):
        """Test blocked action execution."""
        action_plan = {
            "action": "scale",
            "parameters": {"count": 15},  # Exceeds safety limit
        }

        result = aws_service.execute_action(action_plan)

        assert result["status"] == "blocked"
        assert "reason" in result

    def test_execute_action_error(self, aws_service):
        """Test action execution with error."""
        action_plan = {"action": "invalid_action", "parameters": {}}

        result = aws_service.execute_action(action_plan)

        assert result["status"] == "success"  # Should handle gracefully
        assert result["result"]["status"] == "unsupported"

    def test_get_execution_history(self, aws_service):
        """Test execution history retrieval."""
        # Add some test executions
        action_plan = {"action": "deploy", "parameters": {}}
        aws_service.execute_action(action_plan)

        history = aws_service.get_execution_history(limit=5)

        assert len(history) <= 5
        assert all("timestamp" in entry for entry in history)

    def test_get_execution_statistics(self, aws_service):
        """Test execution statistics."""
        # Add some test executions
        action_plan = {"action": "deploy", "parameters": {}}
        aws_service.execute_action(action_plan)

        stats = aws_service.get_execution_statistics()

        assert "total_executions" in stats
        assert "successful_executions" in stats
        assert "success_rate" in stats
        assert "actions" in stats

    def test_health_check(self, aws_service):
        """Test health check functionality."""
        # Mock AWS client to simulate healthy state
        with patch.object(aws_service.ec2_client, "describe_regions") as mock_regions:
            mock_regions.return_value = {"Regions": []}

            health = aws_service.health_check()

            assert "status" in health
            assert "timestamp" in health
            assert health["status"] == "healthy"

    def test_health_check_no_credentials(self, aws_service):
        """Test health check with no AWS credentials."""
        from botocore.exceptions import NoCredentialsError

        with patch.object(aws_service.ec2_client, "describe_regions", side_effect=NoCredentialsError()):
            health = aws_service.health_check()

            assert health["status"] == "unhealthy"
            assert "credentials not configured" in health["error"]


class TestPhase5Integration:
    """Integration tests for Phase 5 functionality."""

    def test_nlp_to_aws_integration(self, nlp_service, aws_service):
        """Test integration between NLP and AWS services."""
        # Test complete flow from NLP to AWS execution
        command = "deploy the smartcloudops app to production"

        # Process through NLP
        nlp_result = nlp_service.process_command(command)

        assert nlp_result["status"] == "success"
        assert nlp_result["intent"] == "deploy"

        # Execute through AWS service
        if nlp_result["confidence"] > 0.7:
            aws_result = aws_service.execute_action(nlp_result["action_plan"])

            # Check that the action was processed (could be success, blocked, or error)
            assert aws_result["status"] in ["success", "blocked", "error"]
            assert aws_result["action"] == "deploy"

    def test_command_history_integration(self, nlp_service):
        """Test command history integration."""
        # Process multiple commands
        commands = ["deploy the app", "scale servers to 3", "show logs of ec2"]

        for command in commands:
            nlp_service.process_command(command)

        # Check history
        history = nlp_service.get_command_history(limit=10)
        assert len(history) >= len(commands)

    def test_statistics_integration(self, nlp_service, aws_service):
        """Test statistics integration."""
        # Process some commands
        nlp_service.process_command("deploy app")
        aws_service.execute_action({"action": "deploy", "parameters": {}})

        # Get statistics
        nlp_stats = nlp_service.get_intent_statistics()
        aws_stats = aws_service.get_execution_statistics()

        assert nlp_stats["total_commands"] > 0
        assert aws_stats["total_executions"] > 0


class TestPhase5APIEndpoints:
    """Test cases for Phase 5 API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.main import create_app

        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def test_process_chatops_command_success(self, client):
        """Test successful ChatOps command processing."""
        data = {
            "command": "deploy the app to production",
            "user_id": "test_user",
            "channel": "slack",
        }

        response = client.post("/api/v1/chatops/process", json=data)

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result["status"] == "success"
        assert result["command"] == data["command"]
        assert "nlp_result" in result

    def test_process_chatops_command_missing_command(self, client):
        """Test ChatOps command processing with missing command."""
        data = {"user_id": "test_user"}

        response = client.post("/api/v1/chatops/process", json=data)

        assert response.status_code == 400
        result = json.loads(response.data)
        assert result["status"] == "error"

    def test_get_supported_intents(self, client):
        """Test getting supported intents."""
        response = client.get("/api/v1/chatops/intents")

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result["status"] == "success"
        assert "intents" in result
        assert len(result["intents"]) > 0

    def test_get_command_history(self, client):
        """Test getting command history."""
        response = client.get("/api/v1/chatops/history?limit=5")

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result["status"] == "success"
        assert "history" in result

    def test_get_chatops_statistics(self, client):
        """Test getting ChatOps statistics."""
        response = client.get("/api/v1/chatops/statistics")

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result["status"] == "success"
        assert "nlp_statistics" in result
        assert "aws_statistics" in result

    def test_execute_action(self, client):
        """Test direct action execution."""
        data = {
            "action": "deploy",
            "parameters": {"app_name": "test-app", "environment": "staging"},
        }

        response = client.post("/api/v1/chatops/execute", json=data)

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result["status"] == "success"
        assert result["action"] == "deploy"

    def test_get_execution_history(self, client):
        """Test getting execution history."""
        response = client.get("/api/v1/chatops/executions?limit=5")

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result["status"] == "success"
        assert "history" in result

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/chatops/health")

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result["status"] == "success"
        assert "overall_status" in result
        assert "nlp_service" in result
        assert "aws_service" in result

    def test_test_command(self, client):
        """Test command testing endpoint."""
        data = {"command": "scale servers to 3"}

        response = client.post("/api/v1/chatops/test", json=data)

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result["status"] == "success"
        assert result["command"] == data["command"]
        assert "nlp_result" in result
        assert result["execution_simulated"] is False

    def test_get_safety_limits(self, client):
        """Test getting safety limits."""
        response = client.get("/api/v1/chatops/safety-limits")

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result["status"] == "success"
        assert "safety_limits" in result

    def test_update_safety_limits(self, client):
        """Test updating safety limits."""
        data = {"max_instances": 15, "cooldown_period_minutes": 10}

        response = client.put("/api/v1/chatops/safety-limits", json=data)

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result["status"] == "success"
        assert "Safety limits updated" in result["message"]


if __name__ == "__main__":
    pytest.main([__file__])
