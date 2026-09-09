"""Create all tables defined on Base. Run once: python -m app.init_db

Re-run whenever a new model is added — create_all only creates tables that
don't already exist (it will NOT alter existing ones; that's Alembic's job).
"""
from app.db import Base, engine
import app.models  # noqa: F401  — imported for its side effect: registers models on Base

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("tables created:", list(Base.metadata.tables.keys()))
