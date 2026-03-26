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
