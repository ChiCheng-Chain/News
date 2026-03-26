from unittest.mock import patch, MagicMock
from app.pipeline.agents.summarizer import summarize
from app.pipeline.state import PipelineState, TopicData

def make_state(topics) -> PipelineState:
    return {
        "run_date": "2025-03-08", "triggered_by": "manual",
        "raw_articles": [], "clean_articles": [],
        "topics": topics, "digest_content": "", "error": None,
    }

def test_summarize_generates_markdown():
    topics = [TopicData(
        title="乌克兰和平谈判", summary="各方开始谈判",
        perspectives=[{"source": "BBC", "stance": "西方视角", "summary": "..."}],
        is_blind_spot=False, article_urls=[]
    )]
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "# 2025-03-08 每日简报\n\n## 今日重大事件\n..."

    with patch("app.pipeline.agents.summarizer._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response

        state = make_state(topics)
        result = summarize(state)
        assert result["digest_content"].startswith("#")
        assert len(result["digest_content"]) > 10

def test_summarize_empty_topics():
    state = make_state([])
    result = summarize(state)
    assert "暂无新闻数据" in result["digest_content"]
