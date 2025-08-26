#!/usr/bin/env python3
"""
SmartCloudOps AI - Phase 4 Auto-Remediation Tests
=================================================

Comprehensive test suite for Phase 4 auto-remediation functionality.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch

from app.services.remediation_service import (
    AutoRemediationEngine,
    RemediationRule,
    RemediationAction,
)
from app.services.integration_service import MLRemediationIntegration


class TestRemediationEngine:
    """Test the auto-remediation engine functionality."""

    def test_engine_initialization(self):
        """Test that the remediation engine initializes correctly."""
        engine = AutoRemediationEngine()

        assert engine.is_enabled == True
        assert engine.manual_override == False
        assert len(engine.rules) == 5  # Default rules
        assert len(engine.action_history) == 0

    def test_default_rules_creation(self):
        """Test that default remediation rules are created correctly."""
        engine = AutoRemediationEngine()

        rule_names = [rule.name for rule in engine.rules]
        expected_rules = [
            "Critical System Failure",
            "Service Unresponsive",
            "High CPU Usage",
            "High Memory Usage",
            "Low Resource Utilization",
        ]

        assert set(rule_names) == set(expected_rules)

    def test_rule_priority_ordering(self):
        """Test that rules are properly ordered by priority."""
        engine = AutoRemediationEngine()

        # Sort rules by priority (lower number = higher priority)
        sorted_rules = sorted(engine.rules, key=lambda r: r.priority)

        # Critical failure should have highest priority (0)
        assert sorted_rules[0].name == "Critical System Failure"
        assert sorted_rules[0].priority == 0

        # Low utilization should have lowest priority (3)
        assert sorted_rules[-1].name == "Low Resource Utilization"
        assert sorted_rules[-1].priority == 3

    def test_condition_evaluation(self):
        """Test condition evaluation logic."""
        engine = AutoRemediationEngine()
        rule = engine.rules[0]  # Critical System Failure

        # Test condition that should trigger
        metrics = {"cpu_percent": 96, "memory_percent": 96, "ml_anomaly_score": 0.95}

        assert engine.evaluate_conditions(rule, metrics) == True

        # Test condition that should not trigger
        metrics = {"cpu_percent": 50, "memory_percent": 50, "ml_anomaly_score": 0.3}

        assert engine.evaluate_conditions(rule, metrics) == False

    def test_cooldown_checking(self):
        """Test cooldown period checking."""
        engine = AutoRemediationEngine()
        rule = engine.rules[0]

        # Initially no cooldown
        assert engine.check_cooldown(rule) == False

        # Set last triggered time
        rule.last_triggered = datetime.utcnow()

        # Should be in cooldown
        assert engine.check_cooldown(rule) == True

        # Wait for cooldown to expire
        rule.last_triggered = datetime.utcnow() - timedelta(
            minutes=rule.cooldown_minutes + 1
        )

        # Should not be in cooldown
        assert engine.check_cooldown(rule) == False

    @patch("subprocess.run")
    def test_restart_service_action(self, mock_run):
        """Test restart service remediation action."""
        engine = AutoRemediationEngine()

        # Mock successful systemctl restart
        mock_run.return_value.returncode = 0

        context = {"service_name": "test-service"}
        result = engine._restart_service(context)

        assert result == True
        mock_run.assert_called()

    @patch("subprocess.run")
    def test_clear_cache_action(self, mock_run):
        """Test clear cache remediation action."""
        engine = AutoRemediationEngine()

        mock_run.return_value.returncode = 0

        context = {}
        result = engine._clear_cache(context)

        assert result == True
        mock_run.assert_called()

    def test_send_alert_action(self):
        """Test send alert remediation action."""
        engine = AutoRemediationEngine()

        context = {"message": "Test alert", "severity": "warning"}

        result = engine._send_alert(context)

        assert result == True
        assert len(engine.action_history) > 0

    def test_emergency_shutdown_action(self):
        """Test emergency shutdown remediation action."""
        engine = AutoRemediationEngine()

        context = {"rule_name": "Critical System Failure"}

        with patch("subprocess.run") as mock_run:
            result = engine._emergency_shutdown(context)

            assert result == True
            mock_run.assert_called()

    def test_process_metrics_with_ml_prediction(self):
        """Test processing metrics with ML prediction."""
        engine = AutoRemediationEngine()

        metrics = {
            "cpu_percent": 96,
            "memory_percent": 96,
            "response_time_ms": 6000,
            "error_rate": 0.15,
        }

        ml_prediction = {"anomaly_score": 0.95, "confidence": 0.92, "is_anomaly": True}

        # Mock the remediation actions to avoid actual execution
        with patch.object(engine, "_restart_service", return_value=True), patch.object(
            engine, "_send_alert", return_value=True
        ):

            triggered_actions = engine.process_metrics(metrics, ml_prediction)

            assert len(triggered_actions) > 0
            assert all(action["success"] for action in triggered_actions)

    def test_engine_enable_disable(self):
        """Test enabling and disabling the engine."""
        engine = AutoRemediationEngine()

        # Initially enabled
        assert engine.is_enabled == True

        # Disable
        engine.disable()
        assert engine.is_enabled == False

        # Enable
        engine.enable()
        assert engine.is_enabled == True

    def test_manual_override(self):
        """Test manual override functionality."""
        engine = AutoRemediationEngine()

        # Initially no override
        assert engine.manual_override == False

        # Set override
        engine.set_manual_override(True)
        assert engine.manual_override == True

        # Clear override
        engine.set_manual_override(False)
        assert engine.manual_override == False

    def test_add_remove_rules(self):
        """Test adding and removing remediation rules."""
        engine = AutoRemediationEngine()
        initial_count = len(engine.rules)

        # Add new rule
        new_rule = RemediationRule(
            name="Test Rule",
            conditions={"cpu_percent": {"threshold": 80}},
            actions=[RemediationAction.SEND_ALERT],
        )

        engine.add_rule(new_rule)
        assert len(engine.rules) == initial_count + 1

        # Remove rule
        success = engine.remove_rule("Test Rule")
        assert success == True
        assert len(engine.rules) == initial_count

        # Try to remove non-existent rule
        success = engine.remove_rule("Non-existent Rule")
        assert success == False

    def test_get_status(self):
        """Test getting engine status."""
        engine = AutoRemediationEngine()

        status = engine.get_status()

        assert "enabled" in status
        assert "manual_override" in status
        assert "total_rules" in status
        assert "enabled_rules" in status
        assert "total_actions" in status
        assert "recent_actions" in status
        assert "rules" in status


class TestIntegrationService:
    """Test the ML-Remediation integration service."""

    def test_integration_initialization(self):
        """Test that the integration service initializes correctly."""
        integration = MLRemediationIntegration()

        assert integration.is_running == False
        assert integration.monitoring_interval == 30
        assert integration.confidence_threshold == 0.7
        assert integration.buffer_size == 10
        assert len(integration.metrics_buffer) == 0

    def test_collect_system_metrics(self):
        """Test system metrics collection."""
        integration = MLRemediationIntegration()

        # Test the fallback to simulated metrics
        metrics = integration._collect_system_metrics()

        assert "cpu_percent" in metrics
        assert "memory_percent" in metrics
        assert "disk_percent" in metrics
        assert "response_time_ms" in metrics
        assert "error_rate" in metrics
        assert "timestamp" in metrics

        # Check value ranges (adjusted for actual psutil values)
        assert 0 <= metrics["cpu_percent"] <= 100
        assert 0 <= metrics["memory_percent"] <= 100
        assert 0 <= metrics["disk_percent"] <= 100

    def test_simulated_metrics(self):
        """Test simulated metrics generation."""
        integration = MLRemediationIntegration()

        metrics = integration._get_simulated_metrics()

        assert "cpu_percent" in metrics
        assert "memory_percent" in metrics
        assert "disk_percent" in metrics
        assert "response_time_ms" in metrics
        assert "error_rate" in metrics
        assert "timestamp" in metrics

        # Check value ranges (adjusted for actual psutil values)
        assert 0 <= metrics["cpu_percent"] <= 100
        assert 0 <= metrics["memory_percent"] <= 100
        assert 0 <= metrics["disk_percent"] <= 100

    def test_feature_preparation(self):
        """Test feature preparation for ML prediction."""
        integration = MLRemediationIntegration()

        metrics = {
            "cpu_percent": 75.0,
            "memory_percent": 80.0,
            "disk_percent": 60.0,
            "response_time_ms": 150.0,
            "error_rate": 0.02,
            "network_bytes_sent": 1000,
            "network_bytes_recv": 2000,
            "memory_available_gb": 1.0,
            "disk_free_gb": 5.0,
            "timestamp": datetime.utcnow().isoformat(),
        }

        features = integration._prepare_features(metrics)

        assert features["cpu_percent"] == 75.0
        assert features["memory_percent"] == 80.0
        assert features["disk_percent"] == 60.0
        assert features["response_time_ms"] == 150.0
        assert features["error_rate"] == 0.02
        assert "hour" in features
        assert "minute" in features
        assert "day_of_week" in features

    @patch("app.services.integration_service.ProductionInferenceEngine")
    def test_ml_prediction(self, mock_ml_engine):
        """Test ML prediction functionality."""
        integration = MLRemediationIntegration()

        # Mock ML engine response
        mock_prediction = {
            "anomaly_score": 0.85,
            "confidence": 0.92,
            "is_anomaly": True,
        }
        integration.ml_engine.predict_anomaly.return_value = mock_prediction

        metrics = {
            "cpu_percent": 95.0,
            "memory_percent": 90.0,
            "timestamp": datetime.utcnow().isoformat(),
        }

        prediction = integration._get_ml_prediction(metrics)

        assert prediction is not None
        assert prediction["anomaly_score"] == 0.85
        assert prediction["confidence"] == 0.92
        assert prediction["is_anomaly"] == True

    def test_metrics_buffer_management(self):
        """Test metrics buffer management."""
        integration = MLRemediationIntegration()
        integration.buffer_size = 3

        # Add metrics to buffer
        metrics1 = {"cpu_percent": 50, "timestamp": datetime.utcnow().isoformat()}
        metrics2 = {"cpu_percent": 60, "timestamp": datetime.utcnow().isoformat()}
        metrics3 = {"cpu_percent": 70, "timestamp": datetime.utcnow().isoformat()}
        metrics4 = {"cpu_percent": 80, "timestamp": datetime.utcnow().isoformat()}

        integration._update_metrics_buffer(metrics1, None)
        integration._update_metrics_buffer(metrics2, None)
        integration._update_metrics_buffer(metrics3, None)
        integration._update_metrics_buffer(metrics4, None)

        # Should only keep the last 3 entries
        assert len(integration.metrics_buffer) == 3
        assert integration.metrics_buffer[-1]["metrics"]["cpu_percent"] == 80

    def test_get_status(self):
        """Test getting integration status."""
        integration = MLRemediationIntegration()

        status = integration.get_status()

        assert "is_running" in status
        assert "monitoring_interval" in status
        assert "confidence_threshold" in status
        assert "buffer_size" in status
        assert "last_prediction" in status
        assert "remediation_engine_status" in status

    def test_get_recent_metrics(self):
        """Test getting recent metrics."""
        integration = MLRemediationIntegration()

        # Add some test metrics
        for i in range(5):
            metrics = {
                "cpu_percent": i * 10,
                "timestamp": datetime.utcnow().isoformat(),
            }
            integration._update_metrics_buffer(metrics, None)

        recent_metrics = integration.get_recent_metrics(limit=3)
        assert len(recent_metrics) == 3

    def test_config_update(self):
        """Test configuration updates."""
        integration = MLRemediationIntegration()

        new_config = {
            "monitoring_interval": 60,
            "confidence_threshold": 0.8,
            "buffer_size": 20,
        }

        integration.update_config(new_config)

        assert integration.monitoring_interval == 60
        assert integration.confidence_threshold == 0.8
        assert integration.buffer_size == 20


class TestRemediationAPI:
    """Test the remediation API endpoints."""

    def test_get_remediation_status(self, client):
        """Test getting remediation engine status."""
        response = client.get("/api/v1/remediation/status")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "data" in data
        assert "enabled" in data["data"]

    def test_enable_remediation(self, client):
        """Test enabling the remediation engine."""
        response = client.post("/api/v1/remediation/enable")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "enabled" in data["message"].lower()

    def test_disable_remediation(self, client):
        """Test disabling the remediation engine."""
        response = client.post("/api/v1/remediation/disable")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "disabled" in data["message"].lower()

    def test_set_manual_override(self, client):
        """Test setting manual override."""
        response = client.post("/api/v1/remediation/override", json={"enabled": True})

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "enabled" in data["message"].lower()

    def test_get_rules(self, client):
        """Test getting remediation rules."""
        response = client.get("/api/v1/remediation/rules")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "rules" in data["data"]
        assert len(data["data"]["rules"]) > 0

    def test_add_rule(self, client):
        """Test adding a new remediation rule."""
        rule_data = {
            "name": "Test Rule",
            "conditions": {"cpu_percent": {"threshold": 80}},
            "actions": ["send_alert"],
            "priority": 2,
            "cooldown_minutes": 5,
        }

        response = client.post("/api/v1/remediation/rules", json=rule_data)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "added" in data["message"].lower()

    def test_remove_rule(self, client):
        """Test removing a remediation rule."""
        # First add a rule
        rule_data = {
            "name": "Test Rule for Removal",
            "conditions": {"cpu_percent": {"threshold": 80}},
            "actions": ["send_alert"],
        }
        client.post("/api/v1/remediation/rules", json=rule_data)

        # Then remove it
        response = client.delete("/api/v1/remediation/rules/Test Rule for Removal")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "removed" in data["message"].lower()

    def test_get_action_history(self, client):
        """Test getting action history."""
        response = client.get("/api/v1/remediation/actions")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "actions" in data["data"]

    def test_test_remediation(self, client):
        """Test the remediation test endpoint."""
        test_data = {"cpu_percent": 95, "memory_percent": 90, "ml_anomaly_score": 0.85}

        response = client.post("/api/v1/remediation/test", json=test_data)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "test_metrics" in data["data"]
        assert "triggered_actions" in data["data"]

    def test_get_remediation_metrics(self, client):
        """Test getting remediation metrics."""
        response = client.get("/api/v1/remediation/metrics")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "engine_status" in data["data"]
        assert "rules_summary" in data["data"]
        assert "actions_summary" in data["data"]


class TestIntegrationAPI:
    """Test the integration API endpoints."""

    def test_get_integration_status(self, client):
        """Test getting integration status."""
        response = client.get("/api/v1/integration/status")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "data" in data

    def test_start_integration(self, client):
        """Test starting the integration."""
        response = client.post("/api/v1/integration/start")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "started" in data["message"].lower()

    def test_stop_integration(self, client):
        """Test stopping the integration."""
        response = client.post("/api/v1/integration/stop")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "stopped" in data["message"].lower()

    def test_get_recent_metrics(self, client):
        """Test getting recent metrics."""
        response = client.get("/api/v1/integration/metrics")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "metrics" in data["data"]

    def test_trigger_manual_remediation(self, client):
        """Test manual remediation trigger."""
        response = client.post("/api/v1/integration/trigger")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "metrics" in data["data"]
        assert "triggered_actions" in data["data"]

    def test_get_integration_config(self, client):
        """Test getting integration configuration."""
        response = client.get("/api/v1/integration/config")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "monitoring_interval" in data["data"]
        assert "confidence_threshold" in data["data"]
        assert "buffer_size" in data["data"]

    def test_update_integration_config(self, client):
        """Test updating integration configuration."""
        config_data = {"monitoring_interval": 60, "confidence_threshold": 0.8}

        response = client.put("/api/v1/integration/config", json=config_data)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "updated" in data["message"].lower()

    def test_test_integration(self, client):
        """Test the integration test endpoint."""
        test_data = {"cpu_percent": 95, "memory_percent": 90, "ml_anomaly_score": 0.85}

        response = client.post("/api/v1/integration/test", json=test_data)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "test_metrics" in data["data"]
        assert "ml_prediction" in data["data"]
        assert "triggered_actions" in data["data"]

    def test_get_integration_health(self, client):
        """Test getting integration health status."""
        response = client.get("/api/v1/integration/health")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "health_status" in data["data"]
        assert "health_score" in data["data"]
        assert "health_metrics" in data["data"]


# Test fixtures
@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    from app.main import create_app

    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client
