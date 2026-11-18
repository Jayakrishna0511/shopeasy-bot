"""Approval token manager for risky agent actions (e.g. order cancellations).

Enforces:
- Single-use tokens
- Expiration timestamps (default 10 minutes)
- Customer ownership verification (`token.user_id == current_user.id`)
"""

import time
import uuid
from typing import Any, Dict, Optional
from fastapi import HTTPException, status

# In-memory storage for pending approval requests: token -> approval_data
_pending_approvals: Dict[str, Dict[str, Any]] = {}
DEFAULT_EXPIRY_SECONDS = 600  # 10 minutes


def create_approval_token(
    action: str,
    user_id: str,
    details: Dict[str, Any],
    expiry_seconds: int = DEFAULT_EXPIRY_SECONDS,
) -> str:
    """Create a cryptographically secure, expiring approval token for a customer action."""
    token = f"appr_{uuid.uuid4().hex}"
    _pending_approvals[token] = {
        "action": action,
        "user_id": user_id.lower().strip(),
        "details": details,
        "created_at": time.time(),
        "expires_at": time.time() + expiry_seconds,
        "used": False,
    }
    return token


def consume_approval_token(token: str, user_id: str) -> Dict[str, Any]:
    """Validate, verify ownership, and consume an approval token.

    Security checks:
    1. Token exists
    2. Token has not already been used (single-use)
    3. Token has not expired
    4. Authenticated customer owns this token (cannot approve another user's action)

    Returns:
        The details dict associated with the approved action.
    """
    clean_token = str(token).strip()
    clean_user = str(user_id).lower().strip()

    approval = _pending_approvals.get(clean_token)
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found or invalid token.",
        )

    if approval["used"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This action has already been confirmed and processed.",
        )

    if time.time() > approval["expires_at"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation window has expired. Please request the cancellation again.",
        )

    if approval["user_id"] != clean_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: You cannot approve an action for another customer's account.",
        )

    # Mark token as consumed (single-use)
    approval["used"] = True
    return approval
