import httpx
from app.models.user import User


def test_list_activity_logs_admin_allowed(admin_client: httpx.Client):
    response = admin_client.get("/api/activity-logs")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_list_activity_logs_forbidden_for_staff(staff_client: httpx.Client):
    response = staff_client.get("/api/activity-logs")
    assert response.status_code == 403
    data = response.json()
    assert data["detail"]["code"] == "FORBIDDEN"


def test_activity_log_filters(admin_client: httpx.Client):
    # Create staff to trigger log
    admin_client.post(
        "/api/staff",
        json={"username": "logged_staff", "password": "password123", "name": "Log Person", "role": "staff"},
    )

    # Filter by entity_type=staff
    response = admin_client.get("/api/activity-logs?entity_type=staff")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["entity_type"] == "staff"
