from sqlalchemy import update, text
from .shared import get_db_session, Product, serialize_product

def update_product_popularity(product_id, increment):
    """Atomically increment product popularity."""
    with get_db_session() as session:
        result = session.execute(
            update(Product)
            .where(Product.id == int(product_id))
            .values(popularity=Product.popularity + increment)
        )
        return result.rowcount > 0

def update_product(product_id, **fields):
    """Partial update of editable product fields (title/description/category/price).

    Returns the serialized product, or None if it doesn't exist.
    """
    with get_db_session() as session:
        result = session.execute(
            update(Product)
            .where(Product.id == int(product_id))
            .values(**fields)
        )
        if result.rowcount == 0:
            return None

        if session.bind.dialect.name == "postgresql" and (
            {"title", "description", "category"} & fields.keys()
        ):
            session.execute(
                text("""
                    UPDATE products
                    SET search_vector =
                        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
                        setweight(to_tsvector('english', coalesce(category, '')), 'B') ||
                        setweight(to_tsvector('english', coalesce(description, '')), 'C')
                    WHERE id = :product_id
                """),
                {"product_id": int(product_id)},
            )

        session.commit()
        product = session.query(Product).filter_by(id=int(product_id)).first()
        return serialize_product(product)
