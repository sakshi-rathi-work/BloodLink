from datetime import date, timedelta
import httpx
from sqlalchemy.orm import Session
from app.core import clock
from app.models.activity_log import ActivityLog
from app.models.blood_unit import BloodUnit
from app.models.donor import Donor


def create_donor(db: Session, name: str = "Test Donor", blood_group: str = "A+") -> Donor:
    donor = Donor(
        name=name,
        dob=date(1995, 1, 1),
        gender="male",
        blood_group=blood_group,
        phone="9876543210",
        address="Camp, Pune",
        weight=65.0,
    )
    db.add(donor)
    db.commit()
    db.refresh(donor)
    return donor


def test_get_stock_summary(staff_client: httpx.Client, requester_client: httpx.Client, db: Session):
    donor = create_donor(db, "Aarav", "B+")
    today = clock.today()

    # Add 2 available B+ units, 1 expired B+ unit, 1 available O- unit
    u1 = BloodUnit(donor_id=donor.donor_id, blood_group="B+", collection_date=today, expiry_date=today + timedelta(days=42), status="available")
    u2 = BloodUnit(donor_id=donor.donor_id, blood_group="B+", collection_date=today, expiry_date=today + timedelta(days=20), status="available")
    u3 = BloodUnit(donor_id=donor.donor_id, blood_group="B+", collection_date=today - timedelta(days=50), expiry_date=today - timedelta(days=8), status="expired")
    u4 = BloodUnit(donor_id=donor.donor_id, blood_group="O-", collection_date=today, expiry_date=today + timedelta(days=42), status="available")
    db.add_all([u1, u2, u3, u4])
    db.commit()

    # Requester cannot access stock
    res_req = requester_client.get("/api/inventory/stock")
    assert res_req.status_code == 403

    # Staff can access stock
    res = staff_client.get("/api/inventory/stock")
    assert res.status_code == 200
    data = res.json()
    assert data["total_available_units"] == 3
    assert len(data["stock"]) == 8

    stock_map = {item["blood_group"]: item["available_units"] for item in data["stock"]}
    assert stock_map["B+"] == 2
    assert stock_map["O-"] == 1
    assert stock_map["A+"] == 0


def test_list_inventory_units_and_filters(staff_client: httpx.Client, db: Session):
    donor = create_donor(db, "Priya", "A-")
    today = clock.today()

    u1 = BloodUnit(donor_id=donor.donor_id, blood_group="A-", collection_date=today, expiry_date=today + timedelta(days=5), status="available")
    u2 = BloodUnit(donor_id=donor.donor_id, blood_group="A-", collection_date=today, expiry_date=today + timedelta(days=30), status="available")
    db.add_all([u1, u2])
    db.commit()

    # List all units
    res = staff_client.get("/api/inventory/units")
    assert res.status_code == 200
    assert res.json()["total"] == 2

    # Filter expiring within 7 days
    res_exp = staff_client.get("/api/inventory/units?expiring_within_days=7")
    assert res_exp.status_code == 200
    assert res_exp.json()["total"] == 1
    assert res_exp.json()["items"][0]["unit_id"] == u1.unit_id
    assert res_exp.json()["items"][0]["days_to_expiry"] == 5


def test_get_expiring_units(staff_client: httpx.Client, db: Session):
    donor = create_donor(db, "Karan", "O+")
    today = clock.today()

    u1 = BloodUnit(donor_id=donor.donor_id, blood_group="O+", collection_date=today, expiry_date=today + timedelta(days=2), status="available")
    u2 = BloodUnit(donor_id=donor.donor_id, blood_group="O+", collection_date=today, expiry_date=today + timedelta(days=6), status="available")
    u3 = BloodUnit(donor_id=donor.donor_id, blood_group="O+", collection_date=today, expiry_date=today + timedelta(days=25), status="available")
    db.add_all([u1, u2, u3])
    db.commit()

    res = staff_client.get("/api/inventory/expiring?days=7")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 2
    # Nearest expiry first
    assert items[0]["unit_id"] == u1.unit_id
    assert items[1]["unit_id"] == u2.unit_id


def test_expire_overdue_units_endpoint(staff_client: httpx.Client, db: Session):
    donor = create_donor(db, "Vikas", "AB+")
    today = clock.today()

    # Create available unit whose expiry date is in the past
    u_overdue = BloodUnit(
        donor_id=donor.donor_id,
        blood_group="AB+",
        collection_date=today - timedelta(days=45),
        expiry_date=today - timedelta(days=3),
        status="available",
    )
    # Create valid available unit
    u_valid = BloodUnit(
        donor_id=donor.donor_id,
        blood_group="AB+",
        collection_date=today,
        expiry_date=today + timedelta(days=42),
        status="available",
    )
    db.add_all([u_overdue, u_valid])
    db.commit()

    res = staff_client.post("/api/inventory/expire-overdue")
    assert res.status_code == 200
    assert res.json()["expired_count"] == 1

    # Verify database state
    db.refresh(u_overdue)
    db.refresh(u_valid)
    assert u_overdue.status == "expired"
    assert u_valid.status == "available"

    # Verify activity log
    log = db.query(ActivityLog).filter(ActivityLog.action == "expire_sweep").first()
    assert log is not None
    assert log.details["expired_count"] == 1


def test_delete_blood_unit(admin_client: httpx.Client, staff_client: httpx.Client, db: Session):
    donor = create_donor(db, "Maya", "O+")
    today = clock.today()

    u_available = BloodUnit(
        donor_id=donor.donor_id,
        blood_group="O+",
        collection_date=today,
        expiry_date=today + timedelta(days=42),
        status="available",
    )
    u_issued = BloodUnit(
        donor_id=donor.donor_id,
        blood_group="O+",
        collection_date=today - timedelta(days=10),
        expiry_date=today + timedelta(days=32),
        status="issued",
    )
    db.add_all([u_available, u_issued])
    db.commit()
    db.refresh(u_available)
    db.refresh(u_issued)

    # Staff cannot delete
    res_staff = staff_client.delete(f"/api/inventory/units/{u_available.unit_id}")
    assert res_staff.status_code == 403

    # Admin cannot delete issued unit
    res_issued = admin_client.delete(f"/api/inventory/units/{u_issued.unit_id}")
    assert res_issued.status_code == 409
    assert res_issued.json()["detail"]["code"] == "UNIT_ALREADY_ISSUED"

    # Admin can delete available unit
    res_del = admin_client.delete(f"/api/inventory/units/{u_available.unit_id}")
    assert res_del.status_code == 204

    # Confirm unit is gone
    unit_check = db.query(BloodUnit).filter(BloodUnit.unit_id == u_available.unit_id).first()
    assert unit_check is None
