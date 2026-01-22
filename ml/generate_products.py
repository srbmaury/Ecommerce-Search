import csv
import random
import sys
from datetime import datetime, timedelta

ROWS = int(sys.argv[1]) if len(sys.argv) > 1 else 1000

categories = {
    "Mobiles": (8000, 150000),
    "Laptops": (25000, 250000),
    "Tablets": (10000, 120000),
    "Wearables": (1500, 60000),
    "Audio": (1000, 80000),
    "TVs": (20000, 300000),
    "Cameras": (25000, 300000),
    "Gaming": (2000, 120000),
    "Accessories": (500, 30000),
    "Storage": (800, 40000),
    "Smart Home": (1000, 50000),
    "Networking": (1500, 40000),
    "Office": (3000, 80000),
    "Home Appliances": (5000, 150000),
    "Fitness": (2000, 70000)
}

adjectives = ["Pro", "Max", "Ultra", "Plus", "Neo", "Prime", "Elite", "Smart"]
base_names = [
    "Phone", "Laptop", "Tablet", "Watch", "Headphones",
    "Speaker", "Camera", "Console", "Router", "SSD",
    "Keyboard", "Mouse", "Monitor", "Purifier", "Treadmill"
]

start_date = datetime(2024, 1, 1)

with open(f"data/products.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "product_id", "title", "description", "category",
        "price", "rating", "review_count", "popularity", "created_at"
    ])

    for i in range(1, ROWS + 1):
        category = random.choice(list(categories.keys()))
        min_p, max_p = categories[category]

        price = random.randint(min_p, max_p)
        rating = round(random.uniform(3.8, 4.9), 1)
        reviews = random.randint(50, 12000)
        popularity = random.randint(500, 50000)

        title = f"{random.choice(base_names)} {random.choice(adjectives)} {random.randint(100,999)}"
        desc = f"{title} with advanced features and high performance"

        created_at = start_date + timedelta(days=random.randint(0, 365))

        writer.writerow([
            100000 + i,
            title,
            desc,
            category,
            price,
            rating,
            reviews,
            popularity,
            created_at.strftime("%Y-%m-%d")
        ])

print(f"✅ Generated data/products.csv")
