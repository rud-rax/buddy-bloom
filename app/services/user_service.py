from typing import Optional
import uuid
from repository.user_repository import UserRepository
from models import User
from utils.string import hash_password, check_password


class UserService:
    """Business logic for user operations."""

    def __init__(self, repository: UserRepository):
        self.repo = repository

    def register(self, username: str, email: str, bio: str, name: str, password: str) -> Optional[User]:
        # perform minimal business logic: hash password, create userId
        user_id = str(uuid.uuid4())
        password_hash = hash_password(password)
        user = User(
            userId=user_id,
            username=username,
            email=email,
            bio=bio,
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
    
    def update_profile(self, user_id: str, name: Optional[str] = None, email: Optional[str] = None, new_password: Optional[str] = None, bio: Optional[str] = None) -> Optional[User]:
        password_hash = None
        if new_password:
            password_hash = hash_password(new_password)
        
        updated_user = self.repo.update(
            user_id, 
            name=name, 
            email=email,
            bio=bio,
            password_hash=password_hash
        )
        
        return updated_user

    def get_followers(self, current_user: User, target_username: Optional[str] = None, skip: int = 0, limit: int = 100) -> tuple[bool, list[User], str]:
        """Return followers for target_username (defaults to current_user)."""
        if not current_user:
            return False, [], "Authentication required."

        target = target_username or current_user.username
        if skip < 0 or limit <= 0:
            return False, [], "Invalid pagination parameters."
        if limit > 1000:
            return False, [], "Limit too large."

        target_user = self.repo.get_by_username(target)
        if not target_user:
            return False, [], "Target user not found."

        followers = self.repo.get_followers(target, skip=skip, limit=limit)
        return True, followers, f"Found {len(followers)} followers for {target}."

    def get_following(self, current_user: User, target_username: Optional[str] = None, skip: int = 0, limit: int = 100) -> tuple[bool, list[User], str]:
        """Return users that target_username follows (defaults to current_user)."""
        if not current_user:
            return False, [], "Authentication required."

        target = target_username or current_user.username
        if skip < 0 or limit <= 0:
            return False, [], "Invalid pagination parameters."
        if limit > 1000:
            return False, [], "Limit too large."

        target_user = self.repo.get_by_username(target)
        if not target_user:
            return False, [], "Target user not found."

        following = self.repo.get_following(target, skip=skip, limit=limit)
        return True, following, f"Found {len(following)} users followed by {target}."

    def follow(self, current_user: User, target_username: str) -> tuple[bool, str]:
        """Make current_user follow target_username.

        Returns (success, message).
        """
        if not current_user:
            return False, "Authentication required."
        if current_user.username == target_username:
            return False, "You cannot follow yourself."

        target = self.repo.get_by_username(target_username)
        if not target:
            return False, "Target user not found." 

        ok = self.repo.follow(current_user.username, target_username)
        if ok:
            return True, f"You are now following {target_username}."
        return False, "Follow operation failed or already following."

    def unfollow(self, current_user: User, target_username: str) -> tuple[bool, str]:
        """Make current_user unfollow target_username.

        Returns (success, message).
        """
        if not current_user:
            return False, "Authentication required."
        if current_user.username == target_username:
            return False, "You cannot unfollow yourself."

        target = self.repo.get_by_username(target_username)
        if not target:
            return False, "Target user not found." 

        ok = self.repo.unfollow(current_user.username, target_username)
        if ok:
            return True, f"You have unfollowed {target_username}."
        return False, "Unfollow operation failed or you were not following the user."
    
    def get_mutuals(self, current_user: User, target_username: str) -> tuple[list[User], str]:
        if not current_user:
            return [], "Authentication required."
        
        target = self.repo.get_by_username(target_username)
        if not target:
            return [], "Target user not found."

        mutuals = self.repo.get_mutuals(current_user.username, target_username)
        return mutuals, f"Found {len(mutuals)} mutual connections."
    
    def get_recommendations(self, current_user: User) -> list[User]:
        if not current_user:
            return []
        return self.repo.get_recommendations(current_user.username)
    
    def search_users(self, term: str) -> list[User]:
        if not term:
            return []
        return self.repo.search(term)
    
    def get_popular_users(self) -> list[User]:
        return self.repo.get_popular()
