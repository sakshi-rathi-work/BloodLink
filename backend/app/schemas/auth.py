from typing import Literal, Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    user_id: int
    username: str
    role: str
    name: str
    profile_id: Optional[int] = None

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class RegisterRequesterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1, max_length=100)
    type: Literal["hospital", "patient"]
    phone: str = Field(..., min_length=3, max_length=20)
    address: str = Field(..., min_length=3)
