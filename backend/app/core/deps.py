from typing import Callable, Generator
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session
from app.core import errors
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """Database session dependency for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate JWT access token and return active authenticated user."""
    if not token:
        raise errors.not_authenticated("Authentication token is missing.")

    try:
        payload = decode_access_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise errors.not_authenticated("Invalid token payload.")
        user_id = int(user_id_str)
    except jwt.ExpiredSignatureError:
        raise errors.not_authenticated("Authentication token has expired.")
    except Exception:
        raise errors.not_authenticated("Invalid authentication token.")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise errors.not_authenticated("User not found.")

    if not user.is_active:
        raise errors.account_disabled("User account is disabled.")

    return user


def require_roles(*allowed_roles: str) -> Callable[[User], User]:
    """Dependency factory ensuring user has one of the allowed roles."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise errors.forbidden("Access forbidden for current user role.")
        return current_user

    return role_checker
