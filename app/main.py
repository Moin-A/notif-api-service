from datetime import datetime
from typing import Optional

import jwt
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import text
from app.auth import JWTService
from app.db import engine
from app.queue import QUEUE_KEY, get_redis

app = FastAPI(title="notif-api-service")
redis_client = get_redis()


class NotificationIn(BaseModel):
    endpoint: str
    expirationTime: Optional[datetime] = None
    keys: dict


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok", "db": "reachable"}


@app.post("/notifications", status_code=202)
def enqueue_notification(
    n: NotificationIn,
    request: Request,
    authorization: Optional[str] = Header(default=None),
):
    try:
        JWTService().decode(authorization.removeprefix("Bearer "))
    except AttributeError:
        raise HTTPException(status_code=401, detail="missing token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="invalid token")
    redis_client.rpush(QUEUE_KEY, n.model_dump_json())
    return {"status": "queued"}
