from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core import clock
from app.core.security import hash_password
from app.models.blood_request import BloodRequest
from app.models.blood_unit import BloodUnit
from app.models.donor import Donor
from app.models.requester import Requester
from app.models.user import User


@pytest.fixture
def other_requester_user(db: Session) -> User:
    """Create a second requester for isolation testing."""
    user = User(
        username="city_hospital",
        password_hash=hash_password("password123"),
        role="requester",
        is_active=True,
    )
    db.add(user)
    db.flush()
    requester = Requester(
        user_id=user.user_id,
        name="City General Hospital",
        type="hospital",
        phone="9876500000",
        address="Bandra, Mumbai",
    )
    db.add(requester)
    db.commit()
    db.refresh(user)
    return user


def test_create_request_rbac(client: TestClient, admin_client: TestClient, staff_client: TestClient, requester_client: TestClient):
    """Only requesters can create blood requests; unauthenticated -> 401, admin/staff -> 403."""
    payload = {"blood_group": "A+", "quantity": 2, "urgency": "emergency"}

    # Unauthenticated -> 401
    res1 = client.post("/api/requests", json=payload)
    assert res1.status_code == 401

    # Admin -> 403
    res2 = admin_client.post("/api/requests", json=payload)
    assert res2.status_code == 403
    assert res2.json()["detail"]["code"] == "FORBIDDEN"

    # Staff -> 403
    res3 = staff_client.post("/api/requests", json=payload)
    assert res3.status_code == 403
    assert res3.json()["detail"]["code"] == "FORBIDDEN"

    # Requester -> 201
    res4 = requester_client.post("/api/requests", json=payload)
    assert res4.status_code == 201
    data = res4.json()
    assert data["blood_group"] == "A+"
    assert data["quantity"] == 2
    assert data["urgency"] == "emergency"
    assert data["status"] == "pending"
    assert data["request_date"] == str(clock.today())
    assert data["issued_count"] == 0


def test_create_request_validation(requester_client: TestClient):
    """Strict validation on blood_group, quantity, urgency."""
    # Invalid blood group
    res1 = requester_client.post("/api/requests", json={"blood_group": "X+", "quantity": 1, "urgency": "routine"})
    assert res1.status_code == 422

    # Invalid urgency
    res2 = requester_client.post("/api/requests", json={"blood_group": "O+", "quantity": 1, "urgency": "asap"})
    assert res2.status_code == 422

    # Quantity 0
    res3 = requester_client.post("/api/requests", json={"blood_group": "O+", "quantity": 0, "urgency": "routine"})
    assert res3.status_code == 422

    # Negative quantity
    res4 = requester_client.post("/api/requests", json={"blood_group": "O+", "quantity": -3, "urgency": "routine"})
    assert res4.status_code == 422

    # Float quantity
    res5 = requester_client.post("/api/requests", json={"blood_group": "O+", "quantity": 1.5, "urgency": "routine"})
    assert res5.status_code == 422

    # String quantity
    res6 = requester_client.post("/api/requests", json={"blood_group": "O+", "quantity": "2", "urgency": "routine"})
    assert res6.status_code == 422

    # Boolean quantity
    res7 = requester_client.post("/api/requests", json={"blood_group": "O+", "quantity": True, "urgency": "routine"})
    assert res7.status_code == 422


def test_list_requests_isolation(
    requester_client: TestClient,
    admin_client: TestClient,
    requester_user: User,
    other_requester_user: User,
    db: Session,
):
    """Requester sees only their own requests; admin sees all requests."""
    today = clock.today()
    # Request 1 belonging to requester_user
    req1 = BloodRequest(
        requester_id=requester_user.requester_profile.requester_id,
        blood_group="B+",
        quantity=1,
        urgency="routine",
        status="pending",
        request_date=today,
    )
    # Request 2 belonging to other_requester_user
    req2 = BloodRequest(
        requester_id=other_requester_user.requester_profile.requester_id,
        blood_group="AB+",
        quantity=3,
        urgency="emergency",
        status="pending",
        request_date=today,
    )
    db.add_all([req1, req2])
    db.commit()

    # Requester lists requests - must see only req1 even if supplying other requester_id
    res_req = requester_client.get(f"/api/requests?requester_id={other_requester_user.requester_profile.requester_id}")
    assert res_req.status_code == 200
    items = res_req.json()["items"]
    assert len(items) == 1
    assert items[0]["request_id"] == req1.request_id

    # Admin lists requests - sees both
    res_admin = admin_client.get("/api/requests")
    assert res_admin.status_code == 200
    admin_items = res_admin.json()["items"]
    req_ids = [item["request_id"] for item in admin_items]
    assert req1.request_id in req_ids
    assert req2.request_id in req_ids


def test_list_requests_sorting_and_filtering(admin_client: TestClient, requester_user: User, db: Session):
    """Test priority sort (emergency first, request_date ASC, request_id ASC) vs newest sort."""
    today = clock.today()
    req_id = requester_user.requester_profile.requester_id

    r1 = BloodRequest(requester_id=req_id, blood_group="A+", quantity=1, urgency="routine", status="pending", request_date=today - timedelta(days=2))
    r2 = BloodRequest(requester_id=req_id, blood_group="B+", quantity=1, urgency="emergency", status="pending", request_date=today - timedelta(days=1))
    r3 = BloodRequest(requester_id=req_id, blood_group="O+", quantity=1, urgency="routine", status="pending", request_date=today)
    db.add_all([r1, r2, r3])
    db.commit()

    # Priority sort: emergency (r2) should come first, then r1 (older date), then r3
    res_pri = admin_client.get("/api/requests?sort=priority")
    assert res_pri.status_code == 200
    ids = [i["request_id"] for i in res_pri.json()["items"]]
    assert ids.index(r2.request_id) < ids.index(r1.request_id)
    assert ids.index(r1.request_id) < ids.index(r3.request_id)

    # Newest sort: r3 (today), then r2, then r1
    res_new = admin_client.get("/api/requests?sort=newest")
    assert res_new.status_code == 200
    newest_ids = [i["request_id"] for i in res_new.json()["items"]]
    assert newest_ids.index(r3.request_id) < newest_ids.index(r2.request_id)
    assert newest_ids.index(r2.request_id) < newest_ids.index(r1.request_id)

    # Invalid sort returns 422
    assert admin_client.get("/api/requests?sort=invalid").status_code == 422


def test_get_request_detail_isolation(
    requester_client: TestClient,
    admin_client: TestClient,
    requester_user: User,
    other_requester_user: User,
    db: Session,
):
    """Requester accessing another's request yields 404 (NEVER 403)."""
    req_other = BloodRequest(
        requester_id=other_requester_user.requester_profile.requester_id,
        blood_group="O-",
        quantity=1,
        urgency="routine",
        status="pending",
        request_date=clock.today(),
    )
    db.add(req_other)
    db.commit()

    # Requester attempts to view other's request -> 404 NOT_FOUND
    res = requester_client.get(f"/api/requests/{req_other.request_id}")
    assert res.status_code == 404
    assert res.json()["detail"]["code"] == "NOT_FOUND"

    # Admin views other's request -> 200 OK
    res_admin = admin_client.get(f"/api/requests/{req_other.request_id}")
    assert res_admin.status_code == 200
    assert res_admin.json()["request_id"] == req_other.request_id


def test_request_matches_endpoint(admin_client: TestClient, requester_client: TestClient, requester_user: User, db: Session):
    """Matches endpoint ranks available compatible units nearest-expiry-first and evaluates sufficiency."""
    today = clock.today()
    req = BloodRequest(
        requester_id=requester_user.requester_profile.requester_id,
        blood_group="B+",
        quantity=2,
        urgency="emergency",
        status="pending",
        request_date=today,
    )
    db.add(req)
    db.flush()

    # Requesters are blocked with 403
    res_req = requester_client.get(f"/api/requests/{req.request_id}/matches")
    assert res_req.status_code == 403

    # Add donor and compatible units (B+, B-, O+, O- are compatible with B+)
    donor = Donor(name="Donor Sam", dob=today - timedelta(days=25 * 365), gender="male", blood_group="B+", phone="1234567890", address="Goregaon", weight=60.0)
    db.add(donor)
    db.flush()

    u1 = BloodUnit(donor_id=donor.donor_id, blood_group="B+", collection_date=today - timedelta(days=5), expiry_date=today + timedelta(days=20), status="available")
    u2 = BloodUnit(donor_id=donor.donor_id, blood_group="O-", collection_date=today - timedelta(days=10), expiry_date=today + timedelta(days=10), status="available")
    # Expired unit (should not be in matches)
    u_exp = BloodUnit(donor_id=donor.donor_id, blood_group="B+", collection_date=today - timedelta(days=45), expiry_date=today - timedelta(days=2), status="available")
    db.add_all([u1, u2, u_exp])
    db.commit()

    res_matches = admin_client.get(f"/api/requests/{req.request_id}/matches")
    assert res_matches.status_code == 200
    data = res_matches.json()
    assert data["request_id"] == req.request_id
    assert data["compatible_groups"] == ["B+", "B-", "O+", "O-"]
    assert data["available_compatible_count"] == 2
    assert data["sufficient"] is True
    assert len(data["allocation_preview_unit_ids"]) == 2
    # Nearest expiry first: u2 (10 days) should precede u1 (20 days)
    assert data["allocation_preview_unit_ids"][0] == u2.unit_id
    assert data["allocation_preview_unit_ids"][1] == u1.unit_id


def test_approve_reject_issue_endpoints(
    admin_client: TestClient,
    requester_user: User,
    db: Session,
):
    """End-to-end API lifecycle: create -> approve -> issue -> stock decreases -> units linked."""
    today = clock.today()
    req = BloodRequest(
        requester_id=requester_user.requester_profile.requester_id,
        blood_group="AB+",
        quantity=1,
        urgency="routine",
        status="pending",
        request_date=today,
    )
    db.add(req)

    donor = Donor(name="Donor AB", dob=today - timedelta(days=22 * 365), gender="female", blood_group="AB+", phone="9871112222", address="Sion", weight=55.0)
    db.add(donor)
    db.flush()

    unit = BloodUnit(donor_id=donor.donor_id, blood_group="AB+", collection_date=today, expiry_date=today + timedelta(days=42), status="available")
    db.add(unit)
    db.commit()

    # 1. Approve
    res_app = admin_client.post(f"/api/requests/{req.request_id}/approve")
    assert res_app.status_code == 200
    assert res_app.json()["status"] == "approved"

    # 2. Issue
    res_iss = admin_client.post(f"/api/requests/{req.request_id}/issue")
    assert res_iss.status_code == 200
    data = res_iss.json()
    assert data["status"] == "issued"
    assert data["issued_count"] == 1
    assert len(data["issued_units"]) == 1
    assert data["issued_units"][0]["unit_id"] == unit.unit_id
    assert data["issued_units"][0]["blood_group"] == "AB+"

    # 3. Unit status updated in DB
    db.refresh(unit)
    assert unit.status == "issued"


def test_delete_request_guards(admin_client: TestClient, staff_client: TestClient, requester_user: User, db: Session):
    """Admin only delete; issued requests cannot be deleted."""
    today = clock.today()
    req_pending = BloodRequest(requester_id=requester_user.requester_profile.requester_id, blood_group="O+", quantity=1, urgency="routine", status="pending", request_date=today)
    req_issued = BloodRequest(requester_id=requester_user.requester_profile.requester_id, blood_group="O+", quantity=1, urgency="routine", status="issued", request_date=today)
    db.add_all([req_pending, req_issued])
    db.commit()

    # Staff gets 403
    assert staff_client.delete(f"/api/requests/{req_pending.request_id}").status_code == 403

    # Admin delete pending -> 204
    assert admin_client.delete(f"/api/requests/{req_pending.request_id}").status_code == 204

    # Admin delete issued -> 409 REFERENCED_RECORD
    res_del_issued = admin_client.delete(f"/api/requests/{req_issued.request_id}")
    assert res_del_issued.status_code == 409
    assert res_del_issued.json()["detail"]["code"] == "REFERENCED_RECORD"
