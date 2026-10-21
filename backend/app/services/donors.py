from datetime import date, timedelta
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core import clock, errors
from app.core.config import settings
from app.models.blood_unit import BloodUnit
from app.models.donor import Donor
from app.services import activity_log
from app.services.eligibility import check_donor_eligibility


def get_donor_donation_count(db: Session, donor_id: int) -> int:
    """Count total units donated by this donor."""
    return db.query(func.count(BloodUnit.unit_id)).filter(BloodUnit.donor_id == donor_id).scalar() or 0


def is_donor_regular(db: Session, donor_id: int) -> bool:
    """Check if donor has reached REGULAR_DONOR_MIN_DONATIONS (default >= 3)."""
    count = get_donor_donation_count(db, donor_id)
    return count >= settings.REGULAR_DONOR_MIN_DONATIONS


def record_donation(
    db: Session,
    donor_id: int,
    user_id: int,
    today_date: Optional[date] = None,
) -> BloodUnit:
    """
    Atomically record a blood donation from an eligible donor (Section 6.4).
    
    1. Check eligibility against current date. Fails with 409 ELIGIBILITY_FAILED if not eligible.
    2. Insert blood_units row (collection_date=today, expiry_date=today + 42d, status='available').
    3. Update donor.last_donation_date = today.
    4. Write activity log.
    """
    if today_date is None:
        today_date = clock.today()

    donor = db.query(Donor).filter(Donor.donor_id == donor_id).first()
    if not donor:
        raise errors.not_found(f"Donor with ID {donor_id} not found.")

    eligibility = check_donor_eligibility(
        dob=donor.dob,
        weight=float(donor.weight),
        last_donation_date=donor.last_donation_date,
        current_date=today_date,
    )

    if not eligibility["eligible"]:
        raise errors.eligibility_failed(
            reasons=eligibility["reasons"],
            message=f"Donor is not currently eligible to donate: {', '.join(eligibility['reasons'])}.",
        )

    expiry_date = today_date + timedelta(days=settings.BLOOD_SHELF_LIFE_DAYS)

    unit = BloodUnit(
        donor_id=donor.donor_id,
        blood_group=donor.blood_group,
        collection_date=today_date,
        expiry_date=expiry_date,
        status="available",
    )
    db.add(unit)
    db.flush()  # Populates unit.unit_id

    donor.last_donation_date = today_date

    activity_log.record(
        db,
        user_id=user_id,
        action="create",
        entity_type="blood_unit",
        entity_id=unit.unit_id,
        details={
            "donor_id": donor.donor_id,
            "donor_name": donor.name,
            "blood_group": unit.blood_group,
            "collection_date": str(unit.collection_date),
            "expiry_date": str(unit.expiry_date),
        },
    )

    db.commit()
    db.refresh(unit)
    return unit
