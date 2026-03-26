from unittest.mock import patch

def test_get_pipeline_status_idle(client):
    response = client.get("/api/pipeline/status")
    assert response.status_code == 200
    assert response.json()["status"] == "idle"

def test_trigger_starts_pipeline(client):
    with patch("app.api.trigger.threading.Thread") as mock_thread:
        mock_thread.return_value.start = lambda: None
        response = client.post("/api/trigger")
        assert response.status_code == 200
        assert "run_id" in response.json()
