from datetime import date
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, StrictInt


class RequestCreate(BaseModel):
    blood_group: Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    quantity: StrictInt = Field(..., ge=1)
    urgency: Literal["emergency", "routine"]


class IssuedUnitResponse(BaseModel):
    issue_id: int
    unit_id: int
    blood_group: str
    issue_date: date
    issued_by: int
    issued_by_name: str

    model_config = {"from_attributes": True}


class RequestResponse(BaseModel):
    request_id: int
    requester_id: int
    requester_name: str
    blood_group: str
    quantity: int
    urgency: str
    status: str
    request_date: date
    issued_count: int

    model_config = {"from_attributes": True}


class RequestDetailResponse(RequestResponse):
    issued_units: List[IssuedUnitResponse] = Field(default_factory=list)


class RequestListResponse(BaseModel):
    items: List[RequestResponse]
    total: int
    page: int
    page_size: int


class CandidateUnitResponse(BaseModel):
    unit_id: int
    blood_group: str
    collection_date: date
    expiry_date: date
    days_to_expiry: int

    model_config = {"from_attributes": True}


class RequestMatchesResponse(BaseModel):
    request_id: int
    requested_group: str
    quantity: int
    compatible_groups: List[str]
    available_compatible_count: int
    sufficient: bool
    allocation_preview_unit_ids: List[int]
    units: List[CandidateUnitResponse]
