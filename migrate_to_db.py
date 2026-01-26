#!/usr/bin/env python3
"""
Migration script to transfer data from CSV/JSON files to PostgreSQL database.
Always clears existing data and re-migrates from source files.

Usage:
    python migrate_to_db.py
"""
import sys
import logging
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from backend.database import init_db, create_tables, migrate_csv_to_db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run the migration."""
    try:
        logger.info("=" * 60)
        logger.info("Starting database migration")
        logger.info("=" * 60)
        
        # Initialize database connection
        logger.info("Step 1: Initializing database connection...")
        engine, session_factory = init_db()
        logger.info(f"✓ Connected to: {engine.url}")
        
        # Create tables
        logger.info("\nStep 2: Creating database tables...")
        create_tables()
        logger.info("✓ Tables created successfully")
        
        # Migrate data (always clears existing data first)
        logger.info("\nStep 3: Migrating data from CSV/JSON files...")
        migrate_csv_to_db()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Migration completed successfully!")
        logger.info("=" * 60)
        logger.info("\nYour application is now using the PostgreSQL database.")
        logger.info("You can safely keep the CSV/JSON files as backups.")
        
    except Exception as e:
        logger.error(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
