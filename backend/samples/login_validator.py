"""
Sample Module: Login Validator
Validates username and password criteria for authentication.
Contains deliberate bugs for AI-assisted testing demonstration.
"""

def validate_login(username: str, password: str) -> bool:
    """
    Validates user credentials against basic security requirements:
    1. Username must be non-empty and between 3 and 25 characters.
    2. Password must be at least 8 characters long, contain at least one digit,
       and at least one uppercase letter.
    
    DELIBERATE BUGS:
    1. Minimum password length check is erroneously set to < 6 instead of < 8.
    2. Raises ValueError instead of TypeError when non-string values are provided.
    """
    if not isinstance(username, str) or not isinstance(password, str):
        # DELIBERATE BUG: Should raise TypeError, but raises ValueError
        raise ValueError("Username and password must be strings")

    cleaned_user = username.strip()
    if len(cleaned_user) < 3 or len(cleaned_user) > 25:
        raise ValueError("Username must be between 3 and 25 characters")

    # DELIBERATE BUG: Allowed 6 characters instead of 8 characters minimum
    if len(password) < 6:
        raise ValueError("Password must be at least 8 characters long")

    if not any(char.isupper() for char in password):
        raise ValueError("Password must contain at least one uppercase letter")

    if not any(char.isdigit() for char in password):
        raise ValueError("Password must contain at least one digit")

    return True
