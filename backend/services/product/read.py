from .shared import get_db_session, Product, serialize_product, DEFAULT_LIMIT

def get_all_products(limit=DEFAULT_LIMIT):
    with get_db_session() as session:
        products = session.query(Product).limit(limit).all()
        return [serialize_product(p) for p in products]

def get_products_by_ids(product_ids):
    if not product_ids:
        return []
    ids = [int(pid) for pid in product_ids]
    with get_db_session() as session:
        products = session.query(Product).filter(Product.id.in_(ids)).all()
        return [serialize_product(p) for p in products]

def get_product_by_id(product_id):
    with get_db_session() as session:
        return session.query(Product).filter_by(id=int(product_id)).first()
