from .shared import get_db_session, Product
from sqlalchemy import text

def create_product(
    title,
    description,
    category,
    price,
    rating=0,
    review_count=0,
    popularity=0,
):
    with get_db_session() as session:
        product = Product(
            title=title,
            description=description,
            category=category,
            price=price,
            rating=rating,
            review_count=review_count,
            popularity=popularity,
        )
        session.add(product)
        session.flush()

        if session.bind.dialect.name == "postgresql":
            session.execute(
                text("""
                    UPDATE products
                    SET search_vector =
                        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
                        setweight(to_tsvector('english', coalesce(category, '')), 'B') ||
                        setweight(to_tsvector('english', coalesce(description, '')), 'C')
                    WHERE id = :product_id
                """),
                {"product_id": product.id},
            )

        session.commit()
        session.refresh(product)
        return product
