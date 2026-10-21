from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from app.core.constants import BLOOD_GROUPS, GENDERS


class EligibilityResponse(BaseModel):
    eligible: bool
    reasons: List[str] = []
    age: int
    weight: float
    last_donation_date: Optional[date] = None
    next_eligible_date: Optional[date] = None


class DonorCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    dob: date
    gender: Literal["male", "female", "other"]
    blood_group: Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    phone: str = Field(..., min_length=3, max_length=20)
    address: str = Field(..., min_length=1)
    weight: Decimal = Field(..., gt=0, decimal_places=2)


class DonorUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    dob: Optional[date] = None
    gender: Optional[Literal["male", "female", "other"]] = None
    blood_group: Optional[Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]] = None
    phone: Optional[str] = Field(None, min_length=3, max_length=20)
    address: Optional[str] = Field(None, min_length=1)
    weight: Optional[Decimal] = Field(None, gt=0, decimal_places=2)


class DonorResponse(BaseModel):
    donor_id: int
    name: str
    dob: date
    gender: str
    blood_group: str
    phone: str
    address: str
    weight: float
    last_donation_date: Optional[date] = None
    donation_count: int = 0
    is_regular: bool = False

    model_config = {"from_attributes": True}


class DonorDetailResponse(DonorResponse):
    eligibility: EligibilityResponse


class DonorListResponse(BaseModel):
    items: List[DonorResponse]
    total: int
    page: int
    page_size: int
