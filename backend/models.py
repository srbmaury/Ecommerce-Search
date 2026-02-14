"""
SQLAlchemy models for the e-commerce search application.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey,
    Index,
    Boolean,
)
from sqlalchemy.orm import (
    declarative_base,
    relationship,
    backref,
)
from sqlalchemy.dialects.postgresql import TSVECTOR


# ---------- BASE ----------

Base = declarative_base()


def utcnow():
    """UTC timestamp helper (safe for SQLAlchemy defaults)."""
    return datetime.now(timezone.utc)


# ---------- USER ----------

class User(Base):
    """User model with authentication, A/B group, and clustering."""
    __tablename__ = "users"

    user_id = Column(String(50), primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)

    group = Column(String(10), default="A", index=True)
    cluster = Column(Integer, nullable=True, index=True)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    search_events = relationship(
        "SearchEvent",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    cart_items = relationship(
        "CartItem",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.user_id} username={self.username}>"

# ---------- CART ----------

class CartItem(Base):
    """Normalized cart storage."""
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        String(50),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )

    quantity = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product")

    __table_args__ = (
        Index("idx_cart_user_product", "user_id", "product_id", unique=True),
    )

    def __repr__(self) -> str:
        return (
            f"<CartItem id={self.id} user_id={self.user_id} "
            f"product_id={self.product_id} qty={self.quantity}>"
        )

# ---------- PRODUCT ----------

class Product(Base):
    """Product catalog."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    category = Column(String(100), nullable=True, index=True)
    price = Column(Float, nullable=False)

    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    popularity = Column(Integer, default=0)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # PostgreSQL full-text search (ignored by SQLite)
    search_vector = Column(TSVECTOR)

    __table_args__ = (
        Index("idx_product_category_price", "category", "price"),
        Index("idx_product_popularity", "popularity"),
        Index(
            "ix_products_search_vector",
            "search_vector",
            postgresql_using="gin",
        ),
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} title={self.title[:40]!r}>"

# ---------- SEARCH EVENTS ----------

class SearchEvent(Base):
    """User interaction events for analytics and ML."""
    __tablename__ = "search_events"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        String(50),
        ForeignKey(
            "users.user_id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    query = Column(String(500), nullable=True, index=True)
    product_id = Column(Integer, nullable=True, index=True)

    event_type = Column(String(50), nullable=False, index=True)
    group = Column(String(10), nullable=True, index=True)
    position = Column(Integer, nullable=True)

    timestamp = Column(DateTime, default=utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="search_events")

    __table_args__ = (
        Index("idx_event_user_timestamp", "user_id", "timestamp"),
        Index("idx_event_type_timestamp", "event_type", "timestamp"),
        Index("idx_event_product_timestamp", "product_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return (
            f"<SearchEvent user_id={self.user_id} "
            f"type={self.event_type} ts={self.timestamp.isoformat()}>"
        )


# ---------- EMAIL VERIFICATION TOKEN ----------

class EmailVerificationToken(Base):
    """Token for email verification."""
    __tablename__ = "email_verification_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        String(50),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    user = relationship("User", backref=backref("email_tokens", cascade="all, delete-orphan"))

    def __repr__(self) -> str:
        return f"<EmailVerificationToken user_id={self.user_id}>"


# ---------- PASSWORD RESET TOKEN ----------

class PasswordResetToken(Base):
    """Token for password reset."""
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        String(50),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    user = relationship("User", backref=backref("reset_tokens", cascade="all, delete-orphan"))

    def __repr__(self) -> str:
        return f"<PasswordResetToken user_id={self.user_id}>"
