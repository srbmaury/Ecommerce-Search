"""
Search intent detection utilities.

Responsibilities:
- Detect product category
- Detect modifiers (gaming, wireless, etc.)
- Detect sorting intent (price / rating)
- Detect price constraints
- Produce a cleaned search query
"""

import re
from typing import List, Dict, Optional, Tuple


# ---------- NORMALIZATION ----------

_WHITESPACE_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Lowercase and normalize whitespace."""
    return _WHITESPACE_RE.sub(" ", text.lower()).strip()


def word_match(keyword: str, text: str) -> bool:
    """Check if keyword appears as a standalone word."""
    return re.search(rf"\b{re.escape(keyword)}\b", text) is not None


def parse_price(value: str) -> float:
    """Parse price string like '1,999' -> 1999.0"""
    return float(value.replace(",", ""))


# ---------- CATEGORY DEFINITIONS ----------

CORE_PRODUCT_KEYWORDS = {
    "Computers": {
        "laptop", "laptops", "notebook", "notebooks", "desktop", "desktops",
        "computer", "computers", "pc", "macbook", "chromebook", "ultrabook",
        "workstation", "all-in-one",
    },
    "Electronics": {
        "phone", "phones", "smartphone", "smartphones", "mobile", "mobiles",
        "tablet", "tablets", "ipad", "iphone", "android", "gadget", "gadgets",
        "electronics", "electronic",
    },
    "Audio": {
        "headphone", "headphones", "earbud", "earbuds", "earphone", "earphones",
        "speaker", "speakers", "soundbar", "audio", "bluetooth speaker",
        "noise cancelling", "airpod", "airpods",
    },
    "Photography": {
        "camera", "cameras", "dslr", "mirrorless", "lens", "lenses",
        "tripod", "photography", "gopro", "webcam", "camcorder",
    },
    "Networking": {
        "router", "routers", "modem", "modems", "wifi", "wi-fi",
        "mesh", "access point", "ethernet", "network", "networking",
        "range extender",
    },
    "Storage": {
        "ssd", "ssds", "hdd", "hdds", "hard drive", "hard disk",
        "drive", "drives", "storage", "pendrive", "flash drive",
        "memory card", "sd card", "external drive", "nas",
    },
    "Accessories": {
        "keyboard", "keyboards", "mouse", "mice", "charger", "chargers",
        "cable", "cables", "case", "cases", "accessory", "accessories",
        "stand", "hub", "adapter", "adapters", "monitor",
    },
    "Gaming": {
        "gaming", "console", "consoles", "controller", "controllers",
        "playstation", "xbox", "nintendo", "switch", "game", "games",
        "gamepad", "headset",
    },
    "Smart Home": {
        "smart home", "alexa", "echo", "google home", "nest",
        "smart light", "smart bulb", "bulb", "smart plug", "smart speaker",
        "home automation", "smart display",
    },
}


# ---------- MODIFIERS & SORT INTENTS ----------

MODIFIER_KEYWORDS = {
    "gaming", "wireless", "portable", "smart", "pro",
}

BUDGET_KEYWORDS = {
    "cheap", "budget", "affordable", "low cost", "inexpensive",
}

PREMIUM_KEYWORDS = {
    "premium", "luxury", "expensive", "high end", "flagship",
}

QUALITY_KEYWORDS = {
    "best", "top", "highest rated", "popular", "recommended",
}


# ---------- NEGATION PATTERNS ----------

# Match "not X", "no X", "without X", "except X" — strips the negated term
# so it doesn't confuse category detection or the text-search query.
_NEGATION_RE = re.compile(
    r"\b(?:not|no|without|except)\s+\w+(?:\s+\w+)?",
    re.IGNORECASE,
)


# ---------- PRICE PATTERNS ----------

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


# ---------- DETECTION HELPERS ----------

def detect_category(query_norm: str) -> Optional[str]:
    """Detect primary product category."""
    for category, keywords in CORE_PRODUCT_KEYWORDS.items():
        for kw in keywords:
            if word_match(kw, query_norm):
                return category
    return None


def detect_modifiers(query_norm: str) -> List[str]:
    return [kw for kw in MODIFIER_KEYWORDS if word_match(kw, query_norm)]


def detect_sort(query_norm: str) -> Optional[str]:
    if any(word_match(k, query_norm) for k in BUDGET_KEYWORDS):
        return "price_asc"
    if any(word_match(k, query_norm) for k in PREMIUM_KEYWORDS):
        return "price_desc"
    if any(word_match(k, query_norm) for k in QUALITY_KEYWORDS):
        return "rating"
    return None


def detect_price(query: str) -> Tuple[Optional[float], Optional[float]]:
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


def clean_query_text(query_norm: str) -> str:
    """Remove price phrases, negations, and intent keywords from query."""
    text = query_norm

    # Strip negated phrases before category/modifier detection skews results
    text = _NEGATION_RE.sub("", text)

    for pattern in (
        PRICE_RANGE_PATTERN,
        PRICE_UNDER_PATTERN,
        PRICE_OVER_PATTERN,
    ):
        text = pattern.sub("", text)

    removable_keywords = (
        MODIFIER_KEYWORDS
        | BUDGET_KEYWORDS
        | PREMIUM_KEYWORDS
        | QUALITY_KEYWORDS
    )

    for kw in removable_keywords:
        text = re.sub(rf"\b{re.escape(kw)}\b", "", text)

    return normalize(text)


# ---------- MAIN API ----------

def detect_intent(query: str) -> Dict:
    """
    Detect search intent from free-text query.
    """
    query_norm = normalize(query)

    category = detect_category(query_norm)
    modifiers = detect_modifiers(query_norm)
    sort = detect_sort(query_norm)
    min_price, max_price = detect_price(query)

    cleaned = clean_query_text(query_norm)
    # If cleaning stripped everything (e.g. query was only "cheap gaming"), fall
    # back to the original normalized query so the text search isn't empty.
    clean_query = cleaned or query_norm

    return {
        "original_query": query,
        "clean_query": clean_query,
        "suggested_category": category,
        "modifiers": modifiers,
        "suggested_sort": sort,
        "suggested_min_price": min_price,
        "suggested_max_price": max_price,
    }
