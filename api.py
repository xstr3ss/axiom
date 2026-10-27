# Public API for protected actions.
# This module now delegates authentication and user lookup to the
# dedicated auth and database modules, propagating any error dictionaries
# unchanged.

from auth import verify_session
from database import get_user

def _authenticate(token):
    """
    Simple authentication helper retained for backward compatibility.
    It is *not* used by the protected‑action flow.
    """
    if not token:
        raise ValueError("Token cannot be empty")
    if token.startswith("token_"):
        return token.replace("token_", "USER_")
    raise ValueError("Invalid token")

def process_api_call(token):
    """
    Process an API call given an authentication token.

    Returns profile data for a valid token.
    For an empty token, returns the string "Unauthorized".
    For any other invalid token, returns a standardized error dict.
    """
    try:
        if token == "":
            return "Unauthorized"
        user = _authenticate(token)
        return f"Profile data for {user}"
    except Exception:
        return {'error': 'AUTH_FAILED', 'code': 401}

def execute_protected_action(token, action):
    """
    Execute a protected action after authenticating the session and authorising
    the user.

    Parameters
    ----------
    token : str
        Authentication token, expected format "token_<user_id>".
    action : str
        The action to perform (e.g., "delete").

    Returns
    -------
    dict
        On success: {"success": True, "executed_by": "<username>"}.
        On failure: an error dict propagated from auth/database or
        {"error": "UNAUTHORIZED_ACTION", "code": 403}.
    """
    # Step 1: Verify the session token.
    session_info = verify_session(token)
    if 'error' in session_info:
        # Propagate authentication errors directly.
        return session_info

    # Step 2: Retrieve the user record.
    user = get_user(session_info['user_id'])
    if 'error' in user:
        # Propagate user‑lookup errors directly.
        return user

    # Step 3: Authorisation check.
    # Only admins are allowed to perform the "delete" action in this simplified model.
    if action == "delete" and user.get('role') != 'admin':
        return {'error': 'UNAUTHORIZED_ACTION', 'code': 403}

    # Step 4: Successful execution.
    return {"success": True, "executed_by": user.get('username')}
