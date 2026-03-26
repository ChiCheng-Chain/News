import json
from openai import OpenAI
from app.config import settings
from app.pipeline.state import PipelineState, TopicData, Perspective

def _get_client() -> OpenAI:
    return OpenAI(api_key=settings.volc_api_key, base_url=settings.volc_base_url)

AGGREGATE_PROMPT = """你是新闻聚合编辑。对于给定的事件，基于来自不同媒体的报道，生成：
1. 事件摘要（3-5句话，中立客观）
2. 各方视角（每个媒体来源的立场和核心观点）

事件标题：{title}

相关报道：
{articles}

严格按以下JSON格式输出（不要加markdown代码块）：
{{
  "summary": "事件摘要",
  "perspectives": [
    {{"source": "来源名称", "stance": "立场描述", "summary": "该来源的核心观点"}}
  ]
}}
"""

def aggregate(state: PipelineState) -> PipelineState:
    topics = state["topics"]
    articles = state["clean_articles"]
    if not topics:
        return state

    client = _get_client()
    url_to_article = {a["url"]: a for a in articles}

    enriched_topics: list[TopicData] = []
    for topic in topics:
        topic_articles = [url_to_article[url] for url in topic["article_urls"] if url in url_to_article]
        articles_text = json.dumps(
            [{"source": a["source"], "title": a["title"], "content": a["content"][:500]}
             for a in topic_articles],
            ensure_ascii=False
        )

        response = client.chat.completions.create(
            model=settings.model_deepseek_v3,
            messages=[{"role": "user", "content": AGGREGATE_PROMPT.format(
                title=topic["title"], articles=articles_text
            )}],
            temperature=0.3,
        )

        try:
            result = json.loads(response.choices[0].message.content)
            perspectives = [Perspective(**p) for p in result.get("perspectives", [])]
            enriched_topics.append({**topic,
                "summary": result.get("summary", ""),
                "perspectives": perspectives,
            })
        except (json.JSONDecodeError, KeyError, TypeError):
            enriched_topics.append(topic)

    return {**state, "topics": enriched_topics}
