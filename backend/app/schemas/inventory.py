from datetime import date
from typing import List, Optional
from pydantic import BaseModel


class BloodUnitResponse(BaseModel):
    unit_id: int
    donor_id: int
    blood_group: str
    collection_date: date
    expiry_date: date
    status: str
    days_to_expiry: int
    donor_name: Optional[str] = None

    model_config = {"from_attributes": True}


class BloodUnitListResponse(BaseModel):
    items: List[BloodUnitResponse]
    total: int
    page: int
    page_size: int


class StockByGroup(BaseModel):
    blood_group: str
    available_units: int


class StockSummaryResponse(BaseModel):
    as_of: date
    stock: List[StockByGroup]
    total_available_units: int


class ExpireOverdueResponse(BaseModel):
    expired_count: int
