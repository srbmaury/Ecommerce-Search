"""
Database initialization and session utilities.

Responsibilities:
- Initialize SQLAlchemy engine
- Configure connection pooling safely
- Provide session factory for request-scoped DB access
"""

import logging
from sqlalchemy import create_engine, text
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
    _refresh_product_search_vectors()
    _ensure_password_changed_at_column()
    logger.info("Database tables created")


def _refresh_product_search_vectors():
    """
    Backfill product full-text vectors for PostgreSQL deployments.

    SQLite local development ignores the tsvector column, so this is skipped
    outside Postgres.
    """
    if _engine is None or _engine.dialect.name != "postgresql":
        return

    statement = text("""
        UPDATE products
        SET search_vector =
            setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(category, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(description, '')), 'C')
        WHERE search_vector IS NULL
    """)

    with _engine.begin() as conn:
        conn.execute(statement)


def _ensure_password_changed_at_column():
    """
    Add users.password_changed_at if it's missing.

    Base.metadata.create_all() only creates tables that don't exist yet — it
    never alters an existing table, so a column added to the model after the
    "users" table was already created (e.g. on the live Neon DB) needs this
    one-off, idempotent ALTER TABLE to actually show up.
    """
    if _engine is None:
        return

    with _engine.begin() as conn:
        if _engine.dialect.name == "postgresql":
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP"
            ))
        else:
            # SQLite has no "ADD COLUMN IF NOT EXISTS" — check first.
            existing = {row[1] for row in conn.execute(text("PRAGMA table_info(users)"))}
            if "password_changed_at" not in existing:
                conn.execute(text("ALTER TABLE users ADD COLUMN password_changed_at TIMESTAMP"))


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
