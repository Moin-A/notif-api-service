"""Redis-backed job queue shared by the API (producer) and worker (consumer).

Uses the same Redis instance as reptrack. In-cluster it is reached cross-namespace
at redis.reptrack.svc.cluster.local:6379. reptrack uses db 0 (sidekiq) and db 1
(cable), so notif uses db 2 to stay isolated.
"""
import os

import redis

QUEUE_KEY = "notif:queue"

_DEFAULT_URL = "redis://localhost:6379/2"


def get_redis() -> redis.Redis:
    url = os.getenv("REDIS_URL", _DEFAULT_URL)
    return redis.Redis.from_url(url, decode_responses=True)
