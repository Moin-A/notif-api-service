"""Postgres connection.

Uses the same Postgres instance as reptrack (postgres.practify.svc.cluster.local)
but a separate `notif_staging` database. The real DATABASE_URL is injected from
the `notif-secrets` Kubernetes secret; the default below is for local dev only.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

_DEFAULT_URL = "postgresql://postgres:postgres@localhost:5432/notif"

DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_URL)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Shared declarative base. Every model inherits from this, and its .metadata
# collects all tables so Base.metadata.create_all(engine) can build them.
Base = declarative_base()
