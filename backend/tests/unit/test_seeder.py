from datetime import date, timedelta
import pytest
from scripts.seed_synthetic_data import ALLOWED_DBS, LOOPBACK_HOSTS, validate_safety_guards


def test_safety_guards_disallow_non_loopback():
    with pytest.raises(ValueError, match="Safety Guard: Seeder can only target local database"):
        validate_safety_guards(
            "postgresql+psycopg://bloodlink:bloodlink@192.168.1.100:5432/bloodlink",
            is_reset=False,
            auto_confirm=True,
        )


def test_safety_guards_disallow_unlisted_database():
    with pytest.raises(ValueError, match="not in allowed list"):
        validate_safety_guards(
            "postgresql+psycopg://bloodlink:bloodlink@localhost:5432/production_hospital_db",
            is_reset=False,
            auto_confirm=True,
        )


def test_safety_guards_pass_for_allowed_local_db():
    # Should not raise
    validate_safety_guards(
        "postgresql+psycopg://bloodlink:bloodlink@localhost:5432/bloodlink_test",
        is_reset=False,
        auto_confirm=True,
    )
    validate_safety_guards(
        "postgresql+psycopg://bloodlink:bloodlink@127.0.0.1:5432/bloodlink",
        is_reset=False,
        auto_confirm=True,
    )


def test_safety_guards_require_postgres_or_sqlite():
    with pytest.raises(ValueError, match="is not supported"):
        validate_safety_guards(
            "mysql+pymysql://user:pass@localhost:3306/bloodlink",
            is_reset=False,
            auto_confirm=True,
        )
