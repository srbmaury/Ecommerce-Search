import requests
import random
import time
from collections import defaultdict
import os
import sys
import csv
from datetime import datetime
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

from backend.utils.database import get_db_session, init_db, create_tables
from backend.models import User, Product, SearchEvent, CartItem
from backend.services.db_user_manager import add_to_cart
from backend.services.security import hash_password


# Environment-aware API URL
API_URL = os.environ.get("API_URL", "http://localhost:5000")

# Configurable scale - adjust based on your needs
USER_COUNT = int(os.environ.get("USER_COUNT", 100))  # Default: 100 users
EVENTS_PER_USER = int(os.environ.get("EVENTS_PER_USER", 100))  # Default: 100 events/user
BATCH_SIZE = 500  # Commit database transactions in batches for better performance

# Total events estimate
TOTAL_EVENTS = USER_COUNT * EVENTS_PER_USER
print(f"📊 Configuration: {USER_COUNT} users × {EVENTS_PER_USER} events = {TOTAL_EVENTS:,} total events")

# Performance warning for large datasets
if TOTAL_EVENTS > 100000:
    print(f"⚠️  WARNING: {TOTAL_EVENTS:,} events is a large dataset.")
    print(f"   - SQLite write time: ~{TOTAL_EVENTS // 500:.0f}-{TOTAL_EVENTS // 250:.0f} minutes")
    print(f"   - Database size: ~{TOTAL_EVENTS * 0.5 // 1000:.0f}MB")
    print(f"   - Consider starting with fewer events for testing")

# Detect if running on PythonAnywhere (force database mode there)
def detect_pythonanywhere():
    """Detect if running on PythonAnywhere environment."""
    # Check for PythonAnywhere-specific environment variables
    if any(key in os.environ for key in ['PYTHONANYWHERE_SITE', 'PYTHONANYWHERE_DOMAIN']):
        return True
    # Check if path matches PythonAnywhere user directory pattern (/home/username/)
    cwd = os.getcwd()
    if cwd.startswith('/home/') and '/.local/' not in cwd:
        # Check if it's a typical PythonAnywhere setup (not just any /home/ directory)
        parts = cwd.split('/')
        if len(parts) >= 3 and parts[2]:  # /home/username/something
            return True
    return False

IS_PYTHONANYWHERE = detect_pythonanywhere()

# Check if API is available
def is_api_available():
    """Check if the backend API is running."""
    if IS_PYTHONANYWHERE:
        # On PythonAnywhere, always use direct database to avoid API issues
        return False
    try:
        response = requests.get(f"{API_URL}/search?q=test&user_id=test", timeout=2)
        return response.ok
    except requests.exceptions.RequestException:
        return False

USE_API = is_api_available()
print(f"🌐 Environment: {'PythonAnywhere (forced DB mode)' if IS_PYTHONANYWHERE else 'Local'}")
print(f"🌐 API Mode: {'Enabled' if USE_API else 'Disabled (using direct database)'}")
if USE_API:
    print(f"🌐 API URL: {API_URL}")

# ----------------------------
# Initialize database
# ----------------------------
print("🔧 Initializing database...")
init_db()
create_tables()

# ----------------------------
# Clear existing test data from database
# ----------------------------
print("🧹 Clearing existing test data from database...")
session = get_db_session()
try:
    # Delete test users and their events (cascade will handle events)
    test_users = session.query(User).filter(User.username.like('testuser%')).all()
    if test_users:
        for user in test_users:
            session.delete(user)
        session.commit()
        print(f"✓ Cleared {len(test_users)} test users")
except Exception as e:
    print(f"⚠️  Error clearing data: {e}")
    session.rollback()
finally:
    session.close()

# ----------------------------
# Load products from database
# ----------------------------
print("📦 Loading products from database...")
products = []
category_keywords = defaultdict(list)

session = get_db_session()
try:
    db_products = session.query(Product).all()
    
    if not db_products:
        print("⚠️  No products found in database!")
        print("🔄 Attempting to load products from CSV backup...")
        
        # Try to load from CSV backup
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "products_backup.csv")
        
        if os.path.exists(csv_path):
            print(f"📂 Found CSV backup at {csv_path}")
            print("💾 Importing products into database...")
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                imported = 0
                
                for row in reader:
                    product = Product(
                        id=int(row['product_id']),
                        title=row['title'],
                        description=row['description'],
                        category=row['category'],
                        price=float(row['price']),
                        rating=float(row['rating']),
                        review_count=int(row['review_count']),
                        popularity=int(row['popularity']),
                        created_at=datetime.fromisoformat(row['created_at']) if row.get('created_at') else datetime.utcnow()
                    )
                    session.add(product)
                    imported += 1
                
                session.commit()
                print(f"✅ Imported {imported} products from CSV")
                
                # Reload products
                db_products = session.query(Product).all()
        else:
            print(f"❌ No CSV backup found at {csv_path}")
            print("📝 To create a backup, run:")
            print(f"   python -m ml.export_products_to_csv")
            sys.exit(1)
    
    if not db_products:
        print("❌ Still no products found!")
        sys.exit(1)
    
    for product in db_products:
        products.append({
            "product_id": product.id,
            "title": product.title,
            "category": product.category
        })
        # Build search keywords - extract only brand names (first word of title)
        brand = product.title.split()[0] if product.title else ""
        if brand and len(brand) > 2:
            category_keywords[product.category].append(brand.lower())

finally:
    session.close()

PRODUCT_IDS = [p["product_id"] for p in products]

# Add category names as search terms too
categories = list(set(p["category"] for p in products))

# Unique searchable terms (brands)
brand_terms = list(set(
    word.lower()
    for words in category_keywords.values()
    for word in words
))

# Combine brands and categories for search terms
SEARCH_TERMS = brand_terms + [cat.lower() for cat in categories]

# Filter out any terms that look like product IDs (contain hyphens and numbers)
SEARCH_TERMS = [term for term in SEARCH_TERMS if not any(char.isdigit() for char in term)]

print(f"📦 Loaded {len(products)} products from database")
print(f"🔍 Using {len(SEARCH_TERMS)} unique search terms")

# ----------------------------
# Auth helpers
# ----------------------------
def signup_and_login(username, password):
    """Sign up or login a user. Works with both API and direct database."""
    if USE_API:
        # Try API signup
        r = requests.post(f"{API_URL}/signup", json={
            "username": username,
            "password": password
        })

        if r.status_code == 200 and "user_id" in r.json():
            return r.json()["user_id"]

        # Try API login
        r = requests.post(f"{API_URL}/login", json={
            "username": username,
            "password": password
        })

        if r.status_code == 200 and "user_id" in r.json():
            return r.json()["user_id"]

        return None
    else:
        # Direct database access
        session = get_db_session()
        try:
            # Check if user exists
            existing_user = session.query(User).filter_by(username=username).first()
            if existing_user:
                return existing_user.user_id
            
            # Create new user with UUID-based ID
            user_id = f"u{uuid.uuid4().hex[:12]}"
            group = random.choice(["A", "B"])
            
            new_user = User(
                user_id=user_id,
                username=username,
                password_hash=hash_password(password),
                group=group
            )
            session.add(new_user)
            session.commit()
            return user_id
        except Exception as e:
            print(f"Error creating user {username}: {e}")
            session.rollback()
            return None
        finally:
            session.close()

# ----------------------------
# Optimized batch operations for large-scale data
# ----------------------------
def log_events_batch(events_list):
    """Log multiple events in a single transaction for better performance."""
    if not events_list:
        return
    
    session = get_db_session()
    try:
        for event_data in events_list:
            event = SearchEvent(**event_data)
            session.add(event)
        session.commit()
    except Exception as e:
        print(f"Error logging batch of {len(events_list)} events: {e}")
        session.rollback()
    finally:
        session.close()

def log_event_to_db(user_id, query, product_id, event_type):
    """Log an event directly to the database."""
    session = get_db_session()
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        group = user.group if user else "A"
        
        event = SearchEvent(
            user_id=user_id,
            query=query,
            product_id=int(product_id) if product_id else None,
            event_type=event_type,
            group=group
        )
        session.add(event)
        session.commit()
    except Exception as e:
        print(f"Error logging event for user {user_id}, query '{query}', product_id '{product_id}', event_type '{event_type}': {e}")
        session.rollback()
    finally:
        session.close()

def add_to_cart_db(user_id, product_id, quantity=1):
    """Add product to cart using CartItem model."""
    session = get_db_session()
    try:
        item = session.query(CartItem).filter_by(user_id=user_id, product_id=product_id).first()
        if item:
            item.quantity += quantity
        else:
            item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
            session.add(item)
        session.commit()
    except Exception as e:
        print(f"Error adding product {product_id} to cart for user {user_id}: {e}")
        session.rollback()
    finally:
        session.close()

# ----------------------------
# User behavior simulation
# ----------------------------
def simulate_user(user_id):
    """Simulate user behavior with batch operations for better performance."""
    
    # Get user's group for event logging
    session = get_db_session()
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        group = user.group if user else "A"
    finally:
        session.close()
    
    events_batch = []
    cart_updates = []
    
    for _ in range(EVENTS_PER_USER):
        product = random.choice(products)
        product_id = product["product_id"]

        # 70% keyword search, 30% category search
        if random.random() < 0.7:
            query = random.choice(SEARCH_TERMS)
        else:
            query = product["category"].lower()

        if USE_API:
            # Search
            requests.get(
                f"{API_URL}/search",
                params={"q": query, "user_id": user_id}
            )

            # Click
            requests.post(
                f"{API_URL}/event",
                json={
                    "user_id": user_id,
                    "query": query,
                    "product_id": product_id,
                    "event": "click"
                }
            )

            # Add to cart (30%)
            if not USE_API and random.random() < 0.3:
                quantity = 1
                if random.random() < 0.2:
                    quantity = random.randint(2, 3)
                for _ in range(quantity):
                    events_batch.append({
                        "user_id": user_id,
                        "query": query,
                        "product_id": int(product_id),
                        "event_type": "add_to_cart",
                        "group": group
                    })
                    cart_updates.append((user_id, product_id, 1))
        else:
            # Direct database access with batching
            # Add click event to batch
            events_batch.append({
                "user_id": user_id,
                "query": query,
                "product_id": int(product_id),
                "event_type": "click",
                "group": group
            })
            
            # Add to cart (30%)
            if not USE_API and random.random() < 0.3:
                quantity = 1
                if random.random() < 0.2:
                    quantity = random.randint(2, 3)
                for _ in range(quantity):
                    events_batch.append({
                        "user_id": user_id,
                        "query": query,
                        "product_id": int(product_id),
                        "event_type": "add_to_cart",
                        "group": group
                    })
                    cart_updates.append((user_id, product_id, 1))
            
            # Batch commit every BATCH_SIZE events for performance
            if len(events_batch) >= BATCH_SIZE:
                log_events_batch(events_batch)
                events_batch = []
    
    # Commit remaining events
    if not USE_API and events_batch:
        log_events_batch(events_batch)
    
    # Update cart
    if not USE_API and cart_updates:
        for user_id, product_id, quantity in cart_updates:
            add_to_cart_db(user_id, product_id, quantity)

            

# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":
    print("\n🚀 Starting fake data generation...")
    print(f"   Creating {USER_COUNT} users with {EVENTS_PER_USER} events each")
    
    for i in range(USER_COUNT):
        username = f"testuser{i+1}"
        password = "TestPass123!"
        user_id = signup_and_login(username, password)

        if user_id:
            print(f"   User {i+1}/{USER_COUNT}: {username} (ID: {user_id})")
            simulate_user(user_id)
        else:
            print(f"   ⚠️  Failed to create user: {username}")

    print("\n✅ Fake data generation complete!")
    print("   Data is now stored in the database.")
