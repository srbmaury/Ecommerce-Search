from sqlalchemy import desc
from .shared import get_db_session, Product

def search_products_by_category(category, limit=50):
    """Returns ORM Product objects."""
    with get_db_session() as session:
        return (
            session.query(Product)
            .filter(Product.category.ilike(f"%{category}%"))
            .order_by(desc(Product.popularity))
            .limit(limit)
            .all()
        )

def get_popular_products(limit=20):
    """Returns ORM Product objects."""
    with get_db_session() as session:
        return (
            session.query(Product)
            .order_by(desc(Product.popularity))
            .limit(limit)
            .all()
        )
