import pandas as pd
from sqlalchemy import desc, func, update
from backend.utils.database import get_db_session
from backend.models import Product

DEFAULT_LIMIT = 1000

def serialize_product(product):
    """Convert Product ORM object to API-safe dict."""
    return {
        "product_id": product.id,
        "title": product.title,
        "description": product.description,
        "category": product.category,
        "price": product.price,
        "rating": product.rating,
        "review_count": product.review_count,
        "popularity": product.popularity,
        "created_at": product.created_at,
    }
