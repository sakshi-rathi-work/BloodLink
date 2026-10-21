import os
import sys

# Ensure backend root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Generator
from fastapi import FastAPI
import httpx
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from app.core import clock
from app.core.config import settings
from app.core.deps import get_db
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.main import app
from app.models.requester import Requester
from app.models.staff import Staff
from app.models.user import User

TEST_DB_URL = os.getenv("TEST_DATABASE_URL", settings.TEST_DATABASE_URL)

# Test connection, fallback to SQLite if PostgreSQL is unavailable
try:
    test_engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
    with test_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    is_sqlite = False
except Exception:
    TEST_DB_URL = "sqlite:///./bloodlink_test.db"
    test_engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
    is_sqlite = True

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables in test database once per session."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    # If PostgreSQL, create view v_transactions
    if not is_sqlite:
        with test_engine.connect() as conn:
            conn.execute(text("DROP VIEW IF EXISTS v_transactions CASCADE;"))
            conn.execute(text("""
                CREATE VIEW v_transactions AS
                SELECT 'donation'::text AS transaction_type,
                       u.unit_id, u.blood_group, u.collection_date AS transaction_date,
                       u.donor_id, NULL::integer AS request_id, NULL::integer AS staff_id
                FROM blood_units u
                UNION ALL
                SELECT 'issue'::text, i.unit_id, u.blood_group, i.issue_date,
                       u.donor_id, i.request_id, i.issued_by
                FROM issue_records i
                JOIN blood_units u ON u.unit_id = i.unit_id
                UNION ALL
                SELECT 'wastage'::text, u.unit_id, u.blood_group, u.expiry_date,
                       u.donor_id, NULL::integer, NULL::integer
                FROM blood_units u
                WHERE u.status = 'expired';
            """))
            conn.commit()

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Yield a database session for a test and clean up data after."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Clean up tables after each test
        with test_engine.connect() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                conn.execute(text(f"DELETE FROM {table.name};"))
            conn.commit()


@pytest.fixture
def override_get_db(db: Session):
    """Override FastAPI get_db dependency to use the test session."""
    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.pop(get_db, None)


from fastapi.testclient import TestClient

@pytest.fixture
def client(override_get_db) -> Generator[TestClient, None, None]:
    """Unauthenticated HTTP test client."""
    with TestClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def admin_user(db: Session) -> User:
    """Fixture providing an active admin user and staff record."""
    user = User(
        username="test_admin",
        password_hash=hash_password("adminpassword123"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.flush()
    staff = Staff(user_id=user.user_id, name="Test Administrator")
    db.add(staff)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_client(override_get_db, admin_user: User) -> TestClient:
    """HTTP client authenticated with admin JWT."""
    client = TestClient(app=app, base_url="http://testserver")
    token = create_access_token(user_id=admin_user.user_id, role="admin")
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
def staff_user(db: Session) -> User:
    """Fixture providing an active staff user and staff record."""
    user = User(
        username="test_staff",
        password_hash=hash_password("staffpassword123"),
        role="staff",
        is_active=True,
    )
    db.add(user)
    db.flush()
    staff = Staff(user_id=user.user_id, name="Test Staff Member")
    db.add(staff)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def staff_client(override_get_db, staff_user: User) -> TestClient:
    """HTTP client authenticated with staff JWT."""
    client = TestClient(app=app, base_url="http://testserver")
    token = create_access_token(user_id=staff_user.user_id, role="staff")
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
def requester_user(db: Session) -> User:
    """Fixture providing an active requester user and requester record."""
    user = User(
        username="test_hospital",
        password_hash=hash_password("hospitalpass123"),
        role="requester",
        is_active=True,
    )
    db.add(user)
    db.flush()
    requester = Requester(
        user_id=user.user_id,
        name="Apollo Hospital",
        type="hospital",
        phone="9876543210",
        address="123 Health Ave, Mumbai",
    )
    db.add(requester)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def requester_client(override_get_db, requester_user: User) -> TestClient:
    """HTTP client authenticated with requester JWT."""
    client = TestClient(app=app, base_url="http://testserver")
    token = create_access_token(user_id=requester_user.user_id, role="requester")
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
def freeze_clock():
    """Context/fixture to freeze today's date and reset afterwards."""
    def _freeze(val):
        clock.set_today(val)

    yield _freeze
    clock.set_today(None)
