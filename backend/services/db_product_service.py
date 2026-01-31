"""
Database service for product operations.
"""
import pandas as pd
from sqlalchemy import desc
from backend.utils.database import get_db_session
from backend.models import Product


def get_all_products():
    """Get all products as a list of dictionaries."""
    session = get_db_session()
    try:
        products = session.query(Product).all()
        return [{
            'product_id': p.id,  # Return as product_id for API compatibility
            'title': p.title,
            'description': p.description,
            'category': p.category,
            'price': p.price,
            'rating': p.rating,
            'review_count': p.review_count,
            'popularity': p.popularity,
            'created_at': p.created_at
        } for p in products]
    finally:
        session.close()


def get_products_df():
    """Get all products as a pandas DataFrame (for ML compatibility)."""
    products = get_all_products()
    if not products:
        return pd.DataFrame()
    df = pd.DataFrame(products)
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at'])
    return df


def get_product_by_id(product_id):
    """Get a single product by ID."""
    session = get_db_session()
    try:
        return session.query(Product).filter_by(id=int(product_id)).first()
    finally:
        session.close()


def update_product_popularity(product_id, increment):
    """Update product popularity by incrementing."""
    session = get_db_session()
    try:
        product = session.query(Product).filter_by(id=int(product_id)).first()
        if product:
            product.popularity += increment
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def search_products_by_category(category, limit=50):
    """Search products by category."""
    session = get_db_session()
    try:
        products = session.query(Product).filter(
            Product.category.ilike(f'%{category}%')
        ).order_by(desc(Product.popularity)).limit(limit).all()
        return products
    finally:
        session.close()


def get_popular_products(limit=20):
    """Get most popular products."""
    session = get_db_session()
    try:
        products = session.query(Product).order_by(
            desc(Product.popularity)
        ).limit(limit).all()
        return products
    finally:
        session.close()


def get_products_by_ids(product_ids):
    """Get multiple products by their IDs."""
    session = get_db_session()
    try:
        # Convert all product_ids to integers
        int_product_ids = [int(pid) for pid in product_ids]
        products = session.query(Product).filter(
            Product.id.in_(int_product_ids)
        ).all()
        return [{
            'product_id': p.id,
            'title': p.title,
            'description': p.description,
            'category': p.category,
            'price': p.price,
            'rating': p.rating,
            'review_count': p.review_count,
            'popularity': p.popularity,
            'created_at': p.created_at
        } for p in products]
    finally:
        session.close()


def create_product(title, description, category, price, rating=0, review_count=0, popularity=0):
    """Create a new product."""
    session = get_db_session()
    try:
        product = Product(
            title=title,
            description=description,
            category=category,
            price=price,
            rating=rating,
            review_count=review_count,
            popularity=popularity
        )
        session.add(product)
        session.commit()
        session.refresh(product)
        return product
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
