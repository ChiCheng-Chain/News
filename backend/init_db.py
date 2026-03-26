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
        Source(name="微信公众号RSS代理", type="rss", url="", language="zh", enabled=False),
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
