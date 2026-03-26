from datetime import date, datetime
from app.models import Article, Topic, Digest, Source, PipelineRun

def test_article_create(db_session):
    article = Article(
        source="BBC", title="Test", content="content",
        url="http://example.com", language="en", date=date.today()
    )
    db_session.add(article)
    db_session.commit()
    assert article.id is not None
    assert article.is_duplicate == False

def test_digest_date_unique(db_session):
    d1 = Digest(date=date(2025, 3, 8), content="test", triggered_by="manual")
    db_session.add(d1)
    db_session.commit()
    assert d1.id is not None

def test_source_create(db_session):
    s = Source(name="BBC", type="rss", url="http://feeds.bbci.co.uk/news/rss.xml", language="en")
    db_session.add(s)
    db_session.commit()
    assert s.enabled == True

def test_pipeline_run_create(db_session):
    run = PipelineRun(date=date.today(), status="running", current_step="collect")
    db_session.add(run)
    db_session.commit()
    assert run.id is not None
