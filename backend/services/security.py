import bcrypt
import re
import string

def validate_username(username):
    if not username or not re.match(r"^[a-zA-Z0-9_]{3,50}$", username):
        return False, "invalid username"
    return True, None

def validate_password(password, complexity=True):
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."

    if complexity:
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter (A-Z)."
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter (a-z)."
        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit (0-9)."
        if not any(c in string.punctuation for c in password):
            return False, "Password must contain at least one special character (e.g. !@#$%)."

    return True, None

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
