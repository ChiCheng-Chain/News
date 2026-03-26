def test_get_topics_empty(client):
    response = client.get("/api/topics?date=2020-01-01")
    assert response.status_code == 200
    assert response.json() == []

def test_get_topic_not_found(client):
    response = client.get("/api/topics/99999")
    assert response.status_code == 404
