from datetime import timedelta
import pytest
from sqlalchemy.orm import Session
from app.core import clock, errors
from app.models.blood_request import BloodRequest
from app.models.blood_unit import BloodUnit
from app.models.donor import Donor
from app.models.issue_record import IssueRecord
from app.models.requester import Requester
from app.models.staff import Staff
from app.models.user import User
from app.services.issuing import approve_request, issue_request, reject_request


@pytest.fixture
def test_data(db: Session, admin_user: User, requester_user: User):
    """Fixture providing basic donor, units, and request."""
    today = clock.today()

    donor = Donor(
        name="John Donor",
        dob=today - timedelta(days=30 * 365),
        gender="male",
        blood_group="A+",
        phone="9876543210",
        address="Dadar, Mumbai",
        weight=65.0,
        last_donation_date=today - timedelta(days=100),
    )
    db.add(donor)
    db.flush()

    # Unit 1: A+, expires in 5 days
    unit1 = BloodUnit(
        donor_id=donor.donor_id,
        blood_group="A+",
        collection_date=today - timedelta(days=10),
        expiry_date=today + timedelta(days=5),
        status="available",
    )
    # Unit 2: O+, expires in 2 days (compatible with A+, should be allocated first)
    unit2 = BloodUnit(
        donor_id=donor.donor_id,
        blood_group="O+",
        collection_date=today - timedelta(days=15),
        expiry_date=today + timedelta(days=2),
        status="available",
    )
    # Unit 3: Overdue unit, expired yesterday
    unit3 = BloodUnit(
        donor_id=donor.donor_id,
        blood_group="A+",
        collection_date=today - timedelta(days=45),
        expiry_date=today - timedelta(days=1),
        status="available",
    )
    db.add_all([unit1, unit2, unit3])

    request = BloodRequest(
        requester_id=requester_user.requester_profile.requester_id,
        blood_group="A+",
        quantity=2,
        urgency="emergency",
        status="pending",
        request_date=today,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    db.refresh(unit1)
    db.refresh(unit2)
    db.refresh(unit3)

    return {
        "donor": donor,
        "unit1": unit1,
        "unit2": unit2,
        "unit3": unit3,
        "request": request,
        "admin_user": admin_user,
    }


def test_transition_matrix(db: Session, test_data: dict):
    """Verify all legal and illegal state transitions per Section 4.3 & 6.7."""
    admin_user = test_data["admin_user"]
    req: BloodRequest = test_data["request"]

    # 1. pending -> cannot issue directly
    with pytest.raises(errors.AppException) as exc_info:
        issue_request(db, req.request_id, admin_user)
    assert exc_info.value.code == "INVALID_STATUS_TRANSITION"

    # 2. pending -> approved (legal)
    req = approve_request(db, req.request_id, admin_user)
    assert req.status == "approved"

    # 3. approved -> approved (illegal)
    with pytest.raises(errors.AppException) as exc_info:
        approve_request(db, req.request_id, admin_user)
    assert exc_info.value.code == "INVALID_STATUS_TRANSITION"

    # 4. approved -> rejected (legal)
    req = reject_request(db, req.request_id, admin_user)
    assert req.status == "rejected"

    # 5. rejected is terminal: cannot approve, reject, or issue
    with pytest.raises(errors.AppException) as exc_info:
        approve_request(db, req.request_id, admin_user)
    assert exc_info.value.code == "INVALID_STATUS_TRANSITION"

    with pytest.raises(errors.AppException) as exc_info:
        reject_request(db, req.request_id, admin_user)
    assert exc_info.value.code == "INVALID_STATUS_TRANSITION"

    with pytest.raises(errors.AppException) as exc_info:
        issue_request(db, req.request_id, admin_user)
    assert exc_info.value.code == "INVALID_STATUS_TRANSITION"


def test_atomic_issue_success_and_sweep(db: Session, test_data: dict):
    """Issuing an approved request triggers expiry sweep, allocates nearest-expiry-first, and links records."""
    admin_user = test_data["admin_user"]
    req: BloodRequest = test_data["request"]
    unit1: BloodUnit = test_data["unit1"]
    unit2: BloodUnit = test_data["unit2"]
    unit3: BloodUnit = test_data["unit3"]

    # Approve request first
    approve_request(db, req.request_id, admin_user)

    # Issue request (needs 2 units of A+; unit2 O+ expires in 2 days, unit1 A+ expires in 5 days)
    req = issue_request(db, req.request_id, admin_user)
    assert req.status == "issued"

    # Verify unit3 was swept to expired
    db.refresh(unit3)
    assert unit3.status == "expired"

    # Verify unit1 and unit2 are issued
    db.refresh(unit1)
    db.refresh(unit2)
    assert unit1.status == "issued"
    assert unit2.status == "issued"

    # Verify issue records
    records = db.query(IssueRecord).filter(IssueRecord.request_id == req.request_id).order_by(IssueRecord.issue_id.asc()).all()
    assert len(records) == 2
    # Nearest expiry first: unit2 (expiry in 2 days) allocated before unit1 (expiry in 5 days)
    assert records[0].unit_id == unit2.unit_id
    assert records[1].unit_id == unit1.unit_id
    assert records[0].issued_by == admin_user.staff_profile.staff_id


def test_insufficient_stock_rollback(db: Session, test_data: dict):
    """When stock is insufficient, 409 INSUFFICIENT_STOCK is raised and DB state is unchanged."""
    admin_user = test_data["admin_user"]
    req: BloodRequest = test_data["request"]
    unit1: BloodUnit = test_data["unit1"]
    unit2: BloodUnit = test_data["unit2"]

    # Request requires 2 units. Make 1 unit unavailable.
    unit1.status = "issued"
    db.commit()

    approve_request(db, req.request_id, admin_user)

    # Attempt to issue 2 units with only 1 compatible unit available
    with pytest.raises(errors.AppException) as exc_info:
        issue_request(db, req.request_id, admin_user)

    err = exc_info.value
    assert err.code == "INSUFFICIENT_STOCK"
    assert err.extra["requested"] == 2
    assert err.extra["available"] == 1

    # Verify request is still approved, unit2 is still available, and no issue records exist
    db.refresh(req)
    db.refresh(unit2)
    assert req.status == "approved"
    assert unit2.status == "available"
    assert db.query(IssueRecord).filter(IssueRecord.request_id == req.request_id).count() == 0


def test_missing_staff_profile_raises(db: Session, requester_user: User, test_data: dict):
    """Issuing with a user that has no staff profile raises 400 STAFF_PROFILE_REQUIRED."""
    req: BloodRequest = test_data["request"]
    req.status = "approved"
    db.commit()

    with pytest.raises(errors.AppException) as exc_info:
        issue_request(db, req.request_id, requester_user)

    assert exc_info.value.code == "STAFF_PROFILE_REQUIRED"
