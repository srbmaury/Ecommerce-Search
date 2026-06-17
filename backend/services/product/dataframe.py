import pandas as pd
from sqlalchemy import desc, func
from .shared import get_db_session, Product, serialize_product, DEFAULT_LIMIT


def _is_postgres(session) -> bool:
    return session.bind.dialect.name == "postgresql"


def get_products_df(search_query=None, category_filter=None, limit=DEFAULT_LIMIT):
    """
    Returns products as a pandas DataFrame.

    search_query: free-text search (Postgres full-text / SQLite LIKE)
    category_filter: exact category match (case-insensitive), applied in addition
                     to or independently of search_query
    """
    with get_db_session() as session:
        query = session.query(Product)
        if search_query:
            if _is_postgres(session):
                ts_query = func.plainto_tsquery("english", search_query)
                rank = func.ts_rank_cd(Product.search_vector, ts_query)
                query = (
                    query
                    .filter(Product.search_vector.op("@@")(ts_query))
                    .order_by(desc(rank), desc(Product.popularity))
                )
            else:
                # SQLite/local fallback
                pattern = f"%{search_query}%"
                query = query.filter(
                    (Product.title.ilike(pattern)) |
                    (Product.description.ilike(pattern)) |
                    (Product.category.ilike(pattern))
                )
        if category_filter:
            query = query.filter(Product.category.ilike(category_filter))
        if not search_query:
            # Without text ranking, fall back to popularity order
            query = query.order_by(desc(Product.popularity))
        products = query.limit(limit).all()
        df = pd.DataFrame([serialize_product(p) for p in products])
        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"])
        return df
