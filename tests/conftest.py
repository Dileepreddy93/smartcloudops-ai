import os
import sys
from pathlib import Path

import pytest

# Set environment variables for resource optimization
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:128"

# Ensure project root is on sys.path for `import app`
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import after path setup - using try/except to handle import errors
try:
    from app.main import create_app  # noqa: E402
except ImportError:
    # Fallback for when app.main is not available
    create_app = None  # type: ignore


@pytest.fixture(scope="session")
def app():
    """Create Flask app with session scope to avoid repeated initialization."""
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "PRESERVE_CONTEXT_ON_EXCEPTION": False,
        }
    )
    return app


@pytest.fixture()
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope="session")
def nlp_service():
    """Create NLP service with session scope to avoid repeated model loading."""
    from app.services.nlp_chatops_service import NLPEnhancedChatOps

    return NLPEnhancedChatOps(use_lightweight_model=True)


@pytest.fixture(scope="session")
def aws_service():
    """Create AWS service with session scope."""
    from app.services.aws_integration_service import AWSIntegrationService

    return AWSIntegrationService()


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test."""
    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["FLASK_ENV"] = "testing"

    yield

    # Cleanup after test
    pass


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "phase5: marks tests as Phase 5 specific tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Mark Phase 5 tests
        if "phase5" in item.nodeid.lower():
            item.add_marker(pytest.mark.phase5)

        # Mark integration tests
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)

        # Mark unit tests
        if "unit" in item.nodeid.lower() or "test_" in item.nodeid.lower():
            item.add_marker(pytest.mark.unit)
