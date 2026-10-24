from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


class CampCreateRequest(BaseModel):
    location: str = Field(..., min_length=1, max_length=255)
    camp_date: date
    target_units: int = Field(..., gt=0)
    units_collected: Optional[int] = Field(0, ge=0)


class CampUpdateRequest(BaseModel):
    location: Optional[str] = Field(None, min_length=1, max_length=255)
    camp_date: Optional[date] = None
    target_units: Optional[int] = Field(None, gt=0)
    units_collected: Optional[int] = Field(None, ge=0)


class CampResponse(BaseModel):
    camp_id: int
    location: str
    camp_date: date
    target_units: int
    units_collected: int

    model_config = {"from_attributes": True}


class CampListResponse(BaseModel):
    items: List[CampResponse]
    total: int
    page: int
    page_size: int
