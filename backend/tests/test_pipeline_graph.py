from unittest.mock import patch, MagicMock
from app.pipeline.graph import run_pipeline

def test_run_pipeline_returns_state():
    base_state = {
        "run_date": "2025-03-08", "triggered_by": "manual",
        "raw_articles": [{"source": "BBC", "title": "Test", "content": "...",
                          "url": "http://a.com", "published_at": "", "language": "en"}],
        "clean_articles": [{"source": "BBC", "title": "Test", "content": "...",
                            "url": "http://a.com", "published_at": "", "language": "en", "sentiment": "neutral"}],
        "topics": [],
        "digest_content": "# Test Digest",
        "error": None,
    }

    with patch("app.pipeline.graph._pipeline") as mock_pipeline, \
         patch("app.pipeline.graph._save_to_db") as mock_save:

        mock_pipeline.invoke.return_value = base_state

        result = run_pipeline(run_date="2025-03-08", triggered_by="manual")
        assert result["digest_content"] == "# Test Digest"
        assert mock_save.called
