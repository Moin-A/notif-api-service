"""Shared pytest fixtures.

Lives at the repo root so pytest puts the project root on sys.path, making
`import app.main` resolve. Fixtures defined here are auto-injected into any test
by name — no import needed in the test files.
"""
import pytest
from fastapi.testclient import TestClient

import app.main


class FakeRedis:
    """Minimal in-memory stand-in for redis.Redis.

    Implements only the list commands this service uses, so tests need no real
    Redis running. Backed by a plain dict of lists.
    """

    def __init__(self):
        self.store: dict[str, list[str]] = {}

    def rpush(self, key: str, value: str) -> int:
        self.store.setdefault(key, []).append(value)
        return len(self.store[key])

    def lrange(self, key: str, start: int, end: int) -> list[str]:
        items = self.store.get(key, [])
        # Redis lrange end is inclusive; -1 means "to the end".
        stop = len(items) if end == -1 else end + 1
        return items[start:stop]

    def llen(self, key: str) -> int:
        return len(self.store.get(key, []))


@pytest.fixture
def fake_redis():
    """A fresh, empty in-memory Redis for one test."""
    return FakeRedis()


@pytest.fixture
def client(fake_redis, monkeypatch):
    """TestClient with the app's Redis swapped for the in-memory fake."""
    monkeypatch.setattr(app.main, "redis_client", fake_redis)
    return TestClient(app.main.app)
