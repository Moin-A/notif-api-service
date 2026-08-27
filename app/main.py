from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import text

from app.db import engine
from app.queue import QUEUE_KEY, get_redis

app = FastAPI(title="notif-api-service")
redis_client = get_redis()


class NotificationIn(BaseModel):
    to: str
    channel: str = "email"
    message: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok", "db": "reachable"}


@app.post("/notifications", status_code=202)
def enqueue_notification(n: NotificationIn):
    """Queue a notification for the background worker to deliver."""
    redis_client.rpush(QUEUE_KEY, n.model_dump_json())
    return {"status": "queued"}
