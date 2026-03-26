import json
from openai import OpenAI
from app.config import settings
from app.pipeline.state import PipelineState, CleanArticle

def _get_client() -> OpenAI:
    return OpenAI(api_key=settings.volc_api_key, base_url=settings.volc_base_url)

DEDUP_PROMPT = """你是新闻去重助手。给定以下新闻文章列表（JSON格式），识别内容高度相似或重���的文章。

规则：
1. 标题语义相似度 > 80% 视为重复，只保留第一篇
2. 明显的标题党（含"震惊"、"你不知道的"等词）标记为低质量并移除
3. 对保留的文章判断情感：positive/negative/neutral

输入：
{articles}

严格按以下JSON格式输出（不要加markdown代码块）：
{{"keep": [索引列表], "duplicates": [索引列表], "sentiments": {{"0": "neutral", "2": "positive"}}}}
"""

def deduplicate(state: PipelineState) -> PipelineState:
    articles = state["raw_articles"]
    if not articles:
        return {**state, "clean_articles": []}

    client = _get_client()
    articles_json = json.dumps(
        [{"index": i, "title": a["title"], "source": a["source"]} for i, a in enumerate(articles)],
        ensure_ascii=False
    )

    response = client.chat.completions.create(
        model=settings.model_doubao_lite,
        messages=[{"role": "user", "content": DEDUP_PROMPT.format(articles=articles_json)}],
        temperature=0,
    )

    try:
        result = json.loads(response.choices[0].message.content)
        keep_indices = set(result.get("keep", range(len(articles))))
        sentiments = result.get("sentiments", {})
    except (json.JSONDecodeError, KeyError):
        keep_indices = set(range(len(articles)))
        sentiments = {}

    clean_articles = []
    for i in sorted(keep_indices):
        a = articles[i]
        clean_articles.append(CleanArticle(
            source=a["source"], title=a["title"], content=a["content"],
            url=a["url"], published_at=a["published_at"], language=a["language"],
            sentiment=sentiments.get(str(i), "neutral"),
        ))

    return {**state, "clean_articles": clean_articles}
