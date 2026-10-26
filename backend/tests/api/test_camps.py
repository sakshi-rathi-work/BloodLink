import httpx
from sqlalchemy.orm import Session
from app.models.activity_log import ActivityLog
from app.models.donation_camp import DonationCamp


def test_create_camp_staff_allowed(staff_client: httpx.Client):
    payload = {
        "location": "Bandra Community Center",
        "camp_date": "2026-11-20",
        "target_units": 100,
        "units_collected": 0,
    }
    response = staff_client.post("/api/camps", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["location"] == "Bandra Community Center"
    assert data["camp_date"] == "2026-11-20"
    assert data["target_units"] == 100
    assert data["units_collected"] == 0
    assert "camp_id" in data


def test_create_camp_requester_forbidden(requester_client: httpx.Client):
    payload = {
        "location": "Unauthorized Location",
        "camp_date": "2026-11-20",
        "target_units": 50,
    }
    response = requester_client.post("/api/camps", json=payload)
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "FORBIDDEN"


def test_create_camp_invalid_target_units(staff_client: httpx.Client):
    payload = {
        "location": "Test Campus",
        "camp_date": "2026-11-20",
        "target_units": 0,
    }
    response = staff_client.post("/api/camps", json=payload)
    assert response.status_code == 422


def test_list_camps_pagination_and_date_filters(staff_client: httpx.Client):
    # Seed two camps
    c1 = staff_client.post(
        "/api/camps",
        json={"location": "Camp Nov", "camp_date": "2026-11-01", "target_units": 40},
    ).json()
    c2 = staff_client.post(
        "/api/camps",
        json={"location": "Camp Dec", "camp_date": "2026-12-01", "target_units": 60},
    ).json()

    # List all
    response = staff_client.get("/api/camps")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 2

    # Filter by date range covering only Dec
    response_dec = staff_client.get("/api/camps?start_date=2026-11-15&end_date=2026-12-15")
    assert response_dec.status_code == 200
    dec_items = response_dec.json()["items"]
    dec_ids = [c["camp_id"] for c in dec_items]
    assert c2["camp_id"] in dec_ids
    assert c1["camp_id"] not in dec_ids


def test_get_camp_detail_and_not_found(staff_client: httpx.Client):
    create_res = staff_client.post(
        "/api/camps",
        json={"location": "Camp Xavier", "camp_date": "2026-11-10", "target_units": 75},
    )
    camp_id = create_res.json()["camp_id"]

    res = staff_client.get(f"/api/camps/{camp_id}")
    assert res.status_code == 200
    assert res.json()["location"] == "Camp Xavier"

    res_not_found = staff_client.get("/api/camps/999999")
    assert res_not_found.status_code == 404
    assert res_not_found.json()["detail"]["code"] == "NOT_FOUND"


def test_update_camp_success(staff_client: httpx.Client):
    create_res = staff_client.post(
        "/api/camps",
        json={"location": "Old Hall", "camp_date": "2026-11-05", "target_units": 50},
    )
    camp_id = create_res.json()["camp_id"]

    update_payload = {
        "location": "Renovated Town Hall",
        "units_collected": 55,
    }
    update_res = staff_client.patch(f"/api/camps/{camp_id}", json=update_payload)
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["location"] == "Renovated Town Hall"
    assert updated["units_collected"] == 55
    assert updated["target_units"] == 50


def test_delete_camp_staff_forbidden(staff_client: httpx.Client):
    create_res = staff_client.post(
        "/api/camps",
        json={"location": "Protected Camp", "camp_date": "2026-11-08", "target_units": 50},
    )
    camp_id = create_res.json()["camp_id"]

    delete_res = staff_client.delete(f"/api/camps/{camp_id}")
    assert delete_res.status_code == 403
    assert delete_res.json()["detail"]["code"] == "FORBIDDEN"


def test_delete_camp_admin_success(admin_client: httpx.Client):
    create_res = admin_client.post(
        "/api/camps",
        json={"location": "Camp to Delete", "camp_date": "2026-11-09", "target_units": 30},
    )
    camp_id = create_res.json()["camp_id"]

    delete_res = admin_client.delete(f"/api/camps/{camp_id}")
    assert delete_res.status_code == 204

    # Verify gone
    get_res = admin_client.get(f"/api/camps/{camp_id}")
    assert get_res.status_code == 404


def test_camp_activity_log(admin_client: httpx.Client, db: Session):
    create_res = admin_client.post(
        "/api/camps",
        json={"location": "Logged Camp Drive", "camp_date": "2026-11-12", "target_units": 80},
    )
    camp_id = create_res.json()["camp_id"]

    log = (
        db.query(ActivityLog)
        .filter(ActivityLog.entity_type == "donation_camp", ActivityLog.entity_id == camp_id)
        .first()
    )
    assert log is not None
    assert log.action == "create"
    assert "Logged Camp Drive" in str(log.details)
