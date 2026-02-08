from sqlalchemy import update
from .shared import get_db_session, Product

def update_product_popularity(product_id, increment):
    """Atomically increment product popularity."""
    with get_db_session() as session:
        result = session.execute(
            update(Product)
            .where(Product.id == int(product_id))
            .values(popularity=Product.popularity + increment)
        )
        return result.rowcount > 0
