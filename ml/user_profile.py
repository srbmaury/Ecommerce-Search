import logging
from typing import Dict

import pandas as pd

from backend.services.db_event_service import get_events_df
from backend.services.db_product_service import get_products_df


logger = logging.getLogger(__name__)


EVENT_WEIGHTS = {
    "click": 1,
    "add_to_cart": 2,
}


def build_user_profiles() -> Dict[str, dict]:
    """
    Build user preference profiles from interaction data.

    Profile structure:
    {
        user_id: {
            "category_pref": {category: normalized_weight},
            "avg_price": weighted_average_price
        }
    }
    """
    events = get_events_df()
    products = get_products_df()

    if events.empty or products.empty:
        logger.warning("Events or products table is empty")
        return {}

    events = events.copy()
    products = products.copy()

    events["product_id"] = events["product_id"].astype(str)
    products["product_id"] = products["product_id"].astype(str)

    merged = events.merge(products, on="product_id", how="inner")

    interactions = merged[merged["event"].isin(EVENT_WEIGHTS)].copy()
    if interactions.empty:
        logger.warning("No click or add_to_cart interactions found")
        return {}

    # Apply event weights
    interactions["weight"] = interactions["event"].map(EVENT_WEIGHTS)

    # ------------------------------------------------------------------
    # Category preferences (weighted, normalized)
    # ------------------------------------------------------------------
    category_weights = (
        interactions
        .groupby(["user_id", "category"])["weight"]
        .sum()
    )

    category_totals = category_weights.groupby(level=0).sum()

    category_pref = (
        category_weights
        .div(category_totals, level=0)
        .reset_index()
    )

    # ------------------------------------------------------------------
    # Price preference (weighted average)
    # ------------------------------------------------------------------
    price_sums = (
        interactions
        .assign(weighted_price=lambda df: df["price"] * df["weight"])
        .groupby("user_id")[["weighted_price", "weight"]]
        .sum()
    )
    price_pref = price_sums["weighted_price"] / price_sums["weight"]

    # ------------------------------------------------------------------
    # Assemble profiles
    # ------------------------------------------------------------------
    profiles = {}

    for user_id, user_cats in category_pref.groupby("user_id"):
        profiles[user_id] = {
            "category_pref": dict(
                zip(user_cats["category"], user_cats["weight"])
            ),
            "avg_price": float(price_pref.get(user_id, 0.0)),
        }

    logger.info("Built profiles for %d users", len(profiles))
    return profiles
