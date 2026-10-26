from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core import errors
from app.core.deps import get_db, require_roles
from app.models.donation_camp import DonationCamp
from app.models.user import User
from app.schemas.camp import CampCreateRequest, CampListResponse, CampResponse, CampUpdateRequest
from app.services import activity_log

router = APIRouter(prefix="/camps", tags=["Donation Camps"])


@router.post(
    "",
    response_model=CampResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a donation camp",
)
def create_camp(
    payload: CampCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff & Admin: Schedule a new blood donation camp drive."""
    camp = DonationCamp(
        location=payload.location,
        camp_date=payload.camp_date,
        target_units=payload.target_units,
        units_collected=payload.units_collected or 0,
    )
    db.add(camp)
    db.flush()

    activity_log.record(
        db,
        user_id=current_user.user_id,
        action="create",
        entity_type="donation_camp",
        entity_id=camp.camp_id,
        details={
            "location": camp.location,
            "camp_date": camp.camp_date.isoformat(),
            "target_units": camp.target_units,
            "units_collected": camp.units_collected,
        },
    )

    db.commit()
    db.refresh(camp)
    return camp


@router.get("", response_model=CampListResponse, summary="List donation camps")
def list_camps(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff & Admin: Retrieve paginated list of donation camps ordered by date descending."""
    query = db.query(DonationCamp)

    if start_date:
        query = query.filter(DonationCamp.camp_date >= start_date)
    if end_date:
        query = query.filter(DonationCamp.camp_date <= end_date)

    total = query.count()
    items = (
        query.order_by(DonationCamp.camp_date.desc(), DonationCamp.camp_id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return CampListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{camp_id}", response_model=CampResponse, summary="Get donation camp detail")
def get_camp_detail(
    camp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff & Admin: Retrieve details of a specific donation camp."""
    camp = db.query(DonationCamp).filter(DonationCamp.camp_id == camp_id).first()
    if not camp:
        raise errors.not_found(f"Donation camp with ID {camp_id} not found.")
    return camp


@router.patch("/{camp_id}", response_model=CampResponse, summary="Update donation camp")
def update_camp(
    camp_id: int,
    payload: CampUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff & Admin: Update location, date, target units, or collected units for a camp."""
    camp = db.query(DonationCamp).filter(DonationCamp.camp_id == camp_id).first()
    if not camp:
        raise errors.not_found(f"Donation camp with ID {camp_id} not found.")

    changes = {}
    if payload.location is not None:
        camp.location = payload.location
        changes["location"] = payload.location
    if payload.camp_date is not None:
        camp.camp_date = payload.camp_date
        changes["camp_date"] = payload.camp_date.isoformat()
    if payload.target_units is not None:
        camp.target_units = payload.target_units
        changes["target_units"] = payload.target_units
    if payload.units_collected is not None:
        camp.units_collected = payload.units_collected
        changes["units_collected"] = payload.units_collected

    if changes:
        activity_log.record(
            db,
            user_id=current_user.user_id,
            action="update",
            entity_type="donation_camp",
            entity_id=camp.camp_id,
            details=changes,
        )

    db.commit()
    db.refresh(camp)
    return camp


@router.delete(
    "/{camp_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete donation camp",
)
def delete_camp(
    camp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Admin-only: Delete a scheduled or past donation camp."""
    camp = db.query(DonationCamp).filter(DonationCamp.camp_id == camp_id).first()
    if not camp:
        raise errors.not_found(f"Donation camp with ID {camp_id} not found.")

    activity_log.record(
        db,
        user_id=current_user.user_id,
        action="delete",
        entity_type="donation_camp",
        entity_id=camp_id,
        details={"location": camp.location, "camp_date": camp.camp_date.isoformat()},
    )

    db.delete(camp)
    db.commit()
    return None
