"""
Database initialization utilities.
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base
from backend.utils.config import get_database_url

logger = logging.getLogger(__name__)

# Global session factory
engine = None
SessionLocal = None


def init_db():
    """Initialize the database connection."""
    global engine, SessionLocal
    
    database_url = get_database_url()
    logger.info(f"Connecting to database: {database_url}")
    
    # Add SQLite-specific configuration for better transaction handling
    connect_args = {}
    pool_size = 5
    max_overflow = 10
    
    if database_url.startswith('sqlite'):
        connect_args = {
            'check_same_thread': False,  # Allow multiple threads
            'timeout': 30  # Increase timeout for locked database
        }
        # SQLite doesn't benefit from connection pooling
        pool_size = 1
        max_overflow = 0
    
    engine = create_engine(
        database_url,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=pool_size,  # Connection pool size
        max_overflow=max_overflow,  # Max connections beyond pool_size
        pool_recycle=3600,  # Recycle connections after 1 hour
        echo=False,  # Set to True for SQL debugging
        connect_args=connect_args
    )
    
    # Create session factory - NOT scoped_session because it creates thread-local sessions
    # that persist across requests, leading to stale data and transaction issues in web apps
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return engine, SessionLocal


def create_tables():
    """Create all database tables."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def get_db_session():
    """Get a database session. Remember to close it after use."""
    if SessionLocal is None:
        init_db()
    # Don't use scoped_session() directly, create a new session each time
    # This ensures commits actually persist
    session = SessionLocal()
    return session
