def verify_session(token):
    """
    Validate the authentication token.

    Returns:
        dict: On success, returns {'user_id': <id>}.
              On failure, returns {'error': <error_code>, 'code': <http_status>}.
    """
    # Empty or non‑string tokens are invalid.
    if not token or not isinstance(token, str):
        return {'error': 'INVALID_SESSION', 'code': 401}
    # Expected format: "token_<user_id>"
    if not token.startswith('token_'):
        return {'error': 'INVALID_SESSION', 'code': 401}
    # Extract the user identifier after the prefix.
    user_id = token.split('_', 1)[1]
    if not user_id:
        return {'error': 'INVALID_SESSION', 'code': 401}
    return {'user_id': user_id}
