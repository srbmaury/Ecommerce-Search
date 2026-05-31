import pandas as pd
from sqlalchemy import desc, func
from .shared import get_db_session, Product, serialize_product, DEFAULT_LIMIT


def _is_postgres(session) -> bool:
    return session.bind.dialect.name == "postgresql"


def get_products_df(search_query=None, limit=DEFAULT_LIMIT):
    """
    Returns products as a pandas DataFrame.
    Uses PostgreSQL full-text search in production and a SQLite-friendly
    fallback for local development.
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
                # SQLite/local fallback. Production should use the Postgres
                # tsvector path above to avoid full table scans.
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
