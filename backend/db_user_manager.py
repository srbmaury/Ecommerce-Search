"""
Database-based user management with PostgreSQL/Neon.
"""
from backend.database import get_db_session
from backend.models import User


def load_users():
    """Load all users from database (for backwards compatibility)."""
    session = get_db_session()
    try:
        users = session.query(User).all()
        # Convert to old format for compatibility
        users_list = []
        for user in users:
            users_list.append({
                "user_id": user.user_id,
                "username": user.username,
                "password": user.password_hash,
                "group": user.group,
                "cart": user.cart or {},
                "cluster": user.cluster
            })
        return users_list
    finally:
        session.close()


def save_users(users_list):
    """
    Save users to database (for backwards compatibility).
    This is deprecated - use direct database operations instead.
    """
    session = get_db_session()
    try:
        for user_data in users_list:
            user = session.query(User).filter_by(user_id=user_data["user_id"]).first()
            if user:
                # Update existing user
                user.username = user_data.get("username", user.username)
                user.password_hash = user_data.get("password", user.password_hash)
                user.group = user_data.get("group", user.group)
                user.cart = user_data.get("cart", {})
                user.cluster = user_data.get("cluster")
            else:
                # Create new user
                cart = user_data.get("cart", {})
                if isinstance(cart, list):
                    cart = {str(pid): 1 for pid in cart}
                
                user = User(
                    user_id=user_data["user_id"],
                    username=user_data["username"],
                    password_hash=user_data.get("password", ""),
                    group=user_data.get("group", "A"),
                    cluster=user_data.get("cluster"),
                    cart=cart
                )
                session.add(user)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_user_by_id(user_id):
    """Get a user by user_id."""
    session = get_db_session()
    try:
        return session.query(User).filter_by(user_id=user_id).first()
    finally:
        session.close()


def get_user_by_username(username):
    """Get a user by username."""
    session = get_db_session()
    try:
        return session.query(User).filter_by(username=username).first()
    finally:
        session.close()


def create_user(user_id, username, password_hash, group="A"):
    """Create a new user in the database."""
    session = get_db_session()
    try:
        user = User(
            user_id=user_id,
            username=username,
            password_hash=password_hash,
            group=group,
            cart={}
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def update_user_cart(user_id, cart):
    """Update user's cart."""
    session = get_db_session()
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        if user:
            user.cart = cart
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def update_user_cluster(user_id, cluster):
    """Update user's cluster."""
    session = get_db_session()
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        if user:
            user.cluster = cluster
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
