from fastapi.testclient import TestClient

from src.api.ba_sessions import router
from src.services.ba_session_manager import ba_session_manager
from src.main import app


def setup_module(module):
    ba_session_manager.clear()


def test_list_sessions_empty():
    ba_session_manager.clear()
    client = TestClient(app)
    response = client.get("/ba-sessions")
    assert response.status_code == 200
    assert response.json() == {"sessions": []}


def test_get_session_not_found():
    ba_session_manager.clear()
    client = TestClient(app)
    response = client.get("/ba-sessions/nonexistent")
    assert response.status_code == 404

