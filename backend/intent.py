"""
Intent-Aware Search Module
Detects user intent from search queries and suggests filters/sorting.
"""

import re

# Real categories from data
CATEGORIES = [
    "Audio", "Electronics", "Computers", "Photography", "Accessories",
    "Gaming", "Networking", "Smart Home", "Storage"
]

# Category keywords mapping (keyword -> category)
CATEGORY_KEYWORDS = {
    # Audio
    "headphone": "Audio",
    "headphones": "Audio",
    "earphone": "Audio",
    "earphones": "Audio",
    "earbuds": "Audio",
    "speaker": "Audio",
    "speakers": "Audio",
    "airpods": "Audio",
    "soundbar": "Audio",
    # Electronics
    "phone": "Electronics",
    "phones": "Electronics",
    "mobile": "Electronics",
    "mobiles": "Electronics",
    "smartphone": "Electronics",
    "tablet": "Electronics",
    "tablets": "Electronics",
    "tv": "Electronics",
    "television": "Electronics",
    # Computers
    "laptop": "Computers",
    "laptops": "Computers",
    "notebook": "Computers",
    "computer": "Computers",
    "pc": "Computers",
    "desktop": "Computers",
    # Photography
    "camera": "Photography",
    "cameras": "Photography",
    "dslr": "Photography",
    "lens": "Photography",
    "tripod": "Photography",
    "drone": "Photography",
    # Accessories
    "accessory": "Accessories",
    "accessories": "Accessories",
    "case": "Accessories",
    "charger": "Accessories",
    "cable": "Accessories",
    "mouse": "Accessories",
    "keyboard": "Accessories",
    # Gaming
    "gaming": "Gaming",
    "game": "Gaming",
    "playstation": "Gaming",
    "console": "Gaming",
    "controller": "Gaming",
    # Networking
    "router": "Networking",
    "wifi": "Networking",
    "modem": "Networking",
    "network": "Networking",
    "mesh": "Networking",
    # Smart Home
    "smart home": "Smart Home",
    "alexa": "Smart Home",
    "echo": "Smart Home",
    "nest": "Smart Home",
    "bulb": "Smart Home",
    "smart light": "Smart Home",
    # Storage
    "storage": "Storage",
    "ssd": "Storage",
    "hdd": "Storage",
    "drive": "Storage",
    "pendrive": "Storage",
    "memory card": "Storage",
}

# Brand keywords mapping (brand -> category it's known for)
BRAND_KEYWORDS = {
    # Audio brands
    "boat": "Audio",
    "jbl": "Audio",
    "sony": "Audio",
    # Electronics brands
    "samsung": "Electronics",
    "apple": "Electronics",
    "xiaomi": "Electronics",
    "oneplus": "Electronics",
    # Computer brands
    "hp": "Computers",
    "dell": "Computers",
    "lenovo": "Computers",
    "asus": "Computers",
    # Photography brands
    "canon": "Photography",
    "nikon": "Photography",
    "dji": "Photography",
    # Accessories brands
    "logitech": "Accessories",
    # Gaming brands
    "razer": "Gaming",
    "xbox": "Gaming",
    # Networking brands
    "tp-link": "Networking",
    "tplink": "Networking",
    "netgear": "Networking",
    # Smart Home brands
    "philips": "Smart Home",
    "amazon": "Smart Home",
    # Storage brands
    "wd": "Storage",
}

# Price-sensitive keywords
BUDGET_KEYWORDS = ["cheap", "budget", "affordable", "inexpensive", "low cost", "value"]
PREMIUM_KEYWORDS = ["premium", "expensive", "luxury", "high end", "flagship", "pro"]

# Quality/rating keywords
QUALITY_KEYWORDS = ["best", "top", "highest rated", "popular", "recommended", "great"]

# Price pattern regex
PRICE_UNDER_PATTERN = re.compile(r'(?:under|below|less than|max|upto|up to)\s*\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE)
PRICE_OVER_PATTERN = re.compile(r'(?:over|above|more than|min|at least)\s*\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE)
PRICE_RANGE_PATTERN = re.compile(r'\$?\s*(\d+(?:,\d{3})*)\s*(?:to|-)\s*\$?\s*(\d+(?:,\d{3})*)', re.IGNORECASE)


def parse_price(price_str):
    """Parse price string to float, handling commas"""
    return float(price_str.replace(',', ''))


def detect_intent(query):
    """
    Analyze search query and detect user intent.

    Returns:
        dict with:
            - clean_query: query with intent keywords removed
            - suggested_category: detected category or None
            - suggested_sort: 'price_asc', 'price_desc', 'rating', 'popularity', or None
            - suggested_min_price: float or None
            - suggested_max_price: float or None
            - intents: list of detected intent types
    """
    query_lower = query.lower().strip()
    intents = []
    suggested_category = None
    suggested_sort = None
    suggested_min_price = None
    suggested_max_price = None

    # Detect category intent from category keywords
    for keyword, category in CATEGORY_KEYWORDS.items():
        if keyword in query_lower:
            suggested_category = category
            intents.append("category")
            break

    # If no category found, check brand keywords
    if not suggested_category:
        for brand, category in BRAND_KEYWORDS.items():
            if brand in query_lower:
                suggested_category = category
                intents.append("brand")
                break

    # Detect budget/premium intent
    for keyword in BUDGET_KEYWORDS:
        if keyword in query_lower:
            suggested_sort = "price_asc"
            intents.append("budget")
            break

    for keyword in PREMIUM_KEYWORDS:
        if keyword in query_lower:
            suggested_sort = "price_desc"
            intents.append("premium")
            break

    # Detect quality intent (only if no price intent already set)
    if suggested_sort is None:
        for keyword in QUALITY_KEYWORDS:
            if keyword in query_lower:
                suggested_sort = "rating"
                intents.append("quality")
                break

    # Detect price range patterns
    range_match = PRICE_RANGE_PATTERN.search(query_lower)
    if range_match:
        suggested_min_price = parse_price(range_match.group(1))
        suggested_max_price = parse_price(range_match.group(2))
        intents.append("price_range")
    else:
        # Detect "under X" pattern
        under_match = PRICE_UNDER_PATTERN.search(query_lower)
        if under_match:
            suggested_max_price = parse_price(under_match.group(1))
            intents.append("price_max")

        # Detect "over X" pattern
        over_match = PRICE_OVER_PATTERN.search(query_lower)
        if over_match:
            suggested_min_price = parse_price(over_match.group(1))
            intents.append("price_min")

    # Clean query - remove intent keywords for better fuzzy matching
    clean_query = query_lower

    # Remove price patterns
    clean_query = PRICE_RANGE_PATTERN.sub('', clean_query)
    clean_query = PRICE_UNDER_PATTERN.sub('', clean_query)
    clean_query = PRICE_OVER_PATTERN.sub('', clean_query)

    # Remove budget/premium keywords
    for keyword in BUDGET_KEYWORDS + PREMIUM_KEYWORDS:
        clean_query = clean_query.replace(keyword, '')

    # Remove quality keywords
    for keyword in QUALITY_KEYWORDS:
        clean_query = clean_query.replace(keyword, '')

    # Clean up extra spaces
    clean_query = ' '.join(clean_query.split()).strip()

    # If clean_query is empty, use original
    if not clean_query:
        clean_query = query

    return {
        "clean_query": clean_query,
        "original_query": query,
        "suggested_category": suggested_category,
        "suggested_sort": suggested_sort,
        "suggested_min_price": suggested_min_price,
        "suggested_max_price": suggested_max_price,
        "intents": intents
    }
