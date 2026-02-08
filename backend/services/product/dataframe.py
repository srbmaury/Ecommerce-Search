import pandas as pd
from sqlalchemy import func
from .shared import get_db_session, Product, serialize_product, DEFAULT_LIMIT

def get_products_df(search_query=None, limit=DEFAULT_LIMIT):
    """
    Returns products as a pandas DataFrame.
    Uses ILIKE for flexible text search.
    """
    with get_db_session() as session:
        query = session.query(Product)
        if search_query:
            # Use ILIKE for flexible partial matching
            pattern = f"%{search_query}%"
            query = query.filter(
                (Product.title.ilike(pattern)) |
                (Product.description.ilike(pattern)) |
                (Product.category.ilike(pattern))
            )
        products = query.limit(limit).all()
        df = pd.DataFrame([serialize_product(p) for p in products])
        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"])
        return df
