from pydantic import BaseModel, EmailStr, field_serializer
from typing import Optional, Any
from datetime import datetime
import uuid

class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: Any
    email: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    auth_provider: str
    created_at: datetime

    @field_serializer('id')
    def serialize_id(self, value, _info):
        return str(value)

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenRefresh(BaseModel):
    refresh_token: str

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class PasswordReset(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
