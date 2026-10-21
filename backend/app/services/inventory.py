from datetime import date
from typing import Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core import clock
from app.core.constants import BLOOD_GROUPS
from app.models.blood_unit import BloodUnit


def expire_overdue_units(db: Session, today_date: Optional[date] = None) -> int:
    """
    Find all available units where expiry_date < today and mark them as expired (wastage).
    
    Returns the count of updated units.
    """
    if today_date is None:
        today_date = clock.today()

    overdue_units = (
        db.query(BloodUnit)
        .filter(
            BloodUnit.status == "available",
            BloodUnit.expiry_date < today_date,
        )
        .all()
    )

    count = len(overdue_units)
    if count > 0:
        for unit in overdue_units:
            unit.status = "expired"
        db.commit()

    return count


def get_stock_by_blood_group(db: Session, today_date: Optional[date] = None) -> Dict[str, int]:
    """
    Count available (unexpired) blood units for each blood group.
    
    Returns a dictionary for all 8 blood groups (zero-filled).
    """
    if today_date is None:
        today_date = clock.today()

    # Query counts for status='available' and expiry_date >= today
    rows = (
        db.query(BloodUnit.blood_group, func.count(BloodUnit.unit_id))
        .filter(
            BloodUnit.status == "available",
            BloodUnit.expiry_date >= today_date,
        )
        .group_by(BloodUnit.blood_group)
        .all()
    )

    stock_map = {group: 0 for group in BLOOD_GROUPS}
    for group, count in rows:
        if group in stock_map:
            stock_map[group] = count

    return stock_map
