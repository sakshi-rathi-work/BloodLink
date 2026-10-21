from typing import Dict, List
from pydantic import BaseModel
from app.schemas.inventory import BloodUnitResponse


class CompatibilityMatrixResponse(BaseModel):
    matrix: Dict[str, List[str]]
