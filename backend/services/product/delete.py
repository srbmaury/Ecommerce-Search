from .shared import get_db_session, Product

def delete_product(product_id):
    """Delete a product. Cart items and reviews cascade via FK ondelete.

    Returns True if a row was deleted, False if it didn't exist.
    """
    with get_db_session() as session:
        product = session.query(Product).filter_by(id=int(product_id)).first()
        if not product:
            return False
        session.delete(product)
        session.commit()
        return True
