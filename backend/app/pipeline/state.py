from typing import TypedDict, List, Optional

class RawArticle(TypedDict):
    source: str
    title: str
    content: str
    url: str
    published_at: str
    language: str

class CleanArticle(TypedDict):
    source: str
    title: str
    content: str
    url: str
    published_at: str
    language: str
    sentiment: str

class Perspective(TypedDict):
    source: str
    stance: str
    summary: str

class TopicData(TypedDict):
    title: str
    summary: str
    perspectives: List[Perspective]
    is_blind_spot: bool
    article_urls: List[str]

class PipelineState(TypedDict):
    run_date: str
    triggered_by: str
    raw_articles: List[RawArticle]
    clean_articles: List[CleanArticle]
    topics: List[TopicData]
    digest_content: str
    error: Optional[str]
