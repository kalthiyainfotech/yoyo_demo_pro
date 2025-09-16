from typing import Dict, Any, List


def other_accounts(request) -> Dict[str, Any]:
    """
    Provide `other_accounts` to all templates based on session-stored accounts.
    Excludes the currently active user (by session user_id) if present.
    Each account is a dict with keys: id, name, email.
    """
    try:
        accounts: List[dict] = request.session.get("accounts", []) or []
        current_user_id = request.session.get("user_id")
        if current_user_id is None:
            return {"other_accounts": accounts}
        filtered = [a for a in accounts if int(a.get("id", -1)) != int(current_user_id)]
        return {"other_accounts": filtered}
    except Exception:
        # Never break template rendering due to session issues
        return {"other_accounts": []}


