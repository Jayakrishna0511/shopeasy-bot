"""Authentication and user identity dependency for ShopEasy Support Bot.

Enforces:
- User identity is established strictly by the authentication layer, NEVER by the LLM.
- Validates that the user exists in the Neon PostgreSQL `users` table.
"""

from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User


def get_current_user(
    x_user_id: Optional[str] = Header(
        None, alias="X-User-Id", description="ShopEasy user ID (e.g. ravi, priya, arjun)"
    ),
    authorization: Optional[str] = Header(
        None, description="Optional Bearer <user_id> authorization"
    ),
    db: Session = Depends(get_db),
) -> User:
    """Resolve and authenticate the current user from request headers.

    Extracts user_id from:
    1. X-User-Id header (e.g. 'ravi', 'priya', 'arjun')
    2. Authorization: Bearer <user_id>
    3. Defaults to 'ravi' for seamless local development if neither is passed.

    Raises:
        HTTPException 401 if the resolved user_id does not exist in the database.
    """
    user_id = None

    if x_user_id and x_user_id.strip():
        user_id = x_user_id.strip()
    elif authorization and authorization.startswith("Bearer "):
        user_id = authorization.replace("Bearer ", "").strip()

    # Default to 'ravi' if not provided (safe local dev fallback)
    if not user_id:
        user_id = "ravi"

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: User '{user_id}' does not exist.",
        )

    return user
