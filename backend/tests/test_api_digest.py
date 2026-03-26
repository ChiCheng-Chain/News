from datetime import date
from app.models import Digest

def test_get_digest_not_found(client):
    response = client.get("/api/digest?date=2020-01-01")
    assert response.status_code == 404

def test_get_digest_returns_data(client, db_session):
    d = Digest(date=date(2025, 3, 8), content="# Test", triggered_by="manual", topic_ids=[])
    db_session.add(d)
    db_session.flush()
    response = client.get("/api/digest?date=2025-03-08")
    assert response.status_code == 200
    assert response.json()["content"] == "# Test"
