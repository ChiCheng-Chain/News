import json
from unittest.mock import patch, MagicMock
from app.pipeline.agents.aggregator import aggregate
from app.pipeline.state import PipelineState, TopicData, CleanArticle

def make_state(topics, articles) -> PipelineState:
    return {
        "run_date": "2025-03-08", "triggered_by": "manual",
        "raw_articles": [], "clean_articles": articles,
        "topics": topics, "digest_content": "", "error": None,
    }

def test_aggregate_fills_perspectives():
    articles = [
        CleanArticle(source="BBC", title="Ukraine talks", content="Western view...", url="http://a.com", published_at="", language="en", sentiment="neutral"),
        CleanArticle(source="CCTV", title="乌克兰谈判", content="中方视角...", url="http://b.com", published_at="", language="zh", sentiment="neutral"),
    ]
    topics = [TopicData(
        title="乌克兰和平谈判", summary="", perspectives=[],
        is_blind_spot=False, article_urls=["http://a.com", "http://b.com"]
    )]

    mock_content = json.dumps({
        "summary": "乌克兰和平谈判正式开始",
        "perspectives": [
            {"source": "BBC", "stance": "西方视角", "summary": "西方支持..."},
            {"source": "CCTV", "stance": "中方视角", "summary": "中方认为..."},
        ]
    })
    mock_response = MagicMock()
    mock_response.choices[0].message.content = mock_content

    with patch("app.pipeline.agents.aggregator._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response

        state = make_state(topics, articles)
        result = aggregate(state)
        assert result["topics"][0]["summary"] != ""
        assert len(result["topics"][0]["perspectives"]) == 2

def test_aggregate_empty_topics():
    state = make_state([], [])
    result = aggregate(state)
    assert result["topics"] == []
