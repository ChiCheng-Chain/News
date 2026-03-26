from unittest.mock import patch, MagicMock
from app.pipeline.agents.collector import collect_news
from app.pipeline.state import PipelineState

def make_state() -> PipelineState:
    return {
        "run_date": "2025-03-08", "triggered_by": "manual",
        "raw_articles": [], "clean_articles": [],
        "topics": [], "digest_content": "", "error": None,
    }

def test_collect_rss_returns_articles():
    mock_feed = MagicMock()
    mock_feed.entries = [
        MagicMock(title="Test Title", summary="Test Content",
                  link="http://example.com/1", published="Mon, 08 Mar 2025 10:00:00 +0000")
    ]
    with patch("feedparser.parse", return_value=mock_feed):
        state = make_state()
        result = collect_news(state, rss_urls=["http://feeds.bbci.co.uk/news/rss.xml"])
        assert len(result["raw_articles"]) == 1
        assert result["raw_articles"][0]["title"] == "Test Title"
        assert result["raw_articles"][0]["source"] == "http://feeds.bbci.co.uk/news/rss.xml"

def test_collect_handles_empty_feed():
    mock_feed = MagicMock()
    mock_feed.entries = []
    with patch("feedparser.parse", return_value=mock_feed):
        state = make_state()
        result = collect_news(state, rss_urls=["http://empty.example.com"])
        assert result["raw_articles"] == []
