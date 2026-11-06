from fastapi.testclient import TestClient

from pkmn_teambuilder.api import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}