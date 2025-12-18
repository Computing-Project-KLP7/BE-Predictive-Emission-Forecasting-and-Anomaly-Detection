from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    """Schema untuk request login ke API Transtrack"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Schema untuk response login dari API Transtrack"""
    status: Optional[str] = None
    message: Optional[str] = None
    data: Optional[dict] = None
    token: Optional[str] = None
    user: Optional[dict] = None


class AuthToken(BaseModel):
    """Schema untuk token authentication"""
    access_token: str
    token_type: str
    user: Optional[dict] = None
