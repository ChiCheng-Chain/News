from unittest.mock import patch, MagicMock
from app.pipeline.agents.deduplicator import deduplicate
from app.pipeline.state import PipelineState, RawArticle

def make_state(articles) -> PipelineState:
    return {
        "run_date": "2025-03-08", "triggered_by": "manual",
        "raw_articles": articles, "clean_articles": [],
        "topics": [], "digest_content": "", "error": None,
    }

def test_deduplicate_removes_similar_titles():
    articles = [
        RawArticle(source="BBC", title="Ukraine war latest", content="...", url="http://a.com/1", published_at="", language="en"),
        RawArticle(source="Reuters", title="Ukraine war latest today", content="...", url="http://b.com/1", published_at="", language="en"),
        RawArticle(source="CNN", title="Climate summit begins", content="...", url="http://c.com/1", published_at="", language="en"),
    ]
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"keep": [0, 2], "duplicates": [1], "sentiments": {"0": "neutral", "2": "positive"}}'

    with patch("app.pipeline.agents.deduplicator._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response

        state = make_state(articles)
        result = deduplicate(state)
        assert len(result["clean_articles"]) == 2
        assert result["clean_articles"][1]["sentiment"] == "positive"

def test_deduplicate_empty_input():
    state = make_state([])
    result = deduplicate(state)
    assert result["clean_articles"] == []
