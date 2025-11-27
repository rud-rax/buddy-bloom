from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional

class User(BaseModel):
    """
    Represents a user in the Buddy-Bloom network.
    Works for both CSV storage and future Neo4j nodes.
    """

    userId: str
    username: str = Field(..., min_length=3, max_length=24)
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=64)
    passwordHash: Optional[str] = None  # stored internally, excluded in responses if needed
    version: int = 1

    # Computed fields (not stored in CSV — added dynamically when queried)
    followersCount: Optional[int] = 0
    followingCount: Optional[int] = 0

# # Follow relationship
# class Follow(BaseModel):
#     followerId: str
#     followeeId: str

