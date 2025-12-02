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
            bio=user.bio,
        )
        if not data:
            return None
        return self._to_model(data)

    def get_by_username(self, username: str) -> Optional[User]:
        data = self.crud.get_user_by_username(username)
        if not data:
            return None
        return self._to_model(data)
    
    def update(self, user_id: str, name: Optional[str] = None, email: Optional[str] = None, password_hash: Optional[str] = None, bio: Optional[str] = None) -> Optional[User]:
        data = self.crud.update_user(
            user_id=user_id,
            name=name,
            email=email,
            bio=bio,
            password_hash=password_hash
        )
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
            bio=data.get("bio") or "",
            passwordHash=data.get("passwordHash"),
            version=int(data.get("version", 1)),
            followersCount=int(data.get("followersCount", 0)) if data.get("followersCount") is not None else 0,
            followingCount=int(data.get("followingCount", 0)) if data.get("followingCount") is not None else 0,
        )

    def follow(self, follower_username: str, followee_username: str) -> bool:
        """Create a follow relationship via the CRUD layer."""
        return self.crud.follow_user(follower_username, followee_username)

    def unfollow(self, follower_username: str, followee_username: str) -> bool:
        """Remove a follow relationship via the CRUD layer."""
        return self.crud.unfollow_user(follower_username, followee_username)

    def get_followers(self, username: str, skip: int = 0, limit: int = 100) -> list[User]:
        """Return list of `User` models representing users who follow `username`."""
        raw = self.crud.get_followers_for_user(username, skip=skip, limit=limit)
        return [self._to_model(r) for r in raw] if raw else []

    def get_following(self, username: str, skip: int = 0, limit: int = 100) -> list[User]:
        """Return list of `User` models representing users whom `username` follows."""
        raw = self.crud.get_following_for_user(username, skip=skip, limit=limit)
        return [self._to_model(r) for r in raw] if raw else []
