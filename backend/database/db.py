"""
ConfigSentinel - Database Engine & Session
---------------------------------------------
Creates the SQLAlchemy engine and session factory. Works with SQLite
(default, for development / demo) or PostgreSQL (production, via
DATABASE_URL environment variable) without any code changes.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    # required for SQLite when accessed from multiple threads (FastAPI)
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called once on application startup."""
    from database import models  # noqa: F401  (ensures models are registered)
    Base.metadata.create_all(bind=engine)
