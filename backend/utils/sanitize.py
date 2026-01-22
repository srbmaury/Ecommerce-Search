def sanitize_user_id(user_id):
    if user_id is None:
        return None

    user_id = str(user_id).strip()
    if not user_id:
        return None

    if len(user_id) > 128 or any(c in user_id for c in ("\n", "\r", ",")):
        return None

    return user_id


def sanitize_csv_field(value):
    """
    Sanitize a field value to prevent CSV injection attacks.
    
    CSV injection occurs when values starting with =, +, -, @, or containing
    newlines are interpreted as formulas by spreadsheet applications like
    Excel or Google Sheets. This function neutralizes such values by:
    - Converting to string and stripping whitespace
    - Removing newlines and carriage returns
    - Prefixing dangerous leading characters with a single quote
    - Limiting length to prevent abuse
    
    Args:
        value: The value to sanitize (can be None, str, int, etc.)
    
    Returns:
        Sanitized string safe for CSV output
    """
    if value is None:
        return ""
    
    # Convert to string and strip whitespace
    sanitized = str(value).strip()
    
    # Remove newlines and carriage returns which could break CSV structure
    sanitized = sanitized.replace("\n", " ").replace("\r", " ")
    
    # Limit length to prevent abuse (adjust as needed for your use case)
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000]
    
    # Prefix dangerous leading characters to prevent formula execution
    # Excel/Sheets interpret =, +, -, @ at the start as formula indicators
    if sanitized and sanitized[0] in ('=', '+', '-', '@'):
        sanitized = "'" + sanitized
    
    return sanitized
