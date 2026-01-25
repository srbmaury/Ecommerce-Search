import csv

import requests
import random
import time
import sys
from collections import defaultdict
import os


API = "http://localhost:5000"
CSV_FILE = sys.argv[1] if len(sys.argv) > 1 else "data/products.csv"
EVENTS_FILE = "data/search_events.csv"
USERS_FILE = "backend/users.json"
USER_COUNT = 30
EVENTS_PER_USER = 40

# Clear users.json and search_events.csv before starting
print("🧹 Clearing existing data...")
os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
with open(USERS_FILE, "w", encoding="utf-8") as f:
    f.write("[]")

os.makedirs(os.path.dirname(EVENTS_FILE), exist_ok=True)
with open(EVENTS_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["user_id", "query", "product_id", "event", "timestamp", "group"])

# ----------------------------
# Load products from CSV (create if missing)
# ----------------------------
products = []
category_keywords = defaultdict(list)

if not os.path.exists(CSV_FILE):
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["product_id", "title", "description", "category", "price", "rating", "review_count", "popularity", "created_at"])

with open(CSV_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        products.append({
            "product_id": row["product_id"],
            "title": row["title"],
            "category": row["category"]
        })
        # Build search keywords - extract only brand names (first word of title)
        brand = row["title"].split()[0] if row["title"] else ""
        if brand and len(brand) > 2:
            category_keywords[row["category"]].append(brand.lower())

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
    print(f"📦 Loaded {len(products)} products from {CSV_FILE}")
    print(f"🔍 Using {len(SEARCH_TERMS)} unique search terms")

    for i in range(USER_COUNT):
        username = f"testuser{i+1}"
        password = "TestPass123!"
        user_id = signup_and_login(username, password)

        if user_id:
            simulate_user(user_id)

    print("✅ Fake data generation complete.")
