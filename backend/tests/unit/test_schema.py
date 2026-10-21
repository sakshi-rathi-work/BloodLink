from datetime import date
from app.core import clock
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.db.base import Base


def test_metadata_tables_count():
    table_names = set(Base.metadata.tables.keys())
    expected_tables = {
        "users",
        "staff",
        "requesters",
        "donors",
        "blood_units",
        "blood_requests",
        "issue_records",
        "donation_camps",
        "activity_logs",
        "shortage_predictions",
    }
    assert expected_tables.issubset(table_names), f"Missing tables: {expected_tables - table_names}"


def test_password_hashing():
    pw = "SuperSecretPassword123"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_cycle():
    token = create_access_token(user_id=42, role="admin")
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "admin"
    assert "exp" in payload


def test_clock_today_freezing():
    normal_today = clock.today()
    assert normal_today == date.today()

    frozen = date(2025, 1, 15)
    clock.set_today(frozen)
    assert clock.today() == frozen

    clock.set_today(None)
    assert clock.today() == date.today()
