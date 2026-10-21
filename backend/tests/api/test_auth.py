import httpx
from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.models.user import User


def test_login_success(client: httpx.Client, admin_user: User):
    response = client.post(
        "/api/auth/login",
        json={"username": "test_admin", "password": "adminpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "test_admin"
    assert data["user"]["role"] == "admin"


def test_login_invalid_credentials(client: httpx.Client, admin_user: User):
    response = client.post(
        "/api/auth/login",
        json={"username": "test_admin", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["code"] == "INVALID_CREDENTIALS"


def test_login_account_disabled(client: httpx.Client, db: Session):
    disabled_user = User(
        username="disabled_user",
        password_hash=hash_password("password123"),
        role="staff",
        is_active=False,
    )
    db.add(disabled_user)
    db.commit()

    response = client.post(
        "/api/auth/login",
        json={"username": "disabled_user", "password": "password123"},
    )
    assert response.status_code == 403
    data = response.json()
    assert data["detail"]["code"] == "ACCOUNT_DISABLED"


def test_register_requester_success(client: httpx.Client):
    payload = {
        "username": "city_hospital",
        "password": "securepassword123",
        "name": "City General Hospital",
        "type": "hospital",
        "phone": "9876543210",
        "address": "456 Central Ave, Pune",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "city_hospital"
    assert data["user"]["role"] == "requester"
    assert data["user"]["name"] == "City General Hospital"
    assert data["user"]["profile_id"] is not None


def test_register_requester_duplicate_username(client: httpx.Client, requester_user: User):
    payload = {
        "username": requester_user.username,
        "password": "securepassword123",
        "name": "Duplicate Hospital",
        "type": "hospital",
        "phone": "9876543210",
        "address": "456 Central Ave",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["detail"]["code"] == "DUPLICATE"


def test_get_me_authenticated(admin_client: httpx.Client, admin_user: User):
    response = admin_client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == admin_user.username
    assert data["role"] == "admin"


def test_get_me_unauthenticated(client: httpx.Client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["code"] == "NOT_AUTHENTICATED"
