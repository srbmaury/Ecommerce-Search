"""
Utility functions for services - use database instead.
"""
from backend.db_product_service import get_products_df as _get_products_df, update_product_popularity as _update_product_popularity


def get_products_df():
    """Load products DataFrame from database, returns empty DataFrame on error."""
    return _get_products_df()


def update_product_popularity(product_id, points):
    """Update product popularity score by given points in database."""
    return _update_product_popularity(product_id, points)
