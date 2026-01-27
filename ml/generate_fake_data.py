import requests
import random
import time
from collections import defaultdict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from backend.database import get_db_session, init_db, create_tables
from backend.models import User, Product


API = "http://localhost:5000"
USER_COUNT = 30
EVENTS_PER_USER = 40

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
        print("❌ No products found in database!")
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
    r = requests.post(f"{API}/signup", json={
        "username": username,
        "password": password
    })

    if r.status_code == 200 and "user_id" in r.json():
        return r.json()["user_id"]

    r = requests.post(f"{API}/login", json={
        "username": username,
        "password": password
    })

    if r.status_code == 200 and "user_id" in r.json():
        return r.json()["user_id"]

    return None

# ----------------------------
# User behavior simulation
# ----------------------------
def simulate_user(user_id):
    for _ in range(EVENTS_PER_USER):
        product = random.choice(products)
        product_id = product["product_id"]

        # 70% keyword search, 30% category search
        if random.random() < 0.7:
            query = random.choice(SEARCH_TERMS)
        else:
            query = product["category"].lower()

        # Search
        requests.get(
            f"{API}/search",
            params={"q": query, "user_id": user_id}
        )

        # Click
        requests.post(
            f"{API}/event",
            json={
                "user_id": user_id,
                "query": query,
                "product_id": product_id,
                "event": "click"
            }
        )

        # Add to cart (30%)
        if random.random() < 0.3:
            # Sometimes add multiple quantities (20% chance of 2-3 items)
            quantity = 1
            if random.random() < 0.2:
                quantity = random.randint(2, 3)
            
            for _ in range(quantity):
                requests.post(
                    f"{API}/cart",
                    json={
                        "user_id": user_id,
                        "product_id": product_id,
                        "query": query
                    }
                )

        time.sleep(random.uniform(0.03, 0.08))

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
