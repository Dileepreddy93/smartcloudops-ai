import os
import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path for `import app`
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import create_app


@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.config.update({"TESTING": True})
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


