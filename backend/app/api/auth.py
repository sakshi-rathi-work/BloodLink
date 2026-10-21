from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core import errors
from app.core.deps import get_current_user, get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.requester import Requester
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequesterRequest, UserResponse
from app.services import activity_log

router = APIRouter(prefix="/auth", tags=["Auth"])


def build_user_response(user: User) -> UserResponse:
    profile_id = None
    name = user.username
    if user.staff_profile:
        profile_id = user.staff_profile.staff_id
        name = user.staff_profile.name
    elif user.requester_profile:
        profile_id = user.requester_profile.requester_id
        name = user.requester_profile.name

    return UserResponse(
        user_id=user.user_id,
        username=user.username,
        role=user.role,
        name=name,
        profile_id=profile_id,
    )


@router.post("/login", response_model=LoginResponse, summary="User login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate with username and password, returns JWT access token and user info."""
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise errors.invalid_credentials("Invalid username or password.")

    if not user.is_active:
        raise errors.account_disabled("This account has been disabled.")

    token = create_access_token(user_id=user.user_id, role=user.role)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=build_user_response(user),
    )


@router.post(
    "/register",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Requester self-registration",
)
def register(payload: RegisterRequesterRequest, db: Session = Depends(get_db)):
    """Public registration for hospital and patient requesters."""
    existing_user = db.query(User).filter(User.username == payload.username).first()
    if existing_user:
        raise errors.duplicate(f"Username '{payload.username}' is already taken.")

    # 1. Create user row
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role="requester",
        is_active=True,
    )
    db.add(user)
    db.flush()  # Populates user.user_id

    # 2. Create requester profile
    requester = Requester(
        user_id=user.user_id,
        name=payload.name,
        type=payload.type,
        phone=payload.phone,
        address=payload.address,
    )
    db.add(requester)
    db.flush()

    # 3. Log activity
    activity_log.record(
        db,
        user_id=user.user_id,
        action="create",
        entity_type="user",
        entity_id=user.user_id,
        details={"role": "requester", "username": user.username},
    )
    activity_log.record(
        db,
        user_id=user.user_id,
        action="create",
        entity_type="requester",
        entity_id=requester.requester_id,
        details={"name": requester.name, "type": requester.type},
    )

    db.commit()
    db.refresh(user)

    token = create_access_token(user_id=user.user_id, role=user.role)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=build_user_response(user),
    )


@router.get("/me", response_model=UserResponse, summary="Get current logged-in user")
def get_me(current_user: User = Depends(get_current_user)):
    """Return profile details for the authenticated user."""
    return build_user_response(current_user)
