"""
Database initialization and session utilities.

Responsibilities:
- Initialize SQLAlchemy engine
- Configure connection pooling safely
- Provide session factory for request-scoped DB access
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

from backend.models import Base
from backend.utils.config import get_database_url


logger = logging.getLogger("database")


# ---------- GLOBAL STATE ----------

_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


# ---------- INITIALIZATION ----------

def init_db():
    """
    Initialize SQLAlchemy engine and session factory.

    Safe to call multiple times (idempotent).
    """
    global _engine, _SessionLocal

    if _engine is not None and _SessionLocal is not None:
        return _engine, _SessionLocal

    database_url = get_database_url()
    logger.info("Initializing database engine")

    connect_args = {}
    pool_size = 5
    max_overflow = 10

    # SQLite-specific configuration
    if database_url.startswith("sqlite"):
        connect_args = {
            "check_same_thread": False,
            "timeout": 30,
        }
        pool_size = 1
        max_overflow = 0
        logger.info("Using SQLite configuration")

    _engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_recycle=3600,
        echo=False,
        connect_args=connect_args,
    )

    _SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_engine,
    )

    logger.info("Database engine initialized")
    return _engine, _SessionLocal


# ---------- SCHEMA MANAGEMENT ----------

def create_tables():
    """
    Create all database tables.

    Should be called once at startup or via migration scripts.
    """
    if _engine is None:
        init_db()

    logger.info("Creating database tables")
    Base.metadata.create_all(bind=_engine)
    logger.info("Database tables created")


# ---------- SESSION ACCESS ----------

def get_db_session():
    """
    Get a new database session.

    Caller is responsible for:
    - committing or rolling back
    - closing the session
    """
    if _SessionLocal is None:
        init_db()

    return _SessionLocal()
