"""
PharmaMind AI - Authentication Schemas
"""

from typing import Optional
from pydantic import BaseModel, Field

class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str


class LoginRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$", description="Valid user email address")
    password: str = Field(..., min_length=6)


class UserCreate(BaseModel):
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$", description="Valid user email address")
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None
    role: Optional[str] = "researcher"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    is_superuser: bool

    class Config:
        from_attributes = True
