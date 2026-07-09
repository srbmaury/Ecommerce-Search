import logging
from typing import Dict

import pandas as pd

from backend.services.db_event_service import get_events_df
from backend.services.db_product_service import get_products_df
from backend.utils.database import get_db_session
from backend.models import User


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
    # get_products_df/get_events_df default to limit=1000, a safety cap meant
    # for interactive API calls. Batch ML training needs the full catalog/
    # history, or most events end up referencing products outside the
    # truncated (popularity-ordered) product sample — undercounting real
    # signal and looking like data corruption.
    events = get_events_df(limit=None)
    products = get_products_df(limit=None)

    if events.empty or products.empty:
        logger.warning("Events or products table is empty")
        return {}

    events = events.copy()
    products = products.copy()

    # events.product_id loads as float64 (nullable column) vs products.product_id
    # as int64 — casting straight to str gives "16923.0" vs "16923", which never
    # match and silently merge to nothing. Go through nullable Int64 first so
    # both sides render identically.
    events["product_id"] = events["product_id"].astype("Int64").astype(str)
    products["product_id"] = products["product_id"].astype("Int64").astype(str)
    # Normalize category casing so profile keys match intent-detection output
    products["category"] = products["category"].fillna("").str.strip()

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

    # Attach cluster assignment so cluster-based boosting works in search and recs.
    # profile.get("cluster") is checked by both _get_cluster_category_boost callers;
    # without this it always returns None and the entire feature is a no-op.
    user_clusters = _load_user_clusters()
    for uid, profile in profiles.items():
        profile["cluster"] = user_clusters.get(str(uid))

    logger.info("Built profiles for %d users", len(profiles))
    return profiles


def _load_user_clusters() -> Dict[str, int]:
    """Return {str(user_id): cluster} for users that have been assigned a cluster."""
    try:
        with get_db_session() as session:
            rows = (
                session.query(User.user_id, User.cluster)
                .filter(User.cluster.isnot(None))
                .all()
            )
            return {str(user_id): cluster for user_id, cluster in rows}
    except Exception:
        logger.warning("Failed to load user clusters; cluster boosting will be disabled")
        return {}
