from .shared import get_db_session, Product

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
        session.refresh(product)
        return product
