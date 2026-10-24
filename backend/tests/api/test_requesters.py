import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.security import create_access_token, hash_password
from app.models.activity_log import ActivityLog
from app.models.blood_request import BloodRequest
from app.models.requester import Requester
from app.models.user import User


def test_requester_me_success(requester_client: TestClient, requester_user: User):
    """Requester can retrieve their own profile via /me."""
    res = requester_client.get("/api/requesters/me")
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == requester_user.user_id
    assert data["username"] == requester_user.username
    assert data["name"] == "Apollo Hospital"
    assert data["type"] == "hospital"
    assert data["phone"] == "9876543210"
    assert "password_hash" not in data


def test_requester_me_not_captured_by_id(requester_client: TestClient):
    """Proves /me route is declared before /{requester_id} and not captured as an integer ID."""
    res = requester_client.get("/api/requesters/me")
    assert res.status_code == 200
    # If /me were captured by /{requester_id:int}, FastAPI would return 422 Unprocessable Entity


def test_requester_me_rbac(client: TestClient, admin_client: TestClient, staff_client: TestClient):
    """Unauthenticated gets 401; Admin/Staff get 403 on /requesters/me."""
    res_unauth = client.get("/api/requesters/me")
    assert res_unauth.status_code == 401
    assert res_unauth.json()["detail"]["code"] == "NOT_AUTHENTICATED"

    res_admin = admin_client.get("/api/requesters/me")
    assert res_admin.status_code == 403
    assert res_admin.json()["detail"]["code"] == "FORBIDDEN"

    res_staff = staff_client.get("/api/requesters/me")
    assert res_staff.status_code == 403
    assert res_staff.json()["detail"]["code"] == "FORBIDDEN"


def test_requester_patch_me(requester_client: TestClient, db: Session, requester_user: User):
    """Requester can update their own details and an activity log is written."""
    payload = {
        "name": "Apollo Super Specialty Hospital",
        "phone": "9998887776",
        "address": "456 Health Boulevard, Mumbai",
    }
    res = requester_client.patch("/api/requesters/me", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Apollo Super Specialty Hospital"
    assert data["phone"] == "9998887776"
    assert data["address"] == "456 Health Boulevard, Mumbai"

    # Verify activity log
    log = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.entity_type == "requester",
            ActivityLog.action == "update",
            ActivityLog.entity_id == requester_user.requester_profile.requester_id,
        )
        .first()
    )
    assert log is not None
    assert log.details["name"] == "Apollo Super Specialty Hospital"


def test_requester_patch_me_validation(requester_client: TestClient):
    """Empty or invalid fields in PATCH return 422."""
    res1 = requester_client.patch("/api/requesters/me", json={"name": "   "})
    assert res1.status_code == 422

    res2 = requester_client.patch("/api/requesters/me", json={"type": "invalid_type"})
    assert res2.status_code == 422


def test_requester_list_admin_staff(
    admin_client: TestClient,
    staff_client: TestClient,
    requester_client: TestClient,
    client: TestClient,
    requester_user: User,
):
    """Admin and Staff can list requesters; Requesters get 403."""
    res_admin = admin_client.get("/api/requesters")
    assert res_admin.status_code == 200
    assert res_admin.json()["total"] >= 1
    assert res_admin.json()["items"][0]["username"] == requester_user.username

    res_staff = staff_client.get("/api/requesters")
    assert res_staff.status_code == 200

    res_req = requester_client.get("/api/requesters")
    assert res_req.status_code == 403
    assert res_req.json()["detail"]["code"] == "FORBIDDEN"

    res_unauth = client.get("/api/requesters")
    assert res_unauth.status_code == 401


def test_requester_list_filters(admin_client: TestClient, db: Session):
    """Test filtering by type and q search."""
    # Create patient requester
    patient_user = User(username="patient_bob", password_hash=hash_password("password123"), role="requester", is_active=True)
    db.add(patient_user)
    db.flush()
    patient = Requester(user_id=patient_user.user_id, name="Bob Patient", type="patient", phone="1122334455", address="Borivali")
    db.add(patient)
    db.commit()

    # Filter by type=patient
    res_type = admin_client.get("/api/requesters?type=patient")
    assert res_type.status_code == 200
    assert all(item["type"] == "patient" for item in res_type.json()["items"])

    # Search q=bob
    res_q = admin_client.get("/api/requesters?q=bob")
    assert res_q.status_code == 200
    assert any(item["name"] == "Bob Patient" for item in res_q.json()["items"])

    # Search q by phone
    res_phone = admin_client.get("/api/requesters?q=112233")
    assert res_phone.status_code == 200
    assert any(item["phone"] == "1122334455" for item in res_phone.json()["items"])


def test_requester_detail(admin_client: TestClient, requester_user: User):
    """Admin/staff can get requester by ID; missing ID returns 404."""
    req_id = requester_user.requester_profile.requester_id
    res = admin_client.get(f"/api/requesters/{req_id}")
    assert res.status_code == 200
    assert res.json()["name"] == requester_user.requester_profile.name

    res_missing = admin_client.get("/api/requesters/999999")
    assert res_missing.status_code == 404
    assert res_missing.json()["detail"]["code"] == "NOT_FOUND"


def test_requester_delete_rbac_and_referenced_record(
    admin_client: TestClient,
    staff_client: TestClient,
    requester_client: TestClient,
    db: Session,
):
    """Admin can delete requester; Staff/Requester get 403; foreign key constraint returns 409 REFERENCED_RECORD."""
    # 1. Create a disposable requester
    user = User(username="del_user", password_hash=hash_password("password123"), role="requester", is_active=True)
    db.add(user)
    db.flush()
    req = Requester(user_id=user.user_id, name="Disposable Req", type="patient", phone="5555555555", address="Dadar")
    db.add(req)
    db.commit()
    req_id = req.requester_id

    # Staff gets 403
    res_staff = staff_client.delete(f"/api/requesters/{req_id}")
    assert res_staff.status_code == 403

    # Requester gets 403
    res_req = requester_client.delete(f"/api/requesters/{req_id}")
    assert res_req.status_code == 403

    # Add a blood request referencing this requester
    from app.core import clock
    blood_req = BloodRequest(
        requester_id=req_id,
        blood_group="O+",
        quantity=2,
        urgency="routine",
        status="pending",
        request_date=clock.today(),
    )
    db.add(blood_req)
    db.commit()

    # Now admin delete should fail with 409 REFERENCED_RECORD
    res_del_conflict = admin_client.delete(f"/api/requesters/{req_id}")
    assert res_del_conflict.status_code == 409
    assert res_del_conflict.json()["detail"]["code"] == "REFERENCED_RECORD"

    # Remove the referencing blood request
    db.delete(blood_req)
    db.commit()

    # Now admin delete should succeed with 204
    res_del_ok = admin_client.delete(f"/api/requesters/{req_id}")
    assert res_del_ok.status_code == 204

    # Verify both requester and user row are gone
    assert db.query(Requester).filter(Requester.requester_id == req_id).first() is None
    assert db.query(User).filter(User.username == "del_user").first() is None
