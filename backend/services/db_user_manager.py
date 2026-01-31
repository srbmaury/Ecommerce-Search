"""
Database-based user management with PostgreSQL/Neon.
"""
from backend.utils.database import get_db_session
from backend.models import User, CartItem, Product


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
                "password_hash": user.password_hash,
                "group": user.group,
                # Cart is now normalized; fetch as dict for compatibility
                "cart": {str(item.product_id): item.quantity for item in user.cart_items},
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
        # Fetch all existing users at once to avoid N+1 queries
        user_ids = [u["user_id"] for u in users_list]
        existing_users = session.query(User).filter(User.user_id.in_(user_ids)).all()
        existing_users_dict = {u.user_id: u for u in existing_users}
        
        for user_data in users_list:
            user_id = user_data["user_id"]
            user = existing_users_dict.get(user_id)
            if user:
                user.username = user_data.get("username", user.username)
                user.password_hash = user_data.get("password_hash", user.password_hash)
                user.group = user_data.get("group", user.group)
                user.cluster = user_data.get("cluster")
                # Update cart items
                cart_dict = user_data.get("cart", {})
                session.query(CartItem).filter_by(user_id=user_id).delete()
                for pid, qty in cart_dict.items():
                    session.add(CartItem(user_id=user_id, product_id=int(pid), quantity=qty))
            else:
                user = User(
                    user_id=user_data["user_id"],
                    username=user_data["username"],
                    password_hash=user_data.get("password_hash", ""),
                    group=user_data.get("group", "A"),
                    cluster=user_data.get("cluster")
                )
                session.add(user)
                session.flush()
                cart_dict = user_data.get("cart", {})
                for pid, qty in cart_dict.items():
                    session.add(CartItem(user_id=user.user_id, product_id=int(pid), quantity=qty))
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_user_by_id(user_id):
    session = get_db_session()
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        if user:
            # Return cart as dict for compatibility
            cart_dict = {str(item.product_id): item.quantity for item in user.cart_items}
            return {
                'user_id': user.user_id,
                'username': user.username,
                'password_hash': user.password_hash,
                'group': user.group,
                'cluster': user.cluster,
                'cart': cart_dict,
                'created_at': user.created_at,
                'updated_at': user.updated_at
            }
        return None
    finally:
        session.close()

def get_user_by_username(username):
    """
    Get a user by username.
    
    Returns a detached User object with all scalar attributes loaded.
    Relationships (like search_events) are not loaded and will raise an error if accessed.
    """
    session = get_db_session()
    try:
        user = session.query(User).filter_by(username=username).first()
        if user:
            # Expunge detaches the object while keeping loaded attributes accessible
            session.expunge(user)
        return user
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
            group=group
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        session.expunge(user)
        return user
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()



# CartItem-based cart operations
def add_to_cart(user_id, product_id, quantity=1):
    session = get_db_session()
    try:
        item = session.query(CartItem).filter_by(user_id=user_id, product_id=product_id).first()
        if item:
            item.quantity += quantity
        else:
            item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
            session.add(item)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def remove_from_cart(user_id, product_id, quantity=1):
    session = get_db_session()
    try:
        item = session.query(CartItem).filter_by(user_id=user_id, product_id=product_id).first()
        if item:
            if item.quantity > quantity:
                item.quantity -= quantity
            else:
                session.delete(item)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def clear_cart(user_id):
    session = get_db_session()
    try:
        session.query(CartItem).filter_by(user_id=user_id).delete()
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_cart(user_id):
    session = get_db_session()
    try:
        items = session.query(CartItem).filter_by(user_id=user_id).all()
        return {str(item.product_id): item.quantity for item in items}
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
