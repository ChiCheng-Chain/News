import json
from openai import OpenAI
from app.config import settings
from app.pipeline.state import PipelineState

def _get_client() -> OpenAI:
    return OpenAI(api_key=settings.volc_api_key, base_url=settings.volc_base_url)

SUMMARIZE_PROMPT = """你是资深新闻编辑，负责为读者生成每日新闻简报。

目标：打破信息茧房，让读者看到多元视角。

今日日期：{date}
今日事件包（JSON）：
{topics}

请生成一篇Markdown格式的每日简报，结构如下：

# {date} 每日简报

## 今日重大事件
（3-5个最重要事件，每个一段，包含中立摘要）

## 视角碰撞
（选取1-2个争议性事件，对比各方立场）

## 今日盲区
（标记为盲区的话题，帮助读者发现平时不关注的议题）

---
*数据来源：多元国际媒体 | 生成时间：{date}*
"""

def summarize(state: PipelineState) -> PipelineState:
    topics = state["topics"]
    if not topics:
        return {**state, "digest_content": f"# {state['run_date']} 每日简报\n\n今日暂无新闻数据。"}

    client = _get_client()
    topics_json = json.dumps(topics, ensure_ascii=False, default=str)

    response = client.chat.completions.create(
        model=settings.model_doubao_pro,
        messages=[{"role": "user", "content": SUMMARIZE_PROMPT.format(
            date=state["run_date"], topics=topics_json
        )}],
        temperature=0.7,
    )

    digest_content = response.choices[0].message.content
    return {**state, "digest_content": digest_content}
