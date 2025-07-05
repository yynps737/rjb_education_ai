import re
from typing import Optional

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username: str) -> bool:
    """Validate username (alphanumeric and underscore, 3-20 chars)"""
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None

def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength
    Returns (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"

    return True, None

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove 路径 traversal attempts    filename = filename.replace('..', '')
    # Remove special characters except dot and underscore
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    return filename