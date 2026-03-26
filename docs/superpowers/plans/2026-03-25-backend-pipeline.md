# 打破信息茧房 · 后端 + Pipeline 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建后端 FastAPI 服务 + LangGraph 多 Agent Pipeline，支持定时（每晚20:00）和手动触发新闻采集、分析、聚合、生成每日简报，全部数据持久化到本地 MySQL。

**Architecture:** FastAPI 作为 HTTP 层暴露 REST API，APScheduler 内嵌处理定时任务，LangGraph 定义有向图 Pipeline（采集→去重→分析→聚合→总结），每个 Agent 是图中一个节点，通过共享 State 传递数据。

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.x, PyMySQL, LangGraph, LangChain, APScheduler, feedparser, httpx, openai（兼容火山引擎API）, pytest, pytest-asyncio

**Spec:** `docs/superpowers/specs/2026-03-25-news-anti-bubble-design.md`

---

## 文件结构

```
backend/
├── app/
│   ├── main.py                        # FastAPI app 入口，挂载路由和scheduler
│   ├── config.py                      # 从.env读取配置（Settings类）
│   ├── database.py                    # SQLAlchemy engine + SessionLocal + Base
│   ├── models/
│   │   ├── __init__.py                # 导出所有模型
│   │   ├── article.py                 # Article 模型
│   │   ├── topic.py                   # Topic 模型
│   │   ├── article_topic.py           # ArticleTopic 关联模型
│   │   ├── digest.py                  # Digest 模型
│   │   ├── source.py                  # Source 模型
│   │   └── pipeline_run.py            # PipelineRun 模型
│   ├── api/
│   │   ├── __init__.py
│   │   ├── digest.py                  # GET /api/digest
│   │   ├── topics.py                  # GET /api/topics, GET /api/topics/{id}
│   │   ├── trigger.py                 # POST /api/trigger, GET /api/pipeline/status
│   │   └── sources.py                 # GET/PUT /api/sources
│   ├── pipeline/
│   │   ├── state.py                   # PipelineState TypedDict（节点间共享状态）
│   │   ├── graph.py                   # LangGraph 主图定义，串联5个Agent节点
│   │   └── agents/
│   │       ├── collector.py           # 采集Agent：RSS/API拉取原始新闻
│   │       ├── deduplicator.py        # 去重Agent：Doubao-lite语义去重+过滤
│   │       ├── analyzer.py            # 分析Agent：DeepSeek-R1视角分析+盲区标记
│   │       ├── aggregator.py          # 聚合Agent：DeepSeek-V3.2生成事件包
│   │       └── summarizer.py          # 总结Agent：Doubao-pro生成每日简报
│   └── scheduler.py                   # APScheduler，每晚20:00触发pipeline
├── tests/
│   ├── conftest.py                    # pytest fixtures（测试DB session，mock LLM）
│   ├── test_models.py                 # 模型CRUD测试
│   ├── test_api_digest.py
│   ├── test_api_topics.py
│   ├── test_api_trigger.py
│   ├── test_api_sources.py
│   ├── test_agent_collector.py
│   ├── test_agent_deduplicator.py
│   ├── test_agent_analyzer.py
│   ├── test_agent_aggregator.py
│   ├── test_agent_summarizer.py
│   └── test_pipeline_graph.py
├── init_db.py                         # 一次性：建表 + 初始化来源数据
├── .env.example
└── requirements.txt
```

---

## Task 1: 项目初始化 & 依赖配置

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py`（空文件）

- [ ] **Step 1: 创建 requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.35
pymysql==1.1.1
cryptography==43.0.1
python-dotenv==1.0.1
pydantic-settings==2.5.2
apscheduler==3.10.4
langgraph==0.2.28
langchain==0.3.1
langchain-openai==0.2.1
openai==1.51.0
feedparser==6.0.11
httpx==0.27.2
pytest==8.3.3
pytest-asyncio==0.24.0
```

- [ ] **Step 2: 创建 .env.example**

```
MYSQL_URL=mysql+pymysql://root:password@localhost:3306/akc_news
VOLC_API_KEY=你的火山引擎API Key
VOLC_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# 模型端点ID
MODEL_DOUBAO_LITE=ep-20250627102538-kbh7j
MODEL_DOUBAO_PRO=ep-20250627105312-62njr
MODEL_DEEPSEEK_R1=ep-20250627151708-wfrsp
MODEL_DEEPSEEK_V3=ep-20251222104545-wff8z
```

- [ ] **Step 3: 复制 .env.example 为 .env，填入真实值**

```bash
cp backend/.env.example backend/.env
# 编辑 .env 填入真实 MYSQL_URL 和 VOLC_API_KEY
```

- [ ] **Step 4: 创建虚拟环境并安装依赖**

```bash
cd backend
python3.12 -m venv .venv
.venv/Scripts/activate   # Windows
pip install -r requirements.txt
```

- [ ] **Step 5: 创建空的 __init__.py 文件**

```bash
mkdir -p app/models app/api app/pipeline/agents tests
touch app/__init__.py app/models/__init__.py app/api/__init__.py
touch app/pipeline/__init__.py app/pipeline/agents/__init__.py
```

- [ ] **Step 6: Commit**

```bash
git add backend/
git commit -m "chore: 初始化后端项目结构和依赖配置"
```

---

## Task 2: 配置 & 数据库连接

**Files:**
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`

- [ ] **Step 1: 编写 config.py**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mysql_url: str
    volc_api_key: str
    volc_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    model_doubao_lite: str
    model_doubao_pro: str
    model_deepseek_r1: str
    model_deepseek_v3: str

    class Config:
        env_file = ".env"

settings = Settings()
```

- [ ] **Step 2: 编写 database.py**

```python
# backend/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

engine = create_engine(settings.mysql_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 3: 编写测试 tests/conftest.py**

```python
# backend/tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(test_engine):
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()
```

- [ ] **Step 4: 运行测试（目前只验证配置加载不报错）**

```bash
cd backend
pytest tests/ -v
```

Expected: 0 errors（无测试文件时直接pass）

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/app/database.py backend/tests/conftest.py
git commit -m "feat: 添加配置管理和数据库连接层"
```

---

## Task 3: 数据库模型

**Files:**
- Create: `backend/app/models/article.py`
- Create: `backend/app/models/topic.py`
- Create: `backend/app/models/article_topic.py`
- Create: `backend/app/models/digest.py`
- Create: `backend/app/models/source.py`
- Create: `backend/app/models/pipeline_run.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/tests/test_models.py`

- [ ] **Step 1: 编写失败测试 test_models.py**

```python
# backend/tests/test_models.py
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
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
pytest tests/test_models.py -v
```

Expected: FAIL with "ImportError: cannot import name 'Article'"

- [ ] **Step 3: 编写 article.py**

```python
# backend/app/models/article.py
from sqlalchemy import Column, BigInteger, String, Text, DateTime, Date, Boolean, Enum
from sqlalchemy.sql import func
from app.database import Base

class Article(Base):
    __tablename__ = "articles"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source = Column(String(100))
    title = Column(String(500))
    content = Column(Text)
    url = Column(String(1000))
    published_at = Column(DateTime)
    language = Column(String(10))
    sentiment = Column(Enum("positive", "negative", "neutral"))
    is_duplicate = Column(Boolean, default=False)
    date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
```

- [ ] **Step 4: 编写 topic.py**

```python
# backend/app/models/topic.py
from sqlalchemy import Column, BigInteger, String, Text, Date, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from app.database import Base

class Topic(Base):
    __tablename__ = "topics"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(500))
    summary = Column(Text)
    perspectives = Column(JSON)  # [{"source":"BBC","stance":"西方视角","summary":"..."}]
    is_blind_spot = Column(Boolean, default=False)
    date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
```

- [ ] **Step 5: 编写 article_topic.py**

```python
# backend/app/models/article_topic.py
from sqlalchemy import Column, BigInteger, String, ForeignKey
from app.database import Base

class ArticleTopic(Base):
    __tablename__ = "article_topics"
    article_id = Column(BigInteger, ForeignKey("articles.id"), primary_key=True)
    topic_id = Column(BigInteger, ForeignKey("topics.id"), primary_key=True)
    viewpoint_label = Column(String(100))
```

- [ ] **Step 6: 编写 digest.py**

```python
# backend/app/models/digest.py
from sqlalchemy import Column, BigInteger, Date, Text, JSON, Enum, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base

class Digest(Base):
    __tablename__ = "digests"
    __table_args__ = (UniqueConstraint("date"),)
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True)
    content = Column(Text)
    topic_ids = Column(JSON)
    triggered_by = Column(Enum("scheduled", "manual"))
    created_at = Column(DateTime, server_default=func.now())
```

- [ ] **Step 7: 编写 source.py**

```python
# backend/app/models/source.py
from sqlalchemy import Column, BigInteger, String, Boolean, Enum
from app.database import Base

class Source(Base):
    __tablename__ = "sources"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100))
    type = Column(Enum("rss", "api"))
    url = Column(String(500))
    language = Column(String(10))
    enabled = Column(Boolean, default=True)
```

- [ ] **Step 8: 编写 pipeline_run.py**

```python
# backend/app/models/pipeline_run.py
from sqlalchemy import Column, BigInteger, Date, Enum, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    date = Column(Date)
    status = Column(Enum("running", "done", "failed"))
    current_step = Column(String(50))
    started_at = Column(DateTime, server_default=func.now())
    finished_at = Column(DateTime)
    error_msg = Column(Text)
```

- [ ] **Step 9: 编写 models/__init__.py**

```python
# backend/app/models/__init__.py
from .article import Article
from .topic import Topic
from .article_topic import ArticleTopic
from .digest import Digest
from .source import Source
from .pipeline_run import PipelineRun

__all__ = ["Article", "Topic", "ArticleTopic", "Digest", "Source", "PipelineRun"]
```

- [ ] **Step 10: 运行测试，确认通过**

```bash
pytest tests/test_models.py -v
```

Expected: 4 PASSED

- [ ] **Step 11: Commit**

```bash
git add backend/app/models/ backend/tests/test_models.py
git commit -m "feat: 添加数据库模型（6张核心表）"
```

---

## Task 4: 数据库初始化脚本

**Files:**
- Create: `backend/init_db.py`

- [ ] **Step 1: 编写 init_db.py**

```python
# backend/init_db.py
"""一次性脚本：建表 + 初始化新闻来源数据"""
from app.database import engine, Base
from app.models import Source
from sqlalchemy.orm import Session
import app.models  # noqa: 触发所有模型注册

def init():
    Base.metadata.create_all(engine)
    print("✓ 数据库表创建完成")

    sources = [
        Source(name="NewsAPI", type="api", url="https://newsapi.org/v2/top-headlines", language="en", enabled=True),
        Source(name="GDELT", type="api", url="https://api.gdeltproject.org/api/v2/doc/doc", language="multi", enabled=True),
        Source(name="BBC News RSS", type="rss", url="http://feeds.bbci.co.uk/news/rss.xml", language="en", enabled=True),
        Source(name="Reuters RSS", type="rss", url="https://feeds.reuters.com/reuters/topNews", language="en", enabled=True),
        Source(name="微信公众号RSS代理", type="rss", url="", language="zh", enabled=False),  # URL待配置
    ]

    with Session(engine) as session:
        existing = session.query(Source).count()
        if existing == 0:
            session.add_all(sources)
            session.commit()
            print(f"✓ 初始化 {len(sources)} 个新闻来源")
        else:
            print(f"跳过：已存在 {existing} 个来源")

if __name__ == "__main__":
    init()
```

- [ ] **Step 2: 运行初始化脚本**

```bash
cd backend
python init_db.py
```

Expected:
```
✓ 数据库表创建完成
✓ 初始化 5 个新闻来源
```

- [ ] **Step 3: Commit**

```bash
git add backend/init_db.py
git commit -m "feat: 添加数据库初始化脚本（建表+种子数据）"
```

---

## Task 5: Pipeline State 定义

**Files:**
- Create: `backend/app/pipeline/state.py`

- [ ] **Step 1: 编写 state.py**

```python
# backend/app/pipeline/state.py
from typing import TypedDict, List, Optional
from datetime import date

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
    sentiment: str           # positive/negative/neutral

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
    run_date: str                          # YYYY-MM-DD
    triggered_by: str                     # scheduled/manual
    raw_articles: List[RawArticle]        # 采集Agent输出
    clean_articles: List[CleanArticle]    # 去重Agent输出
    topics: List[TopicData]               # 聚合Agent输出
    digest_content: str                   # 总结Agent输出
    error: Optional[str]
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/pipeline/state.py
git commit -m "feat: 定义LangGraph Pipeline共享状态结构"
```

---

## Task 6: 采集 Agent

**Files:**
- Create: `backend/app/pipeline/agents/collector.py`
- Create: `backend/tests/test_agent_collector.py`

- [ ] **Step 1: 编写失败测试**

```python
# backend/tests/test_agent_collector.py
from unittest.mock import patch, MagicMock
from app.pipeline.agents.collector import collect_news
from app.pipeline.state import PipelineState

def make_state() -> PipelineState:
    return {
        "run_date": "2025-03-08",
        "triggered_by": "manual",
        "raw_articles": [],
        "clean_articles": [],
        "topics": [],
        "digest_content": "",
        "error": None,
    }

def test_collect_rss_returns_articles():
    """采集Agent能从RSS源解析出文章"""
    mock_feed = MagicMock()
    mock_feed.entries = [
        MagicMock(
            title="Test Title",
            summary="Test Content",
            link="http://example.com/1",
            published="Mon, 08 Mar 2025 10:00:00 +0000",
        )
    ]
    with patch("feedparser.parse", return_value=mock_feed):
        state = make_state()
        result = collect_news(state, rss_urls=["http://feeds.bbci.co.uk/news/rss.xml"])
        assert len(result["raw_articles"]) == 1
        assert result["raw_articles"][0]["title"] == "Test Title"
        assert result["raw_articles"][0]["source"] == "http://feeds.bbci.co.uk/news/rss.xml"

def test_collect_handles_empty_feed():
    """采集Agent处理空RSS源不报错"""
    mock_feed = MagicMock()
    mock_feed.entries = []
    with patch("feedparser.parse", return_value=mock_feed):
        state = make_state()
        result = collect_news(state, rss_urls=["http://empty.example.com"])
        assert result["raw_articles"] == []
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
pytest tests/test_agent_collector.py -v
```

Expected: FAIL with "ImportError"

- [ ] **Step 3: 编写 collector.py**

```python
# backend/app/pipeline/agents/collector.py
import feedparser
from datetime import datetime
from typing import List
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

def collect_news(state: PipelineState, rss_urls: List[str] = None) -> PipelineState:
    """
    从数据库中读取已启用的RSS来源并采集新闻。
    rss_urls 参数仅用于测试注入，生产环境从DB读取。
    """
    articles: List[RawArticle] = []

    if rss_urls is not None:
        # 测试模式：直接使用传入的URL列表
        for url in rss_urls:
            articles.extend(_parse_rss(url, "en"))
    else:
        # 生产模式：从数据库读取启用的来源
        with SessionLocal() as db:
            sources = db.query(Source).filter(
                Source.enabled == True,
                Source.type == "rss"
            ).all()
            for source in sources:
                if source.url:
                    articles.extend(_parse_rss(source.url, source.language or "en"))

    return {**state, "raw_articles": articles}
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
pytest tests/test_agent_collector.py -v
```

Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/app/pipeline/agents/collector.py backend/tests/test_agent_collector.py
git commit -m "feat: 实现采集Agent（RSS抓取）"
```

---

## Task 7: 去重/过滤 Agent

**Files:**
- Create: `backend/app/pipeline/agents/deduplicator.py`
- Create: `backend/tests/test_agent_deduplicator.py`

> 该Agent使用 Doubao-lite-128k 做语义去重。火山引擎API兼容 OpenAI 格式，使用 `openai` 库并设置自定义 base_url。

- [ ] **Step 1: 编写失败测试**

```python
# backend/tests/test_agent_deduplicator.py
from unittest.mock import patch, MagicMock
from app.pipeline.agents.deduplicator import deduplicate
from app.pipeline.state import PipelineState, RawArticle

def make_state_with_articles(articles) -> PipelineState:
    return {
        "run_date": "2025-03-08",
        "triggered_by": "manual",
        "raw_articles": articles,
        "clean_articles": [],
        "topics": [],
        "digest_content": "",
        "error": None,
    }

def test_deduplicate_removes_similar_titles():
    """去重Agent移除标题高度相似的文章"""
    articles = [
        RawArticle(source="BBC", title="Ukraine war latest news", content="...", url="http://a.com/1", published_at="", language="en"),
        RawArticle(source="Reuters", title="Ukraine war latest news today", content="...", url="http://b.com/1", published_at="", language="en"),
        RawArticle(source="CNN", title="Climate summit begins in Paris", content="...", url="http://c.com/1", published_at="", language="en"),
    ]
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"keep": [0, 2], "duplicates": [1]}'

    with patch("openai.OpenAI") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response

        state = make_state_with_articles(articles)
        result = deduplicate(state)
        assert len(result["clean_articles"]) == 2

def test_deduplicate_empty_input():
    """去重Agent处理空输入不报错"""
    state = make_state_with_articles([])
    result = deduplicate(state)
    assert result["clean_articles"] == []
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
pytest tests/test_agent_deduplicator.py -v
```

Expected: FAIL with "ImportError"

- [ ] **Step 3: 编写 deduplicator.py**

```python
# backend/app/pipeline/agents/deduplicator.py
import json
from openai import OpenAI
from app.config import settings
from app.pipeline.state import PipelineState, CleanArticle

def _get_client() -> OpenAI:
    return OpenAI(
        api_key=settings.volc_api_key,
        base_url=settings.volc_base_url,
    )

DEDUP_PROMPT = """你是新闻去重助手。给定以下新闻文章列表（JSON格式），识别内容高度相似或重复的文章。

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
    for i in keep_indices:
        a = articles[i]
        clean_articles.append(CleanArticle(
            source=a["source"],
            title=a["title"],
            content=a["content"],
            url=a["url"],
            published_at=a["published_at"],
            language=a["language"],
            sentiment=sentiments.get(str(i), "neutral"),
        ))

    return {**state, "clean_articles": clean_articles}
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
pytest tests/test_agent_deduplicator.py -v
```

Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/app/pipeline/agents/deduplicator.py backend/tests/test_agent_deduplicator.py
git commit -m "feat: 实现去重Agent（Doubao-lite语义去重）"
```

---

## Task 8: 分析 Agent

**Files:**
- Create: `backend/app/pipeline/agents/analyzer.py`
- Create: `backend/tests/test_agent_analyzer.py`

> 使用 DeepSeek-R1，识别对立视角 + 标记盲区话题。

- [ ] **Step 1: 编写失败测试**

```python
# backend/tests/test_agent_analyzer.py
from unittest.mock import patch, MagicMock
import json
from app.pipeline.agents.analyzer import analyze
from app.pipeline.state import PipelineState, CleanArticle

def make_state(articles) -> PipelineState:
    return {
        "run_date": "2025-03-08", "triggered_by": "manual",
        "raw_articles": [], "clean_articles": articles,
        "topics": [], "digest_content": "", "error": None,
    }

def test_analyze_groups_articles_into_topics():
    """分析Agent能将文章按事件分组"""
    articles = [
        CleanArticle(source="BBC", title="Ukraine peace talks begin", content="...", url="http://a.com", published_at="", language="en", sentiment="neutral"),
        CleanArticle(source="CCTV", title="乌克兰和平谈判开始", content="...", url="http://b.com", published_at="", language="zh", sentiment="neutral"),
    ]
    mock_content = json.dumps({
        "topics": [{
            "title": "Ukraine Peace Talks",
            "article_indices": [0, 1],
            "is_blind_spot": False
        }]
    })
    mock_response = MagicMock()
    mock_response.choices[0].message.content = mock_content

    with patch("openai.OpenAI") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response

        state = make_state(articles)
        result = analyze(state)
        assert len(result["topics"]) == 1
        assert result["topics"][0]["title"] == "Ukraine Peace Talks"
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
pytest tests/test_agent_analyzer.py -v
```

Expected: FAIL with "ImportError"

- [ ] **Step 3: 编写 analyzer.py**

```python
# backend/app/pipeline/agents/analyzer.py
import json
from openai import OpenAI
from app.config import settings
from app.pipeline.state import PipelineState, TopicData

def _get_client() -> OpenAI:
    return OpenAI(api_key=settings.volc_api_key, base_url=settings.volc_base_url)

ANALYZE_PROMPT = """你是新闻分析专家。分析以下新闻文章，完成两项任务：

1. **事件分组**：将报道同一事件的文章归为一组
2. **盲区标记**：标记那些非主流、容易被忽视的话题（如：小国政治、科学发现、环境议题、非西方视角的重大事件）

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
            title=t["title"],
            summary="",          # 由聚合Agent填充
            perspectives=[],     # 由聚合Agent填充
            is_blind_spot=t.get("is_blind_spot", False),
            article_urls=[a["url"] for a in topic_articles],
        ))

    return {**state, "topics": topics}
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
pytest tests/test_agent_analyzer.py -v
```

Expected: 1 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/app/pipeline/agents/analyzer.py backend/tests/test_agent_analyzer.py
git commit -m "feat: 实现分析Agent（DeepSeek-R1事件分组+盲区标记）"
```

---

## Task 9: 聚合 Agent

**Files:**
- Create: `backend/app/pipeline/agents/aggregator.py`
- Create: `backend/tests/test_agent_aggregator.py`

> 使用 DeepSeek-V3.2，为每个事件包生成摘要和各方视角。

- [ ] **Step 1: 编写失败测试**

```python
# backend/tests/test_agent_aggregator.py
from unittest.mock import patch, MagicMock
import json
from app.pipeline.agents.aggregator import aggregate
from app.pipeline.state import PipelineState, TopicData, CleanArticle

def make_state(topics, articles) -> PipelineState:
    return {
        "run_date": "2025-03-08", "triggered_by": "manual",
        "raw_articles": [], "clean_articles": articles,
        "topics": topics, "digest_content": "", "error": None,
    }

def test_aggregate_fills_perspectives():
    """聚合Agent为每个主题填充摘要和视角"""
    articles = [
        CleanArticle(source="BBC", title="Ukraine talks", content="Western view...", url="http://a.com", published_at="", language="en", sentiment="neutral"),
        CleanArticle(source="CCTV", title="乌克兰谈判", content="中方视角...", url="http://b.com", published_at="", language="zh", sentiment="neutral"),
    ]
    topics = [TopicData(
        title="乌克兰和平谈判", summary="", perspectives=[],
        is_blind_spot=False, article_urls=["http://a.com", "http://b.com"]
    )]

    mock_content = json.dumps({
        "summary": "乌克兰和平谈判正式开始，各方立场存在分歧",
        "perspectives": [
            {"source": "BBC", "stance": "西方视角", "summary": "西方支持..."},
            {"source": "CCTV", "stance": "中方视角", "summary": "中方认为..."},
        ]
    })
    mock_response = MagicMock()
    mock_response.choices[0].message.content = mock_content

    with patch("openai.OpenAI") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response

        state = make_state(topics, articles)
        result = aggregate(state)
        assert result["topics"][0]["summary"] != ""
        assert len(result["topics"][0]["perspectives"]) == 2
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
pytest tests/test_agent_aggregator.py -v
```

- [ ] **Step 3: 编写 aggregator.py**

```python
# backend/app/pipeline/agents/aggregator.py
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
        except (json.JSONDecodeError, KeyError):
            enriched_topics.append(topic)

    return {**state, "topics": enriched_topics}
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
pytest tests/test_agent_aggregator.py -v
```

Expected: 1 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/app/pipeline/agents/aggregator.py backend/tests/test_agent_aggregator.py
git commit -m "feat: 实现聚合Agent（DeepSeek-V3.2生成事件包和多方视角）"
```

---

## Task 10: 总结 Agent

**Files:**
- Create: `backend/app/pipeline/agents/summarizer.py`
- Create: `backend/tests/test_agent_summarizer.py`

> 使用 Doubao-pro-128k，生成每日简报 Markdown 文章。

- [ ] **Step 1: 编写失败测试**

```python
# backend/tests/test_agent_summarizer.py
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
    """总结Agent生成包含Markdown内容的每日简报"""
    topics = [TopicData(
        title="乌克兰和平谈判", summary="各方开始谈判",
        perspectives=[{"source": "BBC", "stance": "西方视角", "summary": "..."}],
        is_blind_spot=False, article_urls=[]
    )]
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "# 2025-03-08 每日简报\n\n## 今日重大事件\n..."

    with patch("openai.OpenAI") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response

        state = make_state(topics)
        result = summarize(state)
        assert result["digest_content"].startswith("#")
        assert len(result["digest_content"]) > 10
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
pytest tests/test_agent_summarizer.py -v
```

- [ ] **Step 3: 编写 summarizer.py**

```python
# backend/app/pipeline/agents/summarizer.py
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
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
pytest tests/test_agent_summarizer.py -v
```

Expected: 1 PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/app/pipeline/agents/summarizer.py backend/tests/test_agent_summarizer.py
git commit -m "feat: 实现总结Agent（Doubao-pro生成每日简报）"
```

---

## Task 11: LangGraph 主图 + 数据持久化

**Files:**
- Create: `backend/app/pipeline/graph.py`
- Create: `backend/tests/test_pipeline_graph.py`

- [ ] **Step 1: 编写失败测试**

```python
# backend/tests/test_pipeline_graph.py
from unittest.mock import patch, MagicMock
from datetime import date
from app.pipeline.graph import run_pipeline

def test_run_pipeline_returns_state():
    """Pipeline完整运行返回包含digest_content的状态"""
    mock_articles = [
        {"source": "BBC", "title": "Test News", "content": "...",
         "url": "http://a.com", "published_at": "", "language": "en"}
    ]

    with patch("app.pipeline.agents.collector.collect_news") as mock_collect, \
         patch("app.pipeline.agents.deduplicator.deduplicate") as mock_dedup, \
         patch("app.pipeline.agents.analyzer.analyze") as mock_analyze, \
         patch("app.pipeline.agents.aggregator.aggregate") as mock_aggregate, \
         patch("app.pipeline.agents.summarizer.summarize") as mock_summarize, \
         patch("app.pipeline.graph._save_to_db") as mock_save:

        base_state = {
            "run_date": "2025-03-08", "triggered_by": "manual",
            "raw_articles": mock_articles, "clean_articles": mock_articles,
            "topics": [], "digest_content": "# Test Digest", "error": None
        }
        mock_collect.return_value = base_state
        mock_dedup.return_value = base_state
        mock_analyze.return_value = base_state
        mock_aggregate.return_value = base_state
        mock_summarize.return_value = base_state

        result = run_pipeline(run_date="2025-03-08", triggered_by="manual")
        assert result["digest_content"] == "# Test Digest"
        assert mock_save.called
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
pytest tests/test_pipeline_graph.py -v
```

- [ ] **Step 3: 编写 graph.py**

```python
# backend/app/pipeline/graph.py
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
    """将Pipeline结果持久化到MySQL"""
    run_date = date_type.fromisoformat(state["run_date"])

    with SessionLocal() as db:
        # 保存文章
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

        # 保存主题
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

        # 保存简报（upsert by date）
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
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
pytest tests/test_pipeline_graph.py -v
```

Expected: 1 PASSED

- [ ] **Step 5: 运行所有测试**

```bash
pytest tests/ -v
```

Expected: 全部 PASSED

- [ ] **Step 6: Commit**

```bash
git add backend/app/pipeline/graph.py backend/tests/test_pipeline_graph.py
git commit -m "feat: 实现LangGraph主图，串联5个Agent节点并持久化结果"
```

---

## Task 12: 调度器

**Files:**
- Create: `backend/app/scheduler.py`

- [ ] **Step 1: 编写 scheduler.py**

```python
# backend/app/scheduler.py
from datetime import date
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.pipeline.graph import run_pipeline
from app.models import PipelineRun
from app.database import SessionLocal

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

def _run_daily():
    today = date.today().isoformat()
    with SessionLocal() as db:
        # 防重复：今天已有running/done状态则跳过
        existing = db.query(PipelineRun).filter(
            PipelineRun.date == date.today(),
            PipelineRun.status.in_(["running", "done"])
        ).first()
        if existing:
            return

        run = PipelineRun(date=date.today(), status="running", current_step="collect")
        db.add(run)
        db.commit()
        run_id = run.id

    try:
        run_pipeline(run_date=today, triggered_by="scheduled")
        with SessionLocal() as db:
            run = db.get(PipelineRun, run_id)
            run.status = "done"
            run.current_step = "done"
            from datetime import datetime
            run.finished_at = datetime.now()
            db.commit()
    except Exception as e:
        with SessionLocal() as db:
            run = db.get(PipelineRun, run_id)
            run.status = "failed"
            run.error_msg = str(e)
            from datetime import datetime
            run.finished_at = datetime.now()
            db.commit()

def start_scheduler():
    scheduler.add_job(_run_daily, CronTrigger(hour=20, minute=0, timezone="Asia/Shanghai"))
    scheduler.start()

def stop_scheduler():
    scheduler.shutdown()
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/scheduler.py
git commit -m "feat: 添加APScheduler定时任务（每晚20:00）"
```

---

## Task 13: REST API 端点

**Files:**
- Create: `backend/app/api/digest.py`
- Create: `backend/app/api/topics.py`
- Create: `backend/app/api/trigger.py`
- Create: `backend/app/api/sources.py`
- Create: `backend/tests/test_api_digest.py`
- Create: `backend/tests/test_api_topics.py`
- Create: `backend/tests/test_api_trigger.py`
- Create: `backend/tests/test_api_sources.py`

- [ ] **Step 1: 编写 digest API 测试**

```python
# backend/tests/test_api_digest.py
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

def test_get_digest_returns_404_when_no_data(client):
    response = client.get("/api/digest?date=2020-01-01")
    assert response.status_code == 404

def test_get_digest_returns_data(client, db_session):
    from datetime import date
    from app.models import Digest
    d = Digest(date=date(2025, 3, 8), content="# Test", triggered_by="manual", topic_ids=[])
    db_session.add(d)
    db_session.commit()
    response = client.get("/api/digest?date=2025-03-08")
    assert response.status_code == 200
    assert response.json()["content"] == "# Test"
```

> 注意：需要在 `conftest.py` 补充 `client` fixture（见下方 Step 3）

- [ ] **Step 2: 编写 digest.py**

```python
# backend/app/api/digest.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date as date_type
from typing import Optional
from app.database import get_db
from app.models import Digest

router = APIRouter()

@router.get("/api/digest")
def get_digest(date: Optional[date_type] = None, db: Session = Depends(get_db)):
    query_date = date or date_type.today()
    digest = db.query(Digest).filter(Digest.date == query_date).first()
    if not digest:
        raise HTTPException(status_code=404, detail="该日期暂无简报")
    return {
        "id": digest.id,
        "date": str(digest.date),
        "content": digest.content,
        "triggered_by": digest.triggered_by,
        "created_at": str(digest.created_at),
    }
```

- [ ] **Step 3: 在 conftest.py 添加 client fixture**

```python
# 在 backend/tests/conftest.py 追加以下内容

from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

- [ ] **Step 4: 编写 topics.py**

```python
# backend/app/api/topics.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date as date_type
from typing import Optional
from app.database import get_db
from app.models import Topic

router = APIRouter()

@router.get("/api/topics")
def get_topics(date: Optional[date_type] = None, db: Session = Depends(get_db)):
    query_date = date or date_type.today()
    topics = db.query(Topic).filter(Topic.date == query_date).all()
    return [{"id": t.id, "title": t.title, "summary": t.summary,
             "perspectives": t.perspectives, "is_blind_spot": t.is_blind_spot,
             "date": str(t.date)} for t in topics]

@router.get("/api/topics/{topic_id}")
def get_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="主题不存在")
    return {"id": topic.id, "title": topic.title, "summary": topic.summary,
            "perspectives": topic.perspectives, "is_blind_spot": topic.is_blind_spot,
            "date": str(topic.date)}
```

- [ ] **Step 5: 编写 trigger.py**

```python
# backend/app/api/trigger.py
from fastapi import APIRouter, HTTPException
from datetime import date, datetime
from app.models import PipelineRun
from app.database import SessionLocal
from app.pipeline.graph import run_pipeline
import threading

router = APIRouter()

def _run_in_background(run_id: int, run_date: str):
    try:
        run_pipeline(run_date=run_date, triggered_by="manual")
        with SessionLocal() as db:
            run = db.get(PipelineRun, run_id)
            run.status = "done"
            run.current_step = "done"
            run.finished_at = datetime.now()
            db.commit()
    except Exception as e:
        with SessionLocal() as db:
            run = db.get(PipelineRun, run_id)
            run.status = "failed"
            run.error_msg = str(e)
            run.finished_at = datetime.now()
            db.commit()

@router.post("/api/trigger")
def trigger_pipeline():
    today = date.today()
    with SessionLocal() as db:
        existing = db.query(PipelineRun).filter(
            PipelineRun.date == today,
            PipelineRun.status.in_(["running", "done"])
        ).first()
        if existing:
            if existing.status == "running":
                raise HTTPException(status_code=409, detail="今日Pipeline正在运行中")
            raise HTTPException(status_code=409, detail="今日Pipeline已完成，如需重跑请直接重置")

        run = PipelineRun(date=today, status="running", current_step="collect")
        db.add(run)
        db.commit()
        run_id = run.id

    thread = threading.Thread(target=_run_in_background, args=(run_id, today.isoformat()))
    thread.daemon = True
    thread.start()

    return {"message": "Pipeline已启动", "run_id": run_id}

@router.get("/api/pipeline/status")
def get_pipeline_status():
    today = date.today()
    with SessionLocal() as db:
        run = db.query(PipelineRun).filter(PipelineRun.date == today).order_by(
            PipelineRun.started_at.desc()
        ).first()
        if not run:
            return {"status": "idle", "current_step": None}
        return {
            "status": run.status,
            "current_step": run.current_step,
            "started_at": str(run.started_at) if run.started_at else None,
            "finished_at": str(run.finished_at) if run.finished_at else None,
            "error_msg": run.error_msg,
        }
```

- [ ] **Step 6: 编写 sources.py**

```python
# backend/app/api/sources.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import Source

router = APIRouter()

class SourceUpdate(BaseModel):
    enabled: bool

@router.get("/api/sources")
def get_sources(db: Session = Depends(get_db)):
    sources = db.query(Source).all()
    return [{"id": s.id, "name": s.name, "type": s.type,
             "url": s.url, "language": s.language, "enabled": s.enabled} for s in sources]

@router.put("/api/sources/{source_id}")
def update_source(source_id: int, body: SourceUpdate, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="来源不存在")
    source.enabled = body.enabled
    db.commit()
    return {"id": source.id, "name": source.name, "enabled": source.enabled}
```

- [ ] **Step 7: 编写 topics API 测试**

```python
# backend/tests/test_api_topics.py
def test_get_topics_empty(client):
    response = client.get("/api/topics?date=2020-01-01")
    assert response.status_code == 200
    assert response.json() == []

def test_get_topic_not_found(client):
    response = client.get("/api/topics/99999")
    assert response.status_code == 404
```

- [ ] **Step 8: 编写 trigger API 测试**

```python
# backend/tests/test_api_trigger.py
from unittest.mock import patch

def test_get_pipeline_status_idle(client):
    response = client.get("/api/pipeline/status")
    assert response.status_code == 200
    assert response.json()["status"] == "idle"

def test_trigger_starts_pipeline(client):
    with patch("app.api.trigger.threading.Thread") as mock_thread:
        mock_thread.return_value.start = lambda: None
        response = client.post("/api/trigger")
        assert response.status_code == 200
        assert "run_id" in response.json()
```

- [ ] **Step 9: 运行所有API测试**

```bash
pytest tests/test_api_*.py -v
```

Expected: 全部 PASSED

- [ ] **Step 10: Commit**

```bash
git add backend/app/api/ backend/tests/test_api_*.py backend/tests/conftest.py
git commit -m "feat: 实现REST API端点（digest/topics/trigger/sources）"
```

---

## Task 14: FastAPI 主入口

**Files:**
- Create: `backend/app/main.py`

- [ ] **Step 1: 编写 main.py**

```python
# backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import digest, topics, trigger, sources
from app.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(title="打破信息茧房 - 新闻聚合API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(digest.router)
app.include_router(topics.router)
app.include_router(trigger.router)
app.include_router(sources.router)

@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 2: 启动后端验证**

```bash
cd backend
.venv/Scripts/activate
uvicorn app.main:app --reload
```

访问 http://localhost:8000/health，预期返回 `{"status": "ok"}`

访问 http://localhost:8000/docs，可看到 Swagger UI

- [ ] **Step 3: 运行全部测试**

```bash
pytest tests/ -v
```

Expected: 全部 PASSED

- [ ] **Step 4: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: 完成FastAPI主入口，后端服务可启动"
```

---

## 验收标准

后端部分完成后，应满足：

1. `pytest tests/ -v` 全部通过
2. `uvicorn app.main:app --reload` 无报错启动
3. `GET http://localhost:8000/health` 返回 `{"status": "ok"}`
4. `GET http://localhost:8000/docs` 可看到所有API接口
5. `python init_db.py` 成功建表并初始化来源数据
6. `POST http://localhost:8000/api/trigger` 返回 `{"run_id": N}`（Pipeline在后台异步运行）

---

**下一步：** Plan 2 - 前端 + 启动脚本（见 `docs/superpowers/plans/2026-03-25-frontend-startup.md`）
