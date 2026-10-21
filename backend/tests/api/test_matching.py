from datetime import date, timedelta
import httpx
from sqlalchemy.orm import Session
from app.core import clock
from app.models.blood_unit import BloodUnit
from app.models.donor import Donor


def test_get_compatibility_matrix(staff_client: httpx.Client, requester_client: httpx.Client):
    # Both staff and requester can access compatibility matrix
    res_staff = staff_client.get("/api/matching/compatibility")
    assert res_staff.status_code == 200
    matrix = res_staff.json()["matrix"]

    assert "AB+" in matrix
    assert len(matrix["AB+"]) == 8  # Universal recipient
    assert matrix["O-"] == ["O-"]  # Can only receive O-

    res_req = requester_client.get("/api/matching/compatibility")
    assert res_req.status_code == 200


def test_find_matching_units(staff_client: httpx.Client, requester_client: httpx.Client, db: Session):
    donor = Donor(
        name="Compatibility Donor",
        dob=date(1996, 3, 15),
        gender="female",
        blood_group="O-",
        phone="9988776655",
        address="Shivajinagar, Pune",
        weight=58.0,
    )
    db.add(donor)
    db.commit()
    db.refresh(donor)

    today = clock.today()

    # Create various units
    u_o_neg_soon = BloodUnit(donor_id=donor.donor_id, blood_group="O-", collection_date=today, expiry_date=today + timedelta(days=10), status="available")
    u_o_neg_later = BloodUnit(donor_id=donor.donor_id, blood_group="O-", collection_date=today, expiry_date=today + timedelta(days=35), status="available")
    u_b_pos = BloodUnit(donor_id=donor.donor_id, blood_group="B+", collection_date=today, expiry_date=today + timedelta(days=20), status="available")
    u_ab_pos = BloodUnit(donor_id=donor.donor_id, blood_group="AB+", collection_date=today, expiry_date=today + timedelta(days=15), status="available")
    u_expired_o_neg = BloodUnit(donor_id=donor.donor_id, blood_group="O-", collection_date=today - timedelta(days=50), expiry_date=today - timedelta(days=5), status="expired")

    db.add_all([u_o_neg_soon, u_o_neg_later, u_b_pos, u_ab_pos, u_expired_o_neg])
    db.commit()

    # Requester cannot call /api/matching/units
    res_req = requester_client.get("/api/matching/units?blood_group=B+")
    assert res_req.status_code == 403

    # Invalid blood group returns 400
    res_invalid = staff_client.get("/api/matching/units?blood_group=XYZ")
    assert res_invalid.status_code == 400
    assert res_invalid.json()["detail"]["code"] == "INVALID_BLOOD_GROUP"

    # Query compatible for B+ (can receive B+, B-, O+, O-)
    # In our DB: u_o_neg_soon (10 days), u_b_pos (20 days), u_o_neg_later (35 days)
    # AB+ and expired unit must NOT be included
    res = staff_client.get("/api/matching/units?blood_group=B+")
    assert res.status_code == 200
    units = res.json()
    assert len(units) == 3
    # Check nearest expiry first order
    assert units[0]["unit_id"] == u_o_neg_soon.unit_id
    assert units[1]["unit_id"] == u_b_pos.unit_id
    assert units[2]["unit_id"] == u_o_neg_later.unit_id
