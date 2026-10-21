from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class StaffCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1, max_length=100)
    role: Literal["staff", "admin"]


class StaffUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[Literal["staff", "admin"]] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class StaffResponse(BaseModel):
    staff_id: int
    user_id: int
    username: str
    name: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class StaffListResponse(BaseModel):
    items: List[StaffResponse]
    total: int
    page: int
    page_size: int
