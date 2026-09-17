import os
import sys
import tempfile

import pytest

# Ensure a clean, isolated SQLite file for tests, configured BEFORE app import.
_tmp_db_fd, _tmp_db_path = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db_path}"
os.environ["OPENAI_API_KEY"] = ""  # force deterministic explanation path by default

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.database import init_db  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _setup_db():
    init_db()
    yield
    os.close(_tmp_db_fd)
    os.remove(_tmp_db_path)


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def auth_headers(client):
    email = "tester_%s@example.com" % os.urandom(4).hex()
    resp = client.post("/api/auth/register", json={"email": email, "password": "testpass123"})
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
