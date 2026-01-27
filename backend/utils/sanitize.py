def sanitize_user_id(user_id):
    """
    Sanitize and validate user ID input.
    
    Args:
        user_id: The user ID to sanitize (can be None, str, int, etc.)
    
    Returns:
        Sanitized user ID string or None if invalid
    """
    if user_id is None:
        return None

    user_id = str(user_id).strip()
    if not user_id:
        return None

    # Basic validation: length and no special characters that could cause issues
    if len(user_id) > 128 or any(c in user_id for c in ("\n", "\r", ",")):
        return None

    return user_id
