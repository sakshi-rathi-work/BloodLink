from datetime import date, timedelta
import httpx
from sqlalchemy.orm import Session
from app.models.blood_unit import BloodUnit
from app.models.donor import Donor


def test_create_donor_success(staff_client: httpx.Client):
    payload = {
        "name": "Rohan Sharma",
        "dob": "1998-05-15",
        "gender": "male",
        "blood_group": "B+",
        "phone": "9823456789",
        "address": "Kothrud, Pune",
        "weight": 68.5,
    }
    response = staff_client.post("/api/donors", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Rohan Sharma"
    assert data["blood_group"] == "B+"
    assert data["donation_count"] == 0
    assert data["is_regular"] is False


def test_list_donors_with_filters(staff_client: httpx.Client, db: Session):
    d1 = Donor(
        name="Aarav Patel",
        dob=date(1995, 2, 10),
        gender="male",
        blood_group="A+",
        phone="9811111111",
        address="Bandra, Mumbai",
        weight=70.0,
        last_donation_date=date(2026, 6, 1),
    )
    d2 = Donor(
        name="Sneha Kulkarni",
        dob=date(2000, 8, 20),
        gender="female",
        blood_group="O-",
        phone="9822222222",
        address="Aundh, Pune",
        weight=54.0,
        last_donation_date=date(2026, 9, 1),
    )
    db.add_all([d1, d2])
    db.commit()

    # Filter by blood_group=O-
    res = staff_client.get("/api/donors?blood_group=O-")
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["name"] == "Sneha Kulkarni"

    # Filter by location=Mumbai
    res_loc = staff_client.get("/api/donors?location=mumbai")
    assert res_loc.status_code == 200
    assert res_loc.json()["total"] == 1
    assert res_loc.json()["items"][0]["name"] == "Aarav Patel"

    # Filter by q search
    res_q = staff_client.get("/api/donors?q=Sneha")
    assert res_q.status_code == 200
    assert res_q.json()["total"] == 1


def test_get_donor_detail_and_eligibility(staff_client: httpx.Client, db: Session):
    donor = Donor(
        name="Priya Deshmukh",
        dob=date(1996, 3, 14),
        gender="female",
        blood_group="O+",
        phone="9833333333",
        address="Shivajinagar, Pune",
        weight=56.0,
        last_donation_date=None,
    )
    db.add(donor)
    db.commit()

    res = staff_client.get(f"/api/donors/{donor.donor_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Priya Deshmukh"
    assert data["eligibility"]["eligible"] is True
    assert data["eligibility"]["reasons"] == []


def test_record_donation_success(staff_client: httpx.Client, db: Session, freeze_clock):
    today = date(2026, 10, 21)
    freeze_clock(today)

    donor = Donor(
        name="Eligible Donor",
        dob=date(1994, 6, 10),
        gender="male",
        blood_group="AB+",
        phone="9844444444",
        address="Camp, Pune",
        weight=72.0,
        last_donation_date=date(2026, 6, 1),  # > 90 days ago
    )
    db.add(donor)
    db.commit()

    res = staff_client.post(f"/api/donors/{donor.donor_id}/donations")
    assert res.status_code == 201
    unit_data = res.json()
    assert unit_data["blood_group"] == "AB+"
    assert unit_data["collection_date"] == "2026-10-21"
    assert unit_data["expiry_date"] == "2026-12-02"  # 2026-10-21 + 42 days
    assert unit_data["status"] == "available"
    assert unit_data["days_to_expiry"] == 42

    # Verify donor.last_donation_date updated
    db.refresh(donor)
    assert donor.last_donation_date == today


def test_record_donation_ineligible_atomic(staff_client: httpx.Client, db: Session, freeze_clock):
    today = date(2026, 10, 21)
    freeze_clock(today)

    # Donor donated only 10 days ago (ineligible!)
    donor = Donor(
        name="Recent Donor",
        dob=date(1995, 1, 1),
        gender="male",
        blood_group="A-",
        phone="9855555555",
        address="Deccan, Pune",
        weight=65.0,
        last_donation_date=date(2026, 10, 11),
    )
    db.add(donor)
    db.commit()

    res = staff_client.post(f"/api/donors/{donor.donor_id}/donations")
    assert res.status_code == 409
    data = res.json()
    assert data["detail"]["code"] == "ELIGIBILITY_FAILED"
    assert "DONATION_GAP_NOT_MET" in data["detail"]["reasons"]

    # Verify no blood_units were created (atomic!)
    unit_count = db.query(BloodUnit).filter(BloodUnit.donor_id == donor.donor_id).count()
    assert unit_count == 0


def test_patch_donor_blood_group_guard(staff_client: httpx.Client, db: Session):
    donor = Donor(
        name="Donor With Unit",
        dob=date(1992, 4, 1),
        gender="male",
        blood_group="O+",
        phone="9866666666",
        address="Hadapsar, Pune",
        weight=66.0,
    )
    db.add(donor)
    db.commit()

    unit = BloodUnit(
        donor_id=donor.donor_id,
        blood_group="O+",
        collection_date=date(2026, 10, 1),
        expiry_date=date(2026, 11, 12),
        status="available",
    )
    db.add(unit)
    db.commit()

    # Attempt to change blood group to A+ -> should fail with 409 DONOR_HAS_UNITS
    res = staff_client.patch(f"/api/donors/{donor.donor_id}", json={"blood_group": "A+"})
    assert res.status_code == 409
    assert res.json()["detail"]["code"] == "DONOR_HAS_UNITS"


def test_delete_donor_guards(admin_client: httpx.Client, staff_client: httpx.Client, db: Session):
    donor = Donor(
        name="Donor To Delete",
        dob=date(1990, 7, 7),
        gender="female",
        blood_group="B-",
        phone="9877777777",
        address="Baner, Pune",
        weight=58.0,
    )
    db.add(donor)
    db.commit()

    # Staff forbidden
    res_staff = staff_client.delete(f"/api/donors/{donor.donor_id}")
    assert res_staff.status_code == 403

    # Add unit to test REFERENCED_RECORD guard
    unit = BloodUnit(
        donor_id=donor.donor_id,
        blood_group="B-",
        collection_date=date(2026, 10, 1),
        expiry_date=date(2026, 11, 12),
        status="available",
    )
    db.add(unit)
    db.commit()

    res_blocked = admin_client.delete(f"/api/donors/{donor.donor_id}")
    assert res_blocked.status_code == 409
    assert res_blocked.json()["detail"]["code"] == "REFERENCED_RECORD"


def test_donor_endpoints_forbidden_for_requester(requester_client: httpx.Client):
    res = requester_client.get("/api/donors")
    assert res.status_code == 403
    assert res.json()["detail"]["code"] == "FORBIDDEN"
