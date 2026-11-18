"""Authentication API endpoints for ShopEasy Support Bot."""

from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db import get_db
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class UserProfile(BaseModel):
    id: str
    name: str
    is_premium: bool

    class Config:
        from_attributes = True


@router.get("/me", response_model=UserProfile)
def get_my_profile(current_user: User = Depends(get_current_user)) -> UserProfile:
    """Return the profile of the currently authenticated customer."""
    return UserProfile.model_validate(current_user)


@router.get("/users", response_model=List[UserProfile])
def list_available_users(db: Session = Depends(get_db)) -> List[UserProfile]:
    """Return all available demo users from Neon database."""
    stmt = select(User).order_by(User.id.asc())
    users = db.execute(stmt).scalars().all()
    return [UserProfile.model_validate(u) for u in users]
