import re
from typing import List, Dict, Optional

# ------------------------
# Helper functions
# ------------------------

def normalize(text: str) -> str:
    """Lowercase and strip extra spaces."""
    return re.sub(r'\s+', ' ', text.lower()).strip()

def word_match(keyword: str, text: str) -> bool:
    """Check if keyword appears as a standalone word."""
    return re.search(rf'\b{re.escape(keyword)}\b', text) is not None

def parse_price(value: str) -> float:
    return float(value.replace(',', ''))

# ------------------------
# Core Product Keywords
# ------------------------

CORE_PRODUCT_KEYWORDS = {
    ("laptop", "laptops", "desktop", "computer", "pc"): "Computers",
    ("phone", "phones", "smartphone", "mobile", "tablet"): "Electronics",
    ("headphones", "headphone", "earbuds", "earphones", "speaker", "speakers"): "Audio",
    ("camera", "cameras", "dslr", "lens", "tripod"): "Photography",
    ("router", "modem", "wifi", "mesh"): "Networking",
    ("ssd", "hdd", "drive", "storage", "pendrive", "memory card"): "Storage",
    ("keyboard", "mouse", "charger", "cable", "case", "accessory", "accessories"): "Accessories",
    ("console", "controller", "playstation", "xbox"): "Gaming",
    ("alexa", "echo", "nest", "smart light", "bulb"): "Smart Home",
}

# ------------------------
# Modifiers / Attributes
# ------------------------

MODIFIER_KEYWORDS = {
    "gaming", "wireless", "budget", "cheap", "premium", "portable", "smart", "pro"
}

BUDGET_KEYWORDS = {"cheap", "budget", "affordable", "low cost", "inexpensive"}
PREMIUM_KEYWORDS = {"premium", "luxury", "expensive", "high end", "flagship"}
QUALITY_KEYWORDS = {"best", "top", "highest rated", "popular", "recommended"}

# ------------------------
# Price Patterns
# ------------------------

PRICE_UNDER_PATTERN = re.compile(
    r"(?:under|below|less than|upto|up to|max)\s*\$?\s*(\d+(?:,\d{3})*)",
    re.IGNORECASE,
)

PRICE_OVER_PATTERN = re.compile(
    r"(?:over|above|more than|min|at least)\s*\$?\s*(\d+(?:,\d{3})*)",
    re.IGNORECASE,
)

PRICE_RANGE_PATTERN = re.compile(
    r"(?:between\s+)?\$?\s*(\d+(?:,\d{3})*)\s*(?:to|-|and)\s*\$?\s*(\d+(?:,\d{3})*)",
    re.IGNORECASE,
)

# ------------------------
# Detection Functions
# ------------------------

def detect_category(query: str) -> Optional[str]:
    """Detect core product category."""
    query_norm = normalize(query)
    for keywords, category in CORE_PRODUCT_KEYWORDS.items():
        for kw in keywords:
            if word_match(kw, query_norm):
                return category
    return None

def detect_modifiers(query: str) -> List[str]:
    query_norm = normalize(query)
    return [kw for kw in MODIFIER_KEYWORDS if word_match(kw, query_norm)]

def detect_sort(query: str) -> Optional[str]:
    query_norm = normalize(query)
    if any(word_match(k, query_norm) for k in BUDGET_KEYWORDS):
        return "price_asc"
    if any(word_match(k, query_norm) for k in PREMIUM_KEYWORDS):
        return "price_desc"
    if any(word_match(k, query_norm) for k in QUALITY_KEYWORDS):
        return "rating"
    return None

def detect_price(query: str):
    min_price = max_price = None
    if m := PRICE_RANGE_PATTERN.search(query):
        min_price = parse_price(m.group(1))
        max_price = parse_price(m.group(2))
    else:
        if m := PRICE_UNDER_PATTERN.search(query):
            max_price = parse_price(m.group(1))
        if m := PRICE_OVER_PATTERN.search(query):
            min_price = parse_price(m.group(1))
    return min_price, max_price

# ------------------------
# Main API
# ------------------------

def detect_intent(query: str) -> Dict:
    # First detect category (core product)
    category = detect_category(query)
    modifiers = detect_modifiers(query)
    sort = detect_sort(query)
    min_price, max_price = detect_price(query)

    # Clean query for search
    clean_query = normalize(query)
    for pattern in (PRICE_RANGE_PATTERN, PRICE_UNDER_PATTERN, PRICE_OVER_PATTERN):
        clean_query = pattern.sub("", clean_query)
    for kw in MODIFIER_KEYWORDS | BUDGET_KEYWORDS | PREMIUM_KEYWORDS | QUALITY_KEYWORDS:
        clean_query = re.sub(rf'\b{re.escape(kw)}\b', '', clean_query)
    clean_query = normalize(clean_query) or query

    return {
        "original_query": query,
        "clean_query": clean_query,
        "suggested_category": category,
        "modifiers": modifiers,
        "suggested_sort": sort,
        "suggested_min_price": min_price,
        "suggested_max_price": max_price,
    }
