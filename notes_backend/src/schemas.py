from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

# User schemas
class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=100, description="Username")

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=6, description="User password")

class UserResponse(UserBase):
    """Schema for user response."""
    id: int = Field(..., description="User ID")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="User creation timestamp")
    
    class Config:
        from_attributes = True

# Note schemas
class NoteBase(BaseModel):
    """Base note schema with common fields."""
    title: str = Field(..., min_length=1, max_length=255, description="Note title")
    content: Optional[str] = Field(None, description="Note content")

class NoteCreate(NoteBase):
    """Schema for creating a new note."""
    pass

class NoteUpdate(BaseModel):
    """Schema for updating a note."""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Note title")
    content: Optional[str] = Field(None, description="Note content")

class NoteResponse(NoteBase):
    """Schema for note response."""
    id: int = Field(..., description="Note ID")
    owner_id: int = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Note creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Note last update timestamp")
    
    class Config:
        from_attributes = True

# Authentication schemas
class Token(BaseModel):
    """Schema for authentication token."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(..., description="Token type")

class TokenData(BaseModel):
    """Schema for token data."""
    username: Optional[str] = None

class UserLogin(BaseModel):
    """Schema for user login."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
