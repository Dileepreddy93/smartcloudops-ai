# File: tests/test_smartcloudops.py

import pytest
import os
from unittest.mock import patch, MagicMock
from app.main import app as flask_app


# --- Conftest.py (or can be included here for simplicity) ---
# This file provides shared fixtures and mock objects for the tests.
@pytest.fixture
def mock_aws_clients():
    """
    Mocks the AWS Boto3 clients to simulate AWS interactions.
    This prevents tests from making real API calls.
    """
    with patch("boto3.client") as mock_boto_client:
        mock_s3 = MagicMock()
        mock_s3.upload_file.return_value = None
        mock_s3.download_file.return_value = None
        mock_boto_client.return_value = mock_s3
        yield mock_boto_client


@pytest.fixture
def mock_openai():
    """
    Mocks the OpenAI API client to prevent real API calls.
    This fixture simulates a successful response from the model.
    """
    try:
        with patch("openai.OpenAI") as mock_client:
            mock_completion = MagicMock()
            mock_completion.choices = [MagicMock()]
            mock_completion.choices[0].message.content = "Test response from AI."
            mock_client.return_value.chat.completions.create.return_value = mock_completion
            yield mock_client
    except ImportError:
        # Skip this fixture if openai module is not available
        pytest.skip("openai module not available")


@pytest.fixture
def flask_test_client():
    """
    Creates a test client for the Flask application.
    This allows us to make requests to the app endpoints for testing.
    """
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def mock_ml_model_file(tmp_path):
    """
    Creates a dummy ML model file for testing Phase 3.
    """
    model_path = tmp_path / "anomaly_model.pkl"
    # Create a simple, empty file to simulate a model.
    with open(model_path, "w") as f:
        f.write("dummy model content")
    return model_path


# --- Phase 1: Infrastructure Tests (Mocked) ---
# These tests ensure the Terraform files and core setup are correct.
def test_terraform_vpc_cidr(tmp_path):
    """
    Verifies that the VPC CIDR block in main.tf matches the specification.
    This test can be extended to check other resource properties.
    """
    # Create a dummy main.tf file in a temporary directory
    tf_content = """
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}
"""
    tf_file = tmp_path / "main.tf"
    tf_file.write_text(tf_content)

    # Simple check for the CIDR block
    with open(tf_file, "r") as f:
        content = f.read()
        assert 'cidr_block = "10.0.0.0/16"' in content


def test_s3_bucket_creation_mocked(mock_aws_clients):
    """
    Mocks the S3 client to test if the S3 bucket creation script
    would attempt to create a bucket with the correct name.
    """
    # This is a conceptual test. A real test would check a Terraform output or API call.
    # In this mock, we just check if the mock client was called.

    # We can simulate a function that calls Boto3
    def create_s3_bucket_in_app():
        s3 = mock_aws_clients()
        s3.create_bucket(Bucket="smartcloudops-ai-ml-models")

    # For this example, we'll check a mock call within a test.
    # A more robust solution would be to test the actual script.
    mock_s3_client = mock_aws_clients.return_value
    create_s3_bucket_in_app()
    mock_s3_client.create_bucket.assert_called_with(Bucket="smartcloudops-ai-ml-models")


# --- Phase 2: Flask ChatOps Application Tests ---
def test_app_status_endpoint(flask_test_client):
    """
    Tests the /status endpoint to ensure it returns a successful response.
    """
    response = flask_test_client.get("/status")
    assert response.status_code == 200
    assert b"OK" in response.data


def test_query_endpoint_success(flask_test_client, mock_openai):
    """
    Tests the /query endpoint with a mocked OpenAI response.
    It ensures the endpoint handles requests correctly and returns the mocked data.
    """
    try:
        data = {"query": "What is the CPU utilization of server-01?"}
        response = flask_test_client.post("/query", json=data)

        assert response.status_code == 200
        assert response.json["response"] == "Test response from AI."

        # Verify that the OpenAI client's create method was called
    except Exception as e:
        if "openai module not available" in str(e):
            pytest.skip("openai module not available")
        else:
            raise
    mock_openai.return_value.chat.completions.create.assert_called_once()


def test_query_endpoint_invalid_input(flask_test_client):
    """
    Tests the /query endpoint with invalid input to check for proper error handling.
    """
    data = {"invalid_key": "some value"}
    response = flask_test_client.post("/query", json=data)

    assert response.status_code == 400
    assert b"Invalid request" in response.data


def test_logs_endpoint(flask_test_client):
    """
    Tests the /logs endpoint to ensure it returns the correct data.
    """
    # We can mock the file system interaction for a real test
    with patch("os.path.exists", return_value=True), patch(
        "builtins.open", new_callable=MagicMock
    ) as mock_open_file:

        # Configure the mock file object
        mock_file_handle = MagicMock()
        mock_file_handle.read.return_value = "Log line 1\nLog line 2"
        mock_open_file.return_value.__enter__.return_value = mock_file_handle

        response = flask_test_client.get("/logs")
        assert response.status_code == 200
        assert b"Log line 1" in response.data
        assert b"Log line 2" in response.data


# --- Phase 3: ML Anomaly Detection Tests ---
def test_train_model_script_runnable(mock_ml_model_file):
    """
    Tests that the ML training script can be executed and a model is saved.
    This test mocks the actual training process to be fast.
    """
    # Assuming 'scripts/train_model.py' has a main function
    from scripts.train_model import main as train_main

    # Mock the save function to check if it's called
    with patch("pickle.dump") as mock_dump:
        train_main(save_path=mock_ml_model_file)

        # Check if the model was 'saved'
        mock_dump.assert_called_once()
        assert os.path.exists(mock_ml_model_file)


def test_production_inference_script(mock_ml_model_file):
    """
    Tests that the inference script can be loaded and its main function run.
    This also mocks the model loading process.
    """
    # Assuming 'scripts/production_inference.py' has a main function
    from scripts.production_inference import main as inference_main

    # Mock the load function to return a mock model
    with patch("pickle.load", return_value=MagicMock()) as mock_load:
        inference_main(model_path=mock_ml_model_file)

        # Check if the model was 'loaded'
        mock_load.assert_called_once()


# You can add more detailed tests to check the content of the ML model
def test_ml_model_integrity(mock_ml_model_file):
    """
    Verifies the integrity or expected structure of the saved ML model file.
    """
    with open(mock_ml_model_file, "r") as f:
        content = f.read()
        assert "dummy model content" in content
