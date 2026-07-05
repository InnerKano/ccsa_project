import os

# Tests run in-process without Compose/Postgres — skip startup DB check.
os.environ.setdefault("SKIP_DB_CHECK", "true")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
