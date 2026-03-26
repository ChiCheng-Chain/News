import json
from unittest.mock import patch, MagicMock
from app.pipeline.agents.analyzer import analyze
from app.pipeline.state import PipelineState, CleanArticle

def make_state(articles) -> PipelineState:
    return {
        "run_date": "2025-03-08", "triggered_by": "manual",
        "raw_articles": [], "clean_articles": articles,
        "topics": [], "digest_content": "", "error": None,
    }

def test_analyze_groups_articles_into_topics():
    articles = [
        CleanArticle(source="BBC", title="Ukraine peace talks begin", content="...", url="http://a.com", published_at="", language="en", sentiment="neutral"),
        CleanArticle(source="CCTV", title="乌克兰和平谈判开始", content="...", url="http://b.com", published_at="", language="zh", sentiment="neutral"),
    ]
    mock_content = json.dumps({
        "topics": [{"title": "乌克兰和平谈判", "article_indices": [0, 1], "is_blind_spot": False}]
    })
    mock_response = MagicMock()
    mock_response.choices[0].message.content = mock_content

    with patch("app.pipeline.agents.analyzer._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response

        state = make_state(articles)
        result = analyze(state)
        assert len(result["topics"]) == 1
        assert result["topics"][0]["title"] == "乌克兰和平谈判"
        assert len(result["topics"][0]["article_urls"]) == 2

def test_analyze_empty_input():
    state = make_state([])
    result = analyze(state)
    assert result["topics"] == []
