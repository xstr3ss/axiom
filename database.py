# In‑memory user store.
_USERS = {
    '123': {'username': 'admin_shyam', 'role': 'admin'},
    '999': {'username': 'guest_gopal', 'role': 'guest'},
}

def get_user(user_id):
    """
    Retrieve a user record by its identifier.

    Returns:
        dict: On success, returns {'username': <str>, 'role': <str>}.
              On failure, returns {'error': 'USER_NOT_FOUND', 'code': 404}.
    """
    user = _USERS.get(user_id)
    if user is None:
        return {'error': 'USER_NOT_FOUND', 'code': 404}
    return user
