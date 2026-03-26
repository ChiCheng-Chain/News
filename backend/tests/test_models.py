import pytest
from datetime import date, datetime
from sqlalchemy.exc import IntegrityError
from app.models import Article, Topic, Digest, Source, PipelineRun, ArticleTopic

def test_article_create(db_session):
    article = Article(
        source="BBC", title="Test", content="content",
        url="http://example.com", language="en", date=date.today()
    )
    db_session.add(article)
    db_session.commit()
    assert article.id is not None
    assert article.is_duplicate is False

def test_digest_date_unique(db_session):
    d1 = Digest(date=date(2025, 3, 8), content="test", triggered_by="manual")
    db_session.add(d1)
    db_session.commit()
    assert d1.id is not None

def test_source_create(db_session):
    s = Source(name="BBC", type="rss", url="http://feeds.bbci.co.uk/news/rss.xml", language="en")
    db_session.add(s)
    db_session.commit()
    assert s.enabled is True

def test_pipeline_run_create(db_session):
    run = PipelineRun(date=date.today(), status="running", current_step="collect")
    db_session.add(run)
    db_session.commit()
    assert run.id is not None

def test_digest_date_unique_constraint(db_session):
    """同一日期不能有两条digest记录"""
    d1 = Digest(date=date(2025, 6, 1), content="first", triggered_by="manual")
    db_session.add(d1)
    db_session.commit()

    d2 = Digest(date=date(2025, 6, 1), content="second", triggered_by="scheduled")
    db_session.add(d2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_topic_create(db_session):
    """Topic模型CRUD正常"""
    t = Topic(
        title="测试话题",
        summary="这是摘要",
        perspectives=[{"source": "BBC", "stance": "西方视角", "summary": "..."}],
        is_blind_spot=True,
        date=date.today()
    )
    db_session.add(t)
    db_session.commit()
    assert t.id is not None
    assert t.is_blind_spot is True

def test_article_topic_create(db_session):
    """ArticleTopic关联表CRUD正常"""
    article = Article(source="CNN", title="Test", content="...", url="http://x.com", language="en", date=date.today())
    topic = Topic(title="Topic", summary="sum", perspectives=[], is_blind_spot=False, date=date.today())
    db_session.add_all([article, topic])
    db_session.flush()

    at = ArticleTopic(article_id=article.id, topic_id=topic.id, viewpoint_label="中立视角")
    db_session.add(at)
    db_session.commit()
    assert at.viewpoint_label == "中立视角"
