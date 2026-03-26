from datetime import date
from app.models import Source

def test_get_sources_empty(client):
    response = client.get("/api/sources")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_update_source_not_found(client):
    response = client.put("/api/sources/99999", json={"enabled": False})
    assert response.status_code == 404
