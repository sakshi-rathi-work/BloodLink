from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.inventory import to_unit_response
from app.core import errors
from app.core.constants import BLOOD_GROUPS
from app.core.deps import get_current_user, get_db, require_roles
from app.models.user import User
from app.schemas.inventory import BloodUnitResponse
from app.schemas.matching import CompatibilityMatrixResponse
from app.services.compatibility import COMPATIBILITY
from app.services.matching import get_compatible_units

router = APIRouter(prefix="/matching", tags=["matching"])


@router.get(
    "/compatibility",
    response_model=CompatibilityMatrixResponse,
    summary="Get blood group compatibility matrix",
)
def get_compatibility_matrix(
    current_user: User = Depends(get_current_user),
):
    """Authenticated users (Admin, Staff, Requester): View full canonical compatibility matrix."""
    return CompatibilityMatrixResponse(matrix=COMPATIBILITY)


@router.get(
    "/units",
    response_model=List[BloodUnitResponse],
    summary="Find available compatible units for a blood group",
)
def find_matching_units(
    blood_group: str = Query(..., description="Target recipient blood group"),
    limit: Optional[int] = Query(50, ge=1, le=500, description="Max units to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    # URL decoding might turn '+' into ' ', normalize it
    normalized_group = blood_group.replace(" ", "+").strip()
    if normalized_group not in BLOOD_GROUPS:
        raise errors.AppException(
            status_code=400,
            code="INVALID_BLOOD_GROUP",
            message=f"Invalid blood group '{blood_group}'. Must be one of: {', '.join(BLOOD_GROUPS)}",
        )

    units = get_compatible_units(db, requested_group=normalized_group, limit=limit)
    return [to_unit_response(u) for u in units]
