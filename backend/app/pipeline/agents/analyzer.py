import json
from openai import OpenAI
from app.config import settings
from app.pipeline.state import PipelineState, TopicData

def _get_client() -> OpenAI:
    return OpenAI(api_key=settings.volc_api_key, base_url=settings.volc_base_url)

ANALYZE_PROMPT = """你是新闻分析专家。分析以下新闻文章，完成两项任务：

1. **事件分组**：将报道同一事件的文章归为一组
2. **盲区标记**：标记那些非主流、容易被忽视的话题

文章列表：
{articles}

严格按以下JSON格式输出（不要加markdown代码块）：
{{
  "topics": [
    {{
      "title": "事件标题（中文）",
      "article_indices": [文章索引列表],
      "is_blind_spot": true/false
    }}
  ]
}}
"""

def analyze(state: PipelineState) -> PipelineState:
    articles = state["clean_articles"]
    if not articles:
        return {**state, "topics": []}

    client = _get_client()
    articles_json = json.dumps(
        [{"index": i, "title": a["title"], "source": a["source"], "language": a["language"]}
         for i, a in enumerate(articles)],
        ensure_ascii=False
    )

    response = client.chat.completions.create(
        model=settings.model_deepseek_r1,
        messages=[{"role": "user", "content": ANALYZE_PROMPT.format(articles=articles_json)}],
        temperature=0.3,
    )

    try:
        result = json.loads(response.choices[0].message.content)
        raw_topics = result.get("topics", [])
    except (json.JSONDecodeError, KeyError):
        raw_topics = []

    topics: list[TopicData] = []
    for t in raw_topics:
        topic_articles = [articles[i] for i in t.get("article_indices", []) if i < len(articles)]
        topics.append(TopicData(
            title=t["title"], summary="", perspectives=[],
            is_blind_spot=t.get("is_blind_spot", False),
            article_urls=[a["url"] for a in topic_articles],
        ))

    return {**state, "topics": topics}
