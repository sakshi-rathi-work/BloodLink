from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session, joinedload
from app.core import clock, errors
from app.core.constants import BLOOD_GROUPS
from app.core.deps import get_db, require_roles
from app.models.blood_unit import BloodUnit
from app.models.user import User
from app.schemas.inventory import (
    BloodUnitListResponse,
    BloodUnitResponse,
    ExpireOverdueResponse,
    StockByGroup,
    StockSummaryResponse,
)
from app.services import activity_log
from app.services.inventory import expire_overdue_units, get_stock_by_blood_group

router = APIRouter(prefix="/inventory", tags=["inventory"])


def to_unit_response(unit: BloodUnit, today_date: Optional[date] = None) -> BloodUnitResponse:
    if today_date is None:
        today_date = clock.today()
    days_to_expiry = (unit.expiry_date - today_date).days
    return BloodUnitResponse(
        unit_id=unit.unit_id,
        donor_id=unit.donor_id,
        blood_group=unit.blood_group,
        collection_date=unit.collection_date,
        expiry_date=unit.expiry_date,
        status=unit.status,
        days_to_expiry=days_to_expiry,
        donor_name=unit.donor.name if unit.donor else None,
    )


@router.get("/stock", response_model=StockSummaryResponse, summary="Get current blood stock summary")
def get_stock(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff/Admin: Aggregated count of available unexpired units per blood group (all 8 zero-filled)."""
    today_date = clock.today()
    stock_dict = get_stock_by_blood_group(db, today_date=today_date)
    stock_list = [
        StockByGroup(blood_group=bg, available_units=stock_dict.get(bg, 0))
        for bg in BLOOD_GROUPS
    ]
    total = sum(stock_dict.values())
    return StockSummaryResponse(
        as_of=today_date,
        stock=stock_list,
        total_available_units=total,
    )


@router.get("/expiring", response_model=List[BloodUnitResponse], summary="Get units expiring soon")
def get_expiring_units(
    days: int = Query(7, ge=1, le=42, description="Days threshold to check for upcoming expiration"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff/Admin: List available units expiring within specified days, ordered nearest-expiry first."""
    today_date = clock.today()
    threshold_date = today_date + timedelta(days=days)

    units = (
        db.query(BloodUnit)
        .options(joinedload(BloodUnit.donor))
        .filter(
            BloodUnit.status == "available",
            BloodUnit.expiry_date >= today_date,
            BloodUnit.expiry_date <= threshold_date,
        )
        .order_by(BloodUnit.expiry_date.asc(), BloodUnit.unit_id.asc())
        .all()
    )

    return [to_unit_response(u, today_date) for u in units]


@router.get("/units", response_model=BloodUnitListResponse, summary="List inventory units")
def list_units(
    blood_group: Optional[str] = Query(None, description="Filter by blood group"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by unit status"),
    donor_id: Optional[int] = Query(None, description="Filter by donor ID"),
    expiring_within_days: Optional[int] = Query(None, ge=1, description="Expiring within days"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff/Admin: List blood units with pagination and filters."""
    today_date = clock.today()
    query = db.query(BloodUnit).options(joinedload(BloodUnit.donor))

    if blood_group:
        normalized_group = blood_group.replace(" ", "+").strip()
        query = query.filter(BloodUnit.blood_group == normalized_group)
    if status_filter:
        query = query.filter(BloodUnit.status == status_filter)
    if donor_id is not None:
        query = query.filter(BloodUnit.donor_id == donor_id)
    if expiring_within_days is not None:
        cutoff = today_date + timedelta(days=expiring_within_days)
        query = query.filter(
            BloodUnit.status == "available",
            BloodUnit.expiry_date >= today_date,
            BloodUnit.expiry_date <= cutoff,
        )

    query = query.order_by(BloodUnit.expiry_date.asc(), BloodUnit.unit_id.asc())

    total = query.count()
    units = query.offset((page - 1) * page_size).limit(page_size).all()

    return BloodUnitListResponse(
        items=[to_unit_response(u, today_date) for u in units],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/units/{unit_id}", response_model=BloodUnitResponse, summary="Get single blood unit details")
def get_unit(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff/Admin: Get blood unit details."""
    unit = (
        db.query(BloodUnit)
        .options(joinedload(BloodUnit.donor))
        .filter(BloodUnit.unit_id == unit_id)
        .first()
    )
    if not unit:
        raise errors.not_found(f"Blood unit #{unit_id} not found.")

    return to_unit_response(unit)


@router.post("/expire-overdue", response_model=ExpireOverdueResponse, summary="Trigger manual expiry sweep")
def run_expiry_sweep(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff/Admin: Manually sweep inventory and mark all overdue available units as expired."""
    count = expire_overdue_units(db)

    if count > 0:
        activity_log.record(
            db,
            user_id=current_user.user_id,
            action="expire_sweep",
            entity_type="inventory",
            entity_id=None,
            details={"expired_count": count},
        )
        db.commit()

    return ExpireOverdueResponse(expired_count=count)


@router.delete("/units/{unit_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete blood unit")
def delete_unit(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Admin-only: Delete blood unit. Cannot delete issued units or referenced units."""
    unit = db.query(BloodUnit).filter(BloodUnit.unit_id == unit_id).first()
    if not unit:
        raise errors.not_found(f"Blood unit #{unit_id} not found.")

    if unit.status == "issued":
        raise errors.unit_already_issued()

    if unit.issue_record is not None:
        raise errors.referenced_record("Unit is referenced by an issue record and cannot be deleted.")

    blood_group = unit.blood_group
    donor_id = unit.donor_id

    activity_log.record(
        db,
        user_id=current_user.user_id,
        action="delete",
        entity_type="blood_unit",
        entity_id=unit_id,
        details={"blood_group": blood_group, "donor_id": donor_id},
    )

    db.delete(unit)
    db.commit()
    return None
