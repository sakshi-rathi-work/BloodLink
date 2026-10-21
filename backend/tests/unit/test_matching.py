from datetime import date
from sqlalchemy.orm import Session
from app.models.blood_unit import BloodUnit
from app.models.donor import Donor
from app.services.matching import get_compatible_units


def test_matching_ranking_nearest_expiry_first(db: Session):
    today = date(2026, 10, 21)

    donor = Donor(
        name="Matching Donor",
        dob=date(1990, 1, 1),
        gender="male",
        blood_group="O+",
        phone="9999999999",
        address="Test Address",
        weight=65.0,
    )
    db.add(donor)
    db.commit()

    # Unit 1: A+, expires in 10 days
    u1 = BloodUnit(
        donor_id=donor.donor_id,
        blood_group="A+",
        collection_date=date(2026, 9, 20),
        expiry_date=date(2026, 11, 1),
        status="available",
    )
    # Unit 2: O-, expires in 2 days (sooner!)
    u2 = BloodUnit(
        donor_id=donor.donor_id,
        blood_group="O-",
        collection_date=date(2026, 9, 11),
        expiry_date=date(2026, 10, 23),
        status="available",
    )
    # Unit 3: A-, expires in 5 days
    u3 = BloodUnit(
        donor_id=donor.donor_id,
        blood_group="A-",
        collection_date=date(2026, 9, 14),
        expiry_date=date(2026, 10, 26),
        status="available",
    )
    # Unit 4: Already expired yesterday (should be excluded)
    u4 = BloodUnit(
        donor_id=donor.donor_id,
        blood_group="A+",
        collection_date=date(2026, 9, 8),
        expiry_date=date(2026, 10, 20),
        status="available",
    )
    # Unit 5: Issued (should be excluded)
    u5 = BloodUnit(
        donor_id=donor.donor_id,
        blood_group="O+",
        collection_date=date(2026, 9, 15),
        expiry_date=date(2026, 10, 27),
        status="issued",
    )
    # Unit 6: B+ (incompatible for A+ recipient, should be excluded)
    u6 = BloodUnit(
        donor_id=donor.donor_id,
        blood_group="B+",
        collection_date=date(2026, 9, 12),
        expiry_date=date(2026, 10, 24),
        status="available",
    )

    db.add_all([u1, u2, u3, u4, u5, u6])
    db.commit()

    # Recipient wants A+
    matches = get_compatible_units(db, requested_group="A+", today_date=today)

    # Should match u2 (O-, Oct 23), u3 (A-, Oct 26), u1 (A+, Nov 1) in that exact order
    assert len(matches) == 3
    assert matches[0].unit_id == u2.unit_id
    assert matches[1].unit_id == u3.unit_id
    assert matches[2].unit_id == u1.unit_id
