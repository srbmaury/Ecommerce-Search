"""
Database initialization and migration utilities.
"""
import os
import csv
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base, Product, User, SearchEvent
from backend.config import get_database_url
from utils.data_paths import get_data_path
import json

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
    if database_url.startswith('sqlite'):
        connect_args = {
            'check_same_thread': False,  # Allow multiple threads
            'timeout': 30  # Increase timeout for locked database
        }
    
    engine = create_engine(
        database_url,
        pool_pre_ping=True,  # Verify connections before using
        echo=False,  # Set to True for SQL debugging
        connect_args=connect_args
    )
    
    # Create session factory - NOT scoped_session to avoid thread-local caching issues
    SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)
    
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


def migrate_csv_to_db(force=False):
    """
    Migrate data from CSV files to PostgreSQL database.
    Always clears existing data before migration.
    
    Args:
        force: Deprecated, migration always clears data first
    """
    session = get_db_session()
    
    try:
        # Always clear existing data before migration
        logger.info("Clearing existing data...")
        session.query(SearchEvent).delete()
        session.query(User).delete()
        session.query(Product).delete()
        session.commit()
        logger.info("Existing data cleared")
        
        # Migrate products
        products_file = get_data_path("products.csv")
        if os.path.exists(products_file):
            logger.info(f"Migrating products from {products_file}...")
            with open(products_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                products = []
                for row in reader:
                    product = Product(
                        product_id=row['product_id'],
                        title=row['title'],
                        description=row.get('description', ''),
                        category=row.get('category', ''),
                        price=float(row['price']),
                        rating=float(row.get('rating', 0)),
                        review_count=int(row.get('review_count', 0)),
                        popularity=int(row.get('popularity', 0)),
                        created_at=datetime.strptime(row['created_at'], '%Y-%m-%d') if row.get('created_at') else datetime.utcnow()
                    )
                    products.append(product)
                    
                    # Batch insert for performance
                    if len(products) >= 1000:
                        session.bulk_save_objects(products)
                        session.commit()
                        logger.info(f"Migrated {len(products)} products...")
                        products = []
                
                if products:
                    session.bulk_save_objects(products)
                    session.commit()
                    logger.info(f"Migrated {len(products)} products")
        
        # Migrate users
        users_file = os.path.join(os.path.dirname(__file__), "users.json")
        if os.path.exists(users_file):
            logger.info(f"Migrating users from {users_file}...")
            with open(users_file, 'r') as f:
                users_data = json.load(f)
                migrated_count = 0
                # Handle list format: [{"user_id": "u1", "username": "user1", "password": "hash", ...}, ...]
                if isinstance(users_data, list):
                    for user_obj in users_data:
                        user_id = user_obj.get('user_id')
                        username = user_obj.get('username')
                        password_hash = user_obj.get('password')
                        if username and password_hash:
                            cart = user_obj.get('cart', {})
                            # Convert old list format to dict format if needed
                            if isinstance(cart, list):
                                cart = {str(pid): 1 for pid in cart}
                            
                            user = User(
                                user_id=user_id or f"u{migrated_count + 1}",
                                username=username,
                                password_hash=password_hash,
                                group=user_obj.get('group', 'A'),
                                cluster=user_obj.get('cluster'),
                                cart=cart,
                                created_at=datetime.utcnow()
                            )
                            session.add(user)
                            migrated_count += 1
                    session.commit()
                    logger.info(f"Migrated {migrated_count} users")
        
        # Migrate search events
        events_file = get_data_path("search_events.csv")
        if os.path.exists(events_file):
            logger.info(f"Migrating search events from {events_file}...")
            with open(events_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                events = []
                for row in reader:
                    # Parse timestamp safely
                    timestamp = datetime.utcnow()
                    if row.get('timestamp'):
                        try:
                            timestamp_str = row['timestamp'].replace('Z', '+00:00')
                            timestamp = datetime.fromisoformat(timestamp_str)
                        except (ValueError, AttributeError):
                            pass
                    
                    event = SearchEvent(
                        user_id=row.get('user_id', ''),
                        query=row.get('query', ''),
                        product_id=row.get('product_id', ''),
                        event_type=row.get('event', 'search'),  # Note: CSV has 'event' column
                        group=row.get('group', ''),
                        timestamp=timestamp,
                        position=int(row['position']) if row.get('position') and row['position'] != '' else None
                    )
                    events.append(event)
                    
                    # Batch insert for performance
                    if len(events) >= 1000:
                        session.bulk_save_objects(events)
                        session.commit()
                        logger.info(f"Migrated {len(events)} events...")
                        events = []
                
                if events:
                    session.bulk_save_objects(events)
                    session.commit()
                    logger.info(f"Migrated {len(events)} events")
        
        logger.info("✅ Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    # Run migration when called directly
    logging.basicConfig(level=logging.INFO)
    
    init_db()
    create_tables()
    migrate_csv_to_db()
