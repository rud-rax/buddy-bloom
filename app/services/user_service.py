from typing import Optional
import uuid
from app.repository.user_repository import UserRepository
from app.models import User
from app.utils.string import hash_password, check_password


class UserService:
    """Business logic for user operations."""

    def __init__(self, repository: UserRepository):
        self.repo = repository

    def register(self, username: str, email: str, name: str, password: str) -> Optional[User]:
        # perform minimal business logic: hash password, create userId
        user_id = str(uuid.uuid4())
        password_hash = hash_password(password)
        user = User(
            userId=user_id,
            username=username,
            email=email,
            name=name,
            passwordHash=password_hash,
        )
        created = self.repo.create(user)
        return created

    def authenticate(self, username: str, password: str) -> Optional[User]:
        user = self.repo.get_by_username(username)
        if not user:
            return None
        if not user.passwordHash:
            return None
        if check_password(password, user.passwordHash):
            return user
        return None
