from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core import clock
from app.models.blood_unit import BloodUnit
from app.services.compatibility import get_compatible_donor_groups


def get_compatible_units(
    db: Session,
    requested_group: str,
    limit: Optional[int] = None,
    today_date: Optional[date] = None,
    for_update: bool = False,
) -> List[BloodUnit]:
    """
    Query available, usable blood units compatible with the requested blood group.
    
    Ordered strictly by expiry_date ASC, unit_id ASC (nearest-expiry-first).
    Only includes units where status='available' and expiry_date >= today.
    """
    if today_date is None:
        today_date = clock.today()

    compatible_groups = get_compatible_donor_groups(requested_group)

    query = (
        db.query(BloodUnit)
        .filter(
            BloodUnit.status == "available",
            BloodUnit.expiry_date >= today_date,
            BloodUnit.blood_group.in_(compatible_groups),
        )
        .order_by(BloodUnit.expiry_date.asc(), BloodUnit.unit_id.asc())
    )

    if for_update:
        # Use row-level locking for atomic issuing
        query = query.with_for_update()

    if limit is not None:
        query = query.limit(limit)

    return query.all()
