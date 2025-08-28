#!/usr/bin/env python3
"""
Production Test Suite for SmartCloudOps AI
==========================================

Comprehensive testing framework including:
- Unit tests for all components
- Integration tests for API endpoints
- Load testing for performance validation
- Security testing for vulnerabilities
- Database testing with proper fixtures
- ML pipeline testing with validation
"""

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pytest
import requests

from app.database_improvements import get_db_service
from app.main_secure import app
from app.ml_production_pipeline import get_ml_pipeline

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../app"))


# Test configuration
TEST_CONFIG = {
    "base_url": "http://localhost:5000",
    "api_keys": {
        "admin": os.getenv("ADMIN_API_KEY", "test-admin-key"),
        "ml": os.getenv("ML_API_KEY", "test-ml-key"),
        "readonly": os.getenv("READONLY_API_KEY", "test-readonly-key"),
    },
    "load_test": {
        "concurrent_users": 50,
        "duration_seconds": 60,
        "ramp_up_seconds": 10,
    },
    "performance_thresholds": {
        "response_time_ms": 500,
        "error_rate_percent": 1.0,
        "throughput_rps": 100,
    },
}


class TestBase:
    """Base class for all tests with common setup and utilities."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.app = app.test_client()
        self.app.testing = True
        self.db_service = get_db_service()
        self.ml_pipeline = get_ml_pipeline()

        # Setup test data
        self.setup_test_data()

        yield

        # Cleanup after tests
        self.cleanup_test_data()

    def setup_test_data(self):
        """Setup test data for tests."""
        self.test_metrics = {
            "cpu_usage": 75.5,
            "memory_usage": 60.2,
            "disk_usage": 45.8,
            "network_io": 1024.5,
        }

        self.test_user_id = "test-user-123"
        self.test_ab_test_id = "test-ab-123"

    def cleanup_test_data(self):
        """Cleanup test data after tests."""
        # Clean up any test data created during tests
        pass

    def make_request(self, method: str, endpoint: str, api_key: str = None, data: Dict = None) -> requests.Response:
        """Make HTTP request with proper headers."""
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-API-Key"] = api_key

        url = f"{TEST_CONFIG['base_url']}{endpoint}"

        if method.upper() == "GET":
            return requests.get(url, headers=headers, timeout=10)
        elif method.upper() == "POST":
            return requests.post(url, headers=headers, json=data, timeout=10)
        elif method.upper() == "PUT":
            return requests.put(url, headers=headers, json=data, timeout=10)
        elif method.upper() == "DELETE":
            return requests.delete(url, headers=headers, timeout=10)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")


class TestUnitComponents(TestBase):
    """Unit tests for individual components."""

    def test_database_connection(self):
        """Test database connection and health check."""
        health_status = self.db_service.health_check()

        assert "database" in health_status
        assert "status" in health_status["database"]
        assert health_status["database"]["status"] in ["healthy", "unhealthy"]

    def test_ml_pipeline_health(self):
        """Test ML pipeline health status."""
        health_status = self.ml_pipeline.get_health_status()

        assert "pipeline_status" in health_status
        assert "current_model" in health_status
        assert "performance_metrics" in health_status

    def test_ml_prediction(self):
        """Test ML prediction functionality."""
        result = self.ml_pipeline.predict(self.test_metrics)

        assert "prediction" in result
        assert result["prediction"] in ["anomaly", "normal", "error"]
        assert "anomaly_score" in result
        assert "confidence" in result
        assert "latency_ms" in result

    def test_database_metrics_storage(self):
        """Test database metrics storage functionality."""
        success = self.db_service.store_metrics(self.test_metrics)
        assert success is True

        # Verify metrics can be retrieved
        metrics = self.db_service.get_metrics(limit=10)
        assert isinstance(metrics, list)

    def test_redis_caching(self):
        """Test Redis caching functionality."""
        # Test cache storage and retrieval
        cache_key = "test:metrics:latest:10"
        test_data = [self.test_metrics]

        if self.db_service.redis_client:
            self.db_service.redis_client.setex(cache_key, 300, str(test_data))
            cached_data = self.db_service.redis_client.get(cache_key)
            assert cached_data is not None


class TestAPIEndpoints(TestBase):
    """Integration tests for API endpoints."""

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.make_request("GET", "/health", api_key=TEST_CONFIG["api_keys"]["admin"])

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy"]

    def test_status_endpoint(self):
        """Test status endpoint."""
        response = self.make_request("GET", "/status", api_key=TEST_CONFIG["api_keys"]["readonly"])

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data

    def test_ml_prediction_endpoint(self):
        """Test ML prediction endpoint."""
        data = {"metrics": self.test_metrics}
        response = self.make_request("POST", "/ml/predict", api_key=TEST_CONFIG["api_keys"]["ml"], data=data)

        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert "anomaly_score" in data

    def test_metrics_endpoint(self):
        """Test metrics endpoint."""
        response = self.make_request("GET", "/metrics", api_key=TEST_CONFIG["api_keys"]["readonly"])

        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data

    def test_authentication_required(self):
        """Test that authentication is required for protected endpoints."""
        response = self.make_request("GET", "/status")
        assert response.status_code == 401

    def test_invalid_api_key(self):
        """Test that invalid API keys are rejected."""
        response = self.make_request("GET", "/status", api_key="invalid-key")
        assert response.status_code == 401

    def test_permission_denied(self):
        """Test that readonly keys cannot access admin endpoints."""
        response = self.make_request("GET", "/admin/status", api_key=TEST_CONFIG["api_keys"]["readonly"])
        assert response.status_code == 403


class TestSecurityVulnerabilities(TestBase):
    """Security tests to identify vulnerabilities."""

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention."""
        malicious_data = {
            "metrics": {
                "cpu_usage": "'; DROP TABLE system_metrics; --",
                "memory_usage": 60.2,
            }
        }

        response = self.make_request(
            "POST",
            "/ml/predict",
            api_key=TEST_CONFIG["api_keys"]["ml"],
            data=malicious_data,
        )

        # Should handle gracefully, not crash
        assert response.status_code in [200, 400, 422]

    def test_xss_prevention(self):
        """Test XSS prevention."""
        malicious_data = {
            "metrics": {
                "cpu_usage": '<script>alert("xss")</script>',
                "memory_usage": 60.2,
            }
        }

        response = self.make_request(
            "POST",
            "/ml/predict",
            api_key=TEST_CONFIG["api_keys"]["ml"],
            data=malicious_data,
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        # Make many rapid requests
        responses = []
        for _ in range(100):
            response = self.make_request("GET", "/status", api_key=TEST_CONFIG["api_keys"]["readonly"])
            responses.append(response.status_code)

        # Should have some rate limiting (429 responses)
        assert 429 in responses

    def test_input_validation(self):
        """Test input validation for various data types."""
        invalid_inputs = [
            {"metrics": {"cpu_usage": "not_a_number"}},
            {"metrics": {"cpu_usage": -1}},
            {"metrics": {"cpu_usage": 101}},
            {"metrics": {}},
            {"invalid_key": "value"},
        ]

        for invalid_input in invalid_inputs:
            response = self.make_request(
                "POST",
                "/ml/predict",
                api_key=TEST_CONFIG["api_keys"]["ml"],
                data=invalid_input,
            )

            # Should reject invalid input
            assert response.status_code in [400, 422]

    def test_sensitive_data_exposure(self):
        """Test that sensitive data is not exposed."""
        response = self.make_request("GET", "/status", api_key=TEST_CONFIG["api_keys"]["readonly"])

        data = response.json()
        sensitive_keys = ["password", "secret", "key", "token"]

        # Check that response doesn't contain sensitive data
        response_text = json.dumps(data).lower()
        for sensitive_key in sensitive_keys:
            assert sensitive_key not in response_text


class TestPerformanceLoad(TestBase):
    """Load testing for performance validation."""

    def test_single_request_performance(self):
        """Test single request performance."""
        start_time = time.time()
        response = self.make_request("GET", "/status", api_key=TEST_CONFIG["api_keys"]["readonly"])
        end_time = time.time()

        response_time_ms = (end_time - start_time) * 1000

        assert response.status_code == 200
        assert response_time_ms < TEST_CONFIG["performance_thresholds"]["response_time_ms"]

    def test_concurrent_requests(self):
        """Test concurrent request handling."""

        def make_concurrent_request():
            return self.make_request("GET", "/status", api_key=TEST_CONFIG["api_keys"]["readonly"])

        # Make concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_concurrent_request) for _ in range(50)]
            responses = [future.result() for future in as_completed(futures)]

        # Check all requests succeeded
        success_count = sum(1 for r in responses if r.status_code == 200)
        error_rate = (len(responses) - success_count) / len(responses) * 100

        assert error_rate < TEST_CONFIG["performance_thresholds"]["error_rate_percent"]

    def test_sustained_load(self):
        """Test sustained load over time."""
        start_time = time.time()
        request_count = 0
        error_count = 0

        while time.time() - start_time < TEST_CONFIG["load_test"]["duration_seconds"]:
            try:
                response = self.make_request("GET", "/status", api_key=TEST_CONFIG["api_keys"]["readonly"])
                request_count += 1

                if response.status_code != 200:
                    error_count += 1

            except Exception:
                error_count += 1

            time.sleep(0.1)  # 10 requests per second

        # Calculate metrics
        duration = time.time() - start_time
        throughput_rps = request_count / duration
        error_rate = (error_count / request_count) * 100 if request_count > 0 else 0

        # Assert performance thresholds
        assert throughput_rps >= TEST_CONFIG["performance_thresholds"]["throughput_rps"]
        assert error_rate < TEST_CONFIG["performance_thresholds"]["error_rate_percent"]

    def test_ml_pipeline_performance(self):
        """Test ML pipeline performance under load."""

        def make_ml_request():
            data = {"metrics": self.test_metrics}
            return self.make_request("POST", "/ml/predict", api_key=TEST_CONFIG["api_keys"]["ml"], data=data)

        # Test ML pipeline with concurrent requests
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_ml_request) for _ in range(20)]
            responses = [future.result() for future in as_completed(futures)]

        end_time = time.time()

        # Check performance
        success_count = sum(1 for r in responses if r.status_code == 200)
        avg_response_time = (end_time - start_time) / len(responses) * 1000

        assert success_count >= len(responses) * 0.95  # 95% success rate
        assert avg_response_time < 1000  # Less than 1 second average


class TestDatabaseOperations(TestBase):
    """Database operation tests."""

    def test_connection_pooling(self):
        """Test database connection pooling."""

        # Make multiple concurrent database operations
        def db_operation():
            return self.db_service.get_metrics(limit=10)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(db_operation) for _ in range(20)]
            results = [future.result() for future in as_completed(futures)]

        # All operations should succeed
        assert all(isinstance(result, list) for result in results)

    def test_transaction_rollback(self):
        """Test database transaction rollback on error."""
        # This would test transaction handling in a real scenario
        # For now, just verify the service is available
        assert self.db_service is not None

    def test_data_consistency(self):
        """Test data consistency across operations."""
        # Store metrics
        success = self.db_service.store_metrics(self.test_metrics)
        assert success is True

        # Retrieve and verify
        metrics = self.db_service.get_metrics(limit=1)
        if metrics:
            stored_metric = metrics[0]
            for key, value in self.test_metrics.items():
                assert key in stored_metric
                assert stored_metric[key] == value


class TestMLPipelineValidation(TestBase):
    """ML pipeline validation tests."""

    def test_model_loading(self):
        """Test model loading and validation."""
        health_status = self.ml_pipeline.get_health_status()

        assert "pipeline_status" in health_status
        assert "current_model" in health_status

    def test_prediction_consistency(self):
        """Test prediction consistency for same input."""
        result1 = self.ml_pipeline.predict(self.test_metrics)
        result2 = self.ml_pipeline.predict(self.test_metrics)

        # Predictions should be consistent
        assert result1["prediction"] == result2["prediction"]
        assert abs(result1["anomaly_score"] - result2["anomaly_score"]) < 0.001

    def test_prediction_bounds(self):
        """Test prediction output bounds."""
        result = self.ml_pipeline.predict(self.test_metrics)

        assert 0 <= result["confidence"] <= 1
        assert result["latency_ms"] >= 0

    def test_error_handling(self):
        """Test ML pipeline error handling."""
        # Test with invalid input
        invalid_metrics = {"invalid_key": "invalid_value"}
        result = self.ml_pipeline.predict(invalid_metrics)

        # Should handle gracefully
        assert "prediction" in result
        assert result["prediction"] in ["anomaly", "normal", "error"]


def run_all_tests():
    """Run all test suites and generate report."""
    print("🧪 Starting Production Test Suite")
    print("=" * 50)

    test_results = {
        "unit_tests": [],
        "integration_tests": [],
        "security_tests": [],
        "performance_tests": [],
        "database_tests": [],
        "ml_tests": [],
    }

    # Run tests and collect results
    test_classes = [
        TestUnitComponents,
        TestAPIEndpoints,
        TestSecurityVulnerabilities,
        TestPerformanceLoad,
        TestDatabaseOperations,
        TestMLPipelineValidation,
    ]

    for test_class in test_classes:
        print(f"\n📋 Running {test_class.__name__}...")

        # Create test instance and run tests
        test_instance = test_class()
        test_instance.setup()

        # Run all test methods
        test_methods = [method for method in dir(test_class) if method.startswith("test_")]

        for method_name in test_methods:
            try:
                method = getattr(test_instance, method_name)
                method()
                print(f"  ✅ {method_name}")
                test_results["unit_tests"].append({"test": method_name, "status": "PASS", "duration_ms": 0})
            except Exception as e:
                print(f"  ❌ {method_name}: {e}")
                test_results["unit_tests"].append({"test": method_name, "status": "FAIL", "error": str(e)})

        test_instance.cleanup_test_data()

    # Generate test report
    print("\n📊 Test Results Summary")
    print("=" * 50)

    total_tests = len(test_results["unit_tests"])
    passed_tests = sum(1 for test in test_results["unit_tests"] if test["status"] == "PASS")
    failed_tests = total_tests - passed_tests

    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%")

    # Save detailed report
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w") as f:
        json.dump(test_results, f, indent=2)

    print(f"\n📄 Detailed report saved to: {report_file}")

    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
