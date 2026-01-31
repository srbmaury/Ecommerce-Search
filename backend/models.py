"""
SQLAlchemy models for the e-commerce search application.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

Base = declarative_base()



class User(Base):
    """User model with authentication and cart information."""
    __tablename__ = 'users'
    user_id = Column(String(50), primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    group = Column(String(10), default='A')  # A/B testing group
    cluster = Column(Integer, nullable=True, index=True)  # User cluster for recommendations
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    # Relationship to search events
    search_events = relationship('SearchEvent', back_populates='user', cascade='all, delete-orphan')
    def __repr__(self):
        return f"<User(user_id='{self.user_id}', username='{self.username}')>"

# CartItem model for normalized cart storage
class CartItem(Base):
    __tablename__ = 'cart_items'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    user = relationship('User', backref=backref('cart_items', cascade='all, delete-orphan'))
    product = relationship('Product')
    def __repr__(self):
        return f"<CartItem(id={self.id}, user_id='{self.user_id}', product_id={self.product_id}, quantity={self.quantity})>"


class Product(Base):
    """Product model with all product information."""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    price = Column(Float, nullable=False)
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    popularity = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_product_category_price', 'category', 'price'),
        Index('idx_product_popularity', 'popularity'),
    )
    
    def __repr__(self):
        return f"<Product(id={self.id}, title='{self.title}')>"


class SearchEvent(Base):
    """Search event model for tracking user interactions."""
    __tablename__ = 'search_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    query = Column(String(500), nullable=True, index=True)
    product_id = Column(Integer, nullable=True, index=True)  # References Product.id
    event_type = Column(String(50), nullable=False, index=True)  # click, add_to_cart, search
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    group = Column(String(10), nullable=True, index=True)  # A/B testing group at time of event
    position = Column(Integer, nullable=True)  # Position in search results
    
    # Relationship to user
    user = relationship('User', back_populates='search_events')
    
    # Indexes for analytics queries
    __table_args__ = (
        Index('idx_event_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_event_type_timestamp', 'event_type', 'timestamp'),
        Index('idx_event_product', 'product_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<SearchEvent(user_id='{self.user_id}', event_type='{self.event_type}', timestamp='{self.timestamp}')>"
