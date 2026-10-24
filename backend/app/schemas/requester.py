from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class RequesterUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[Literal["hospital", "patient"]] = None
    phone: Optional[str] = Field(None, min_length=1, max_length=20)
    address: Optional[str] = Field(None, min_length=1)

    @field_validator("name", "phone", "address", mode="before")
    @classmethod
    def validate_non_empty(cls, v):
        if v is not None:
            if isinstance(v, str) and not v.strip():
                raise ValueError("Field cannot be empty or whitespace only")
        return v


class RequesterResponse(BaseModel):
    requester_id: int
    user_id: int
    username: str
    name: str
    type: str
    phone: str
    address: str

    model_config = {"from_attributes": True}


class RequesterListResponse(BaseModel):
    items: List[RequesterResponse]
    total: int
    page: int
    page_size: int
