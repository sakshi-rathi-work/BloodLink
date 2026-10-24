from typing import Literal, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import or_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core import errors
from app.core.deps import get_db, require_roles
from app.models.requester import Requester
from app.models.user import User
from app.schemas.requester import RequesterListResponse, RequesterResponse, RequesterUpdateRequest
from app.services import activity_log

router = APIRouter(prefix="/requesters", tags=["Requesters"])


def to_requester_response(requester: Requester) -> RequesterResponse:
    """Format Requester ORM object to API response schema without exposing password_hash."""
    return RequesterResponse(
        requester_id=requester.requester_id,
        user_id=requester.user_id,
        username=requester.user.username if requester.user else "",
        name=requester.name,
        type=requester.type,
        phone=requester.phone,
        address=requester.address,
    )


# CRITICAL: /me routes declared BEFORE parameterized /{requester_id} routes
@router.get("/me", response_model=RequesterResponse, summary="Get own requester profile")
def get_requester_me(
    current_user: User = Depends(require_roles("requester")),
):
    """Requester self-service: retrieve own profile."""
    if not current_user.requester_profile:
        raise errors.not_found("Requester profile not found for current user.")
    return to_requester_response(current_user.requester_profile)


@router.patch("/me", response_model=RequesterResponse, summary="Update own requester profile")
def update_requester_me(
    payload: RequesterUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("requester")),
):
    """Requester self-service: update own profile details."""
    requester = current_user.requester_profile
    if not requester:
        raise errors.not_found("Requester profile not found for current user.")

    changes = {}
    if payload.name is not None:
        requester.name = payload.name.strip()
        changes["name"] = requester.name
    if payload.type is not None:
        requester.type = payload.type
        changes["type"] = requester.type
    if payload.phone is not None:
        requester.phone = payload.phone.strip()
        changes["phone"] = requester.phone
    if payload.address is not None:
        requester.address = payload.address.strip()
        changes["address"] = requester.address

    if changes:
        activity_log.record(
            db,
            user_id=current_user.user_id,
            action="update",
            entity_type="requester",
            entity_id=requester.requester_id,
            details=changes,
        )

    db.commit()
    db.refresh(requester)
    return to_requester_response(requester)


@router.get("", response_model=RequesterListResponse, summary="List requesters")
def list_requesters(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[Literal["hospital", "patient"]] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Admin and Staff: List registered requesters with pagination, type filtering, and search."""
    query = db.query(Requester).join(Requester.user)

    if type:
        query = query.filter(Requester.type == type)
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(Requester.name.ilike(term), Requester.phone.ilike(term))
        )

    total = query.count()
    items = (
        query.order_by(Requester.requester_id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return RequesterListResponse(
        items=[to_requester_response(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{requester_id}", response_model=RequesterResponse, summary="Get requester details")
def get_requester(
    requester_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Admin and Staff: View details of a specific requester."""
    requester = db.query(Requester).filter(Requester.requester_id == requester_id).first()
    if not requester:
        raise errors.not_found(f"Requester with ID {requester_id} not found.")
    return to_requester_response(requester)


@router.delete("/{requester_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete requester account")
def delete_requester(
    requester_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Admin only: Delete requester profile and underlying user account in one transaction."""
    requester = db.query(Requester).filter(Requester.requester_id == requester_id).first()
    if not requester:
        raise errors.not_found(f"Requester with ID {requester_id} not found.")

    user = requester.user
    req_name = requester.name
    username = user.username if user else ""

    try:
        # Delete the user's own activity log entries first to satisfy the
        # activity_logs.user_id ON DELETE RESTRICT FK constraint.
        # These audit logs recorded actions BY this user (e.g. their registration),
        # not records that reference them as a data entity — safe to cascade.
        if user:
            db.execute(text("DELETE FROM activity_logs WHERE user_id = :uid"), {"uid": user.user_id})
        # Delete profile row then user row in one atomic transaction
        db.delete(requester)
        if user:
            db.delete(user)
        db.flush()

        activity_log.record(
            db,
            user_id=current_user.user_id,
            action="delete",
            entity_type="requester",
            entity_id=requester_id,
            details={"name": req_name, "username": username},
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise errors.referenced_record(
            f"Requester '{req_name}' cannot be deleted because they are referenced by existing requests or system records."
        )

    return None
