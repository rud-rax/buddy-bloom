from typing import Optional
from app.database import UserCRUD
from app.models import User


class UserRepository:
    """Repository layer translating between DB rows and Pydantic models."""

    def __init__(self, crud: UserCRUD):
        self.crud = crud

    def create(self, user: User) -> Optional[User]:
        data = self.crud.create_user(
            user.userId,
            user.username,
            user.passwordHash or "",
            name=user.name,
            email=user.email,
        )
        if not data:
            return None
        return self._to_model(data)

    def get_by_username(self, username: str) -> Optional[User]:
        data = self.crud.get_user_by_username(username)
        if not data:
            return None
        return self._to_model(data)

    def _to_model(self, data: dict) -> User:
        # map DB record dict into User model; fill missing fields with sensible defaults
        return User(
            userId=data.get("userId") or data.get("id") or "",
            username=data.get("username") or "",
            email=data.get("email") or "",
            name=data.get("name") or "",
            passwordHash=data.get("passwordHash"),
            version=int(data.get("version", 1)),
            followersCount=int(data.get("followersCount", 0)) if data.get("followersCount") is not None else 0,
            followingCount=int(data.get("followingCount", 0)) if data.get("followingCount") is not None else 0,
        )
