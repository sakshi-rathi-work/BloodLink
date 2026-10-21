from datetime import date
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from app.core import clock, errors
from app.core.config import settings
from app.core.deps import get_db, require_roles
from app.models.blood_unit import BloodUnit
from app.models.donor import Donor
from app.models.user import User
from app.schemas.donor import (
    DonorCreateRequest,
    DonorDetailResponse,
    DonorListResponse,
    DonorResponse,
    DonorUpdateRequest,
    EligibilityResponse,
)
from app.services import activity_log, donors as donor_service
from app.services.eligibility import check_donor_eligibility

router = APIRouter(prefix="/donors", tags=["Donors"])


def to_donor_response(donor: Donor, db: Session) -> DonorResponse:
    count = donor_service.get_donor_donation_count(db, donor.donor_id)
    is_regular = count >= settings.REGULAR_DONOR_MIN_DONATIONS
    return DonorResponse(
        donor_id=donor.donor_id,
        name=donor.name,
        dob=donor.dob,
        gender=donor.gender,
        blood_group=donor.blood_group,
        phone=donor.phone,
        address=donor.address,
        weight=float(donor.weight),
        last_donation_date=donor.last_donation_date,
        donation_count=count,
        is_regular=is_regular,
    )


@router.post(
    "",
    response_model=DonorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new blood donor",
)
def create_donor(
    payload: DonorCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff/Admin: Register a new donor in the system."""
    donor = Donor(
        name=payload.name,
        dob=payload.dob,
        gender=payload.gender,
        blood_group=payload.blood_group,
        phone=payload.phone,
        address=payload.address,
        weight=payload.weight,
        last_donation_date=None,
    )
    db.add(donor)
    db.flush()

    activity_log.record(
        db,
        user_id=current_user.user_id,
        action="create",
        entity_type="donor",
        entity_id=donor.donor_id,
        details={
            "name": donor.name,
            "blood_group": donor.blood_group,
            "dob": str(donor.dob),
            "phone": donor.phone,
        },
    )

    db.commit()
    db.refresh(donor)
    return to_donor_response(donor, db)


@router.get("", response_model=DonorListResponse, summary="List donors with filters")
def list_donors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    blood_group: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    last_donation_before: Optional[date] = Query(None),
    last_donation_after: Optional[date] = Query(None),
    is_regular: Optional[bool] = Query(None),
    q: Optional[str] = Query(None),
    sort: Optional[str] = Query("name", pattern="^(name|last_donation_date)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff/Admin: Retrieve paginated donors with flexible filters."""
    query = db.query(Donor)

    if blood_group:
        normalized_group = blood_group.replace(" ", "+").strip()
        query = query.filter(Donor.blood_group == normalized_group)
    if location:
        query = query.filter(Donor.address.ilike(f"%{location}%"))
    if last_donation_before:
        query = query.filter(Donor.last_donation_date <= last_donation_before)
    if last_donation_after:
        query = query.filter(Donor.last_donation_date >= last_donation_after)
    if q:
        query = query.filter(
            or_(Donor.name.ilike(f"%{q}%"), Donor.phone.ilike(f"%{q}%"))
        )

    # Filter by regular donors using correlated subquery count of blood_units
    if is_regular is not None:
        unit_count_subquery = (
            db.query(func.count(BloodUnit.unit_id))
            .filter(BloodUnit.donor_id == Donor.donor_id)
            .correlate(Donor)
            .as_scalar()
        )
        if is_regular:
            query = query.filter(unit_count_subquery >= settings.REGULAR_DONOR_MIN_DONATIONS)
        else:
            query = query.filter(unit_count_subquery < settings.REGULAR_DONOR_MIN_DONATIONS)

    # Sorting
    if sort == "last_donation_date":
        query = query.order_by(Donor.last_donation_date.desc().nullslast(), Donor.name.asc())
    else:
        query = query.order_by(Donor.name.asc(), Donor.donor_id.asc())

    total = query.count()
    donors = query.offset((page - 1) * page_size).limit(page_size).all()

    return DonorListResponse(
        items=[to_donor_response(d, db) for d in donors],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{donor_id}", response_model=DonorDetailResponse, summary="Get donor details and eligibility")
def get_donor(
    donor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff/Admin: Get single donor details, donation metrics, and eligibility status."""
    donor = db.query(Donor).filter(Donor.donor_id == donor_id).first()
    if not donor:
        raise errors.not_found(f"Donor with ID {donor_id} not found.")

    base_resp = to_donor_response(donor, db)
    eligibility_info = check_donor_eligibility(
        dob=donor.dob,
        weight=float(donor.weight),
        last_donation_date=donor.last_donation_date,
    )

    return DonorDetailResponse(
        **base_resp.model_dump(),
        eligibility=EligibilityResponse(**eligibility_info),
    )


@router.patch("/{donor_id}", response_model=DonorResponse, summary="Update donor details")
def update_donor(
    donor_id: int,
    payload: DonorUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff/Admin: Update donor profile. Guarded against changing blood_group if units exist."""
    donor = db.query(Donor).filter(Donor.donor_id == donor_id).first()
    if not donor:
        raise errors.not_found(f"Donor with ID {donor_id} not found.")

    # Guard: blood_group cannot be changed once donor has units (Section 6.10)
    if payload.blood_group is not None and payload.blood_group != donor.blood_group:
        unit_count = db.query(BloodUnit).filter(BloodUnit.donor_id == donor_id).count()
        if unit_count > 0:
            raise errors.donor_has_units("Blood group cannot be changed once donations have been recorded.")
        donor.blood_group = payload.blood_group

    changes: Dict[str, Any] = {}
    if payload.name is not None:
        donor.name = payload.name
        changes["name"] = payload.name
    if payload.dob is not None:
        donor.dob = payload.dob
        changes["dob"] = str(payload.dob)
    if payload.gender is not None:
        donor.gender = payload.gender
        changes["gender"] = payload.gender
    if payload.phone is not None:
        donor.phone = payload.phone
        changes["phone"] = payload.phone
    if payload.address is not None:
        donor.address = payload.address
        changes["address"] = payload.address
    if payload.weight is not None:
        donor.weight = payload.weight
        changes["weight"] = float(payload.weight)

    if changes or payload.blood_group is not None:
        activity_log.record(
            db,
            user_id=current_user.user_id,
            action="update",
            entity_type="donor",
            entity_id=donor.donor_id,
            details=changes,
        )

    db.commit()
    db.refresh(donor)
    return to_donor_response(donor, db)


@router.delete("/{donor_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete donor")
def delete_donor(
    donor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Admin-only: Delete donor profile if no units are attached."""
    donor = db.query(Donor).filter(Donor.donor_id == donor_id).first()
    if not donor:
        raise errors.not_found(f"Donor with ID {donor_id} not found.")

    unit_count = db.query(BloodUnit).filter(BloodUnit.donor_id == donor_id).count()
    if unit_count > 0:
        raise errors.referenced_record(
            f"Cannot delete donor #{donor_id} because {unit_count} blood donation record(s) exist."
        )

    activity_log.record(
        db,
        user_id=current_user.user_id,
        action="delete",
        entity_type="donor",
        entity_id=donor_id,
        details={"name": donor.name, "blood_group": donor.blood_group},
    )

    db.delete(donor)
    db.commit()
    return None


@router.get("/{donor_id}/eligibility", response_model=EligibilityResponse, summary="Check donor eligibility")
def get_donor_eligibility(
    donor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff/Admin: Evaluate and return donor eligibility status."""
    donor = db.query(Donor).filter(Donor.donor_id == donor_id).first()
    if not donor:
        raise errors.not_found(f"Donor with ID {donor_id} not found.")

    res = check_donor_eligibility(
        dob=donor.dob,
        weight=float(donor.weight),
        last_donation_date=donor.last_donation_date,
    )
    return EligibilityResponse(**res)


@router.post(
    "/{donor_id}/donations",
    status_code=status.HTTP_201_CREATED,
    summary="Record a blood donation",
)
def record_donation(
    donor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """
    Staff/Admin: Atomically record a donation (Section 6.4).
    Validates eligibility, creates blood unit with 42-day expiry, and updates last donation date.
    """
    unit = donor_service.record_donation(
        db=db,
        donor_id=donor_id,
        user_id=current_user.user_id,
    )
    today_date = clock.today()
    days_to_expiry = (unit.expiry_date - today_date).days

    return {
        "unit_id": unit.unit_id,
        "donor_id": unit.donor_id,
        "blood_group": unit.blood_group,
        "collection_date": str(unit.collection_date),
        "expiry_date": str(unit.expiry_date),
        "status": unit.status,
        "days_to_expiry": days_to_expiry,
    }


@router.get(
    "/{donor_id}/donations",
    summary="Get donor's donation history",
)
def get_donor_donations(
    donor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff/Admin: List all blood units collected from this donor, newest first."""
    donor = db.query(Donor).filter(Donor.donor_id == donor_id).first()
    if not donor:
        raise errors.not_found(f"Donor with ID {donor_id} not found.")

    units = (
        db.query(BloodUnit)
        .filter(BloodUnit.donor_id == donor_id)
        .order_by(BloodUnit.collection_date.desc(), BloodUnit.unit_id.desc())
        .all()
    )

    today_date = clock.today()
    return [
        {
            "unit_id": u.unit_id,
            "donor_id": u.donor_id,
            "blood_group": u.blood_group,
            "collection_date": str(u.collection_date),
            "expiry_date": str(u.expiry_date),
            "status": u.status,
            "days_to_expiry": (u.expiry_date - today_date).days,
        }
        for u in units
    ]
