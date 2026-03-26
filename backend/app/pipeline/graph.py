from datetime import date as date_type, datetime
from langgraph.graph import StateGraph, END
from app.pipeline.state import PipelineState
from app.pipeline.agents.collector import collect_news
from app.pipeline.agents.deduplicator import deduplicate
from app.pipeline.agents.analyzer import analyze
from app.pipeline.agents.aggregator import aggregate
from app.pipeline.agents.summarizer import summarize
from app.models import Article, Topic, ArticleTopic, Digest, PipelineRun
from app.database import SessionLocal

def _save_to_db(state: PipelineState) -> None:
    run_date = date_type.fromisoformat(state["run_date"])

    with SessionLocal() as db:
        saved_articles = {}
        for a in state["clean_articles"]:
            article = Article(
                source=a["source"], title=a["title"], content=a["content"],
                url=a["url"], language=a["language"], sentiment=a["sentiment"],
                date=run_date,
            )
            db.add(article)
            db.flush()
            saved_articles[a["url"]] = article.id

        topic_ids = []
        for t in state["topics"]:
            topic = Topic(
                title=t["title"], summary=t["summary"],
                perspectives=t["perspectives"], is_blind_spot=t["is_blind_spot"],
                date=run_date,
            )
            db.add(topic)
            db.flush()
            topic_ids.append(topic.id)

            for url in t["article_urls"]:
                if url in saved_articles:
                    db.add(ArticleTopic(article_id=saved_articles[url], topic_id=topic.id))

        existing = db.query(Digest).filter(Digest.date == run_date).first()
        if existing:
            existing.content = state["digest_content"]
            existing.topic_ids = topic_ids
            existing.triggered_by = state["triggered_by"]
        else:
            db.add(Digest(
                date=run_date, content=state["digest_content"],
                topic_ids=topic_ids, triggered_by=state["triggered_by"]
            ))

        db.commit()

def _make_pipeline():
    builder = StateGraph(PipelineState)
    builder.add_node("collect", collect_news)
    builder.add_node("deduplicate", deduplicate)
    builder.add_node("analyze", analyze)
    builder.add_node("aggregate", aggregate)
    builder.add_node("summarize", summarize)

    builder.set_entry_point("collect")
    builder.add_edge("collect", "deduplicate")
    builder.add_edge("deduplicate", "analyze")
    builder.add_edge("analyze", "aggregate")
    builder.add_edge("aggregate", "summarize")
    builder.add_edge("summarize", END)

    return builder.compile()

_pipeline = _make_pipeline()

def run_pipeline(run_date: str, triggered_by: str = "scheduled") -> PipelineState:
    initial_state: PipelineState = {
        "run_date": run_date,
        "triggered_by": triggered_by,
        "raw_articles": [],
        "clean_articles": [],
        "topics": [],
        "digest_content": "",
        "error": None,
    }
    final_state = _pipeline.invoke(initial_state)
    _save_to_db(final_state)
    return final_state
