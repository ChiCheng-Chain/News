# backend/app/pipeline/agents/collector.py
import feedparser
from typing import List, Optional
from app.pipeline.state import PipelineState, RawArticle
from app.models import Source
from app.database import SessionLocal

def _parse_rss(url: str, language: str) -> List[RawArticle]:
    articles = []
    feed = feedparser.parse(url)
    for entry in feed.entries:
        articles.append(RawArticle(
            source=url,
            title=getattr(entry, "title", ""),
            content=getattr(entry, "summary", ""),
            url=getattr(entry, "link", ""),
            published_at=getattr(entry, "published", ""),
            language=language,
        ))
    return articles

def collect_news(state: PipelineState, rss_urls: Optional[List[str]] = None) -> PipelineState:
    articles: List[RawArticle] = []

    if rss_urls is not None:
        for url in rss_urls:
            articles.extend(_parse_rss(url, "en"))
    else:
        with SessionLocal() as db:
            sources = db.query(Source).filter(
                Source.enabled == True,
                Source.type == "rss"
            ).all()
            for source in sources:
                if source.url:
                    articles.extend(_parse_rss(source.url, source.language or "en"))

    return {**state, "raw_articles": articles}
