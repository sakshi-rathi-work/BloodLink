import httpx
from app.models.staff import Staff
from app.models.user import User


def test_list_staff_admin_allowed(admin_client: httpx.Client):
    response = admin_client.get("/api/staff")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 1


def test_list_staff_forbidden_for_staff(staff_client: httpx.Client):
    response = staff_client.get("/api/staff")
    assert response.status_code == 403
    data = response.json()
    assert data["detail"]["code"] == "FORBIDDEN"


def test_list_staff_forbidden_for_requester(requester_client: httpx.Client):
    response = requester_client.get("/api/staff")
    assert response.status_code == 403
    data = response.json()
    assert data["detail"]["code"] == "FORBIDDEN"


def test_create_staff_success(admin_client: httpx.Client):
    payload = {
        "username": "new_staff_nurse",
        "password": "password12345",
        "name": "Nurse Joy",
        "role": "staff",
    }
    response = admin_client.post("/api/staff", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "new_staff_nurse"
    assert data["name"] == "Nurse Joy"
    assert data["role"] == "staff"
    assert data["is_active"] is True


def test_update_staff_success(admin_client: httpx.Client, staff_user: User):
    staff_id = staff_user.staff_profile.staff_id
    payload = {
        "name": "Updated Staff Name",
        "is_active": False,
    }
    response = admin_client.patch(f"/api/staff/{staff_id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Staff Name"
    assert data["is_active"] is False


def test_admin_self_deactivation_forbidden(admin_client: httpx.Client, admin_user: User):
    admin_staff_id = admin_user.staff_profile.staff_id
    payload = {"is_active": False}
    response = admin_client.patch(f"/api/staff/{admin_staff_id}", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["detail"]["code"] == "SELF_MODIFICATION_FORBIDDEN"


def test_admin_self_demotion_forbidden(admin_client: httpx.Client, admin_user: User):
    admin_staff_id = admin_user.staff_profile.staff_id
    payload = {"role": "staff"}
    response = admin_client.patch(f"/api/staff/{admin_staff_id}", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["detail"]["code"] == "SELF_MODIFICATION_FORBIDDEN"


def test_admin_self_deletion_forbidden(admin_client: httpx.Client, admin_user: User):
    admin_staff_id = admin_user.staff_profile.staff_id
    response = admin_client.delete(f"/api/staff/{admin_staff_id}")
    assert response.status_code == 409
    data = response.json()
    assert data["detail"]["code"] == "SELF_MODIFICATION_FORBIDDEN"


def test_delete_other_staff_success(admin_client: httpx.Client, staff_user: User):
    staff_id = staff_user.staff_profile.staff_id
    response = admin_client.delete(f"/api/staff/{staff_id}")
    assert response.status_code == 204

    # Verify not found
    get_res = admin_client.get(f"/api/staff/{staff_id}")
    assert get_res.status_code == 404
