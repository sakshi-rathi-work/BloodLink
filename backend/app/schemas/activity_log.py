from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ActivityLogResponse(BaseModel):
    log_id: int
    user_id: int
    username: str
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ActivityLogListResponse(BaseModel):
    items: List[ActivityLogResponse]
    total: int
    page: int
    page_size: int
