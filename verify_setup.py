#!/usr/bin/env python3
"""
Quick verification script to test database setup.
Run this after migration to ensure everything works.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all new modules can be imported."""
    print("Testing imports...")
    try:
        from backend import models
        from backend import database
        from backend import db_user_manager
        from backend import db_product_service
        from backend import db_event_service
        print("✅ All modules import successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_database_connection():
    """Test database connection."""
    print("\nTesting database connection...")
    try:
        from backend.database import init_db, get_db_session
        from backend.models import User, Product, SearchEvent
        
        # Initialize database
        init_db()
        print("✅ Database initialized")
        
        # Test session
        session = get_db_session()
        
        # Check if tables exist by counting
        user_count = session.query(User).count()
        product_count = session.query(Product).count()
        event_count = session.query(SearchEvent).count()
        
        session.close()
        
        print(f"✅ Database connected successfully")
        print(f"   - Users: {user_count}")
        print(f"   - Products: {product_count}")
        print(f"   - Events: {event_count}")
        
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_user_operations():
    """Test basic user operations."""
    print("\nTesting user operations...")
    try:
        from backend.db_user_manager import get_user_by_username, load_users
        
        # Test load_users (backward compatibility)
        users = load_users()
        print(f"✅ load_users() works - found {len(users)} users")
        
        if users:
            # Test get_user_by_username
            first_user = users[0]
            user = get_user_by_username(first_user['username'])
            if user:
                print(f"✅ get_user_by_username() works - found '{user.username}'")
            else:
                print(f"⚠️  Could not find user '{first_user['username']}'")
        
        return True
    except Exception as e:
        print(f"❌ User operations failed: {e}")
        return False


def test_product_operations():
    """Test basic product operations."""
    print("\nTesting product operations...")
    try:
        from backend.db_product_service import get_products_df
        
        products_df = get_products_df()
        print(f"✅ get_products_df() works - found {len(products_df)} products")
        
        if not products_df.empty:
            print(f"   - Categories: {products_df['category'].nunique()}")
            print(f"   - Price range: ${products_df['price'].min():.2f} - ${products_df['price'].max():.2f}")
        
        return True
    except Exception as e:
        print(f"❌ Product operations failed: {e}")
        return False


def test_event_operations():
    """Test basic event operations."""
    print("\nTesting event operations...")
    try:
        from backend.db_event_service import get_events_df
        
        events_df = get_events_df()
        print(f"✅ get_events_df() works - found {len(events_df)} events")
        
        if not events_df.empty:
            print(f"   - Event types: {events_df['event'].unique().tolist()}")
            print(f"   - Unique users: {events_df['user_id'].nunique()}")
        
        return True
    except Exception as e:
        print(f"❌ Event operations failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Database Setup Verification")
    print("=" * 60)
    
    results = {
        "Imports": test_imports(),
        "Database Connection": test_database_connection(),
        "User Operations": test_user_operations(),
        "Product Operations": test_product_operations(),
        "Event Operations": test_event_operations()
    }
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! Your database is ready to use.")
        print("\nNext steps:")
        print("1. Start the application: python -m backend.app")
        print("2. Visit http://localhost:5000")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Ensure DATABASE_URL is set in .env")
        print("2. Run migration: python migrate_to_db.py")
        print("3. Check that all dependencies are installed")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
