from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core import errors
from app.core.deps import get_db, require_roles
from app.core.security import hash_password
from app.models.issue_record import IssueRecord
from app.models.staff import Staff
from app.models.user import User
from app.schemas.staff import StaffCreateRequest, StaffListResponse, StaffResponse, StaffUpdateRequest
from app.services import activity_log

router = APIRouter(prefix="/staff", tags=["Staff"])


def to_staff_response(staff: Staff) -> StaffResponse:
    return StaffResponse(
        staff_id=staff.staff_id,
        user_id=staff.user.user_id,
        username=staff.user.username,
        name=staff.name,
        role=staff.user.role,
        is_active=staff.user.is_active,
    )


@router.get("", response_model=StaffListResponse, summary="List staff and admin accounts")
def list_staff(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Admin-only: Paginated list of all staff and admin accounts."""
    query = db.query(Staff).join(User)
    total = query.count()
    items = query.order_by(Staff.staff_id.asc()).offset((page - 1) * page_size).limit(page_size).all()

    return StaffListResponse(
        items=[to_staff_response(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=StaffResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create staff or admin account",
)
def create_staff(
    payload: StaffCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Admin-only: Create a new staff or admin user and profile."""
    existing_user = db.query(User).filter(User.username == payload.username).first()
    if existing_user:
        raise errors.duplicate(f"Username '{payload.username}' is already taken.")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.flush()

    staff = Staff(
        user_id=user.user_id,
        name=payload.name,
    )
    db.add(staff)
    db.flush()

    activity_log.record(
        db,
        user_id=current_user.user_id,
        action="create",
        entity_type="staff",
        entity_id=staff.staff_id,
        details={"username": user.username, "role": user.role, "name": staff.name},
    )

    db.commit()
    db.refresh(staff)
    return to_staff_response(staff)


@router.get("/{staff_id}", response_model=StaffResponse, summary="Get staff member detail")
def get_staff_detail(
    staff_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Admin-only: Retrieve details for a specific staff member."""
    staff = db.query(Staff).filter(Staff.staff_id == staff_id).first()
    if not staff:
        raise errors.not_found(f"Staff member with ID {staff_id} not found.")

    return to_staff_response(staff)


@router.patch("/{staff_id}", response_model=StaffResponse, summary="Update staff member")
def update_staff(
    staff_id: int,
    payload: StaffUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Admin-only: Update staff member details, role, status, or password."""
    staff = db.query(Staff).filter(Staff.staff_id == staff_id).first()
    if not staff:
        raise errors.not_found(f"Staff member with ID {staff_id} not found.")

    # Guard self-modification: Admin cannot deactivate or demote own account
    if staff.user_id == current_user.user_id:
        if payload.is_active is False:
            raise errors.self_modification_forbidden("Administrators cannot deactivate their own account.")
        if payload.role is not None and payload.role != "admin":
            raise errors.self_modification_forbidden("Administrators cannot demote their own account.")

    changes = {}
    if payload.name is not None:
        staff.name = payload.name
        changes["name"] = payload.name
    if payload.role is not None:
        staff.user.role = payload.role
        changes["role"] = payload.role
    if payload.is_active is not None:
        staff.user.is_active = payload.is_active
        changes["is_active"] = payload.is_active
    if payload.password is not None:
        staff.user.password_hash = hash_password(payload.password)
        changes["password"] = "updated"

    if changes:
        activity_log.record(
            db,
            user_id=current_user.user_id,
            action="update",
            entity_type="staff",
            entity_id=staff.staff_id,
            details=changes,
        )

    db.commit()
    db.refresh(staff)
    return to_staff_response(staff)


@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete staff account")
def delete_staff(
    staff_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Admin-only: Delete staff account if not referenced by issue records."""
    staff = db.query(Staff).filter(Staff.staff_id == staff_id).first()
    if not staff:
        raise errors.not_found(f"Staff member with ID {staff_id} not found.")

    # Guard self-deletion
    if staff.user_id == current_user.user_id:
        raise errors.self_modification_forbidden("Administrators cannot delete their own account.")

    # Check for referenced issue_records
    has_issues = db.query(IssueRecord).filter(IssueRecord.issued_by == staff_id).first()
    if has_issues:
        raise errors.referenced_record(
            "Staff member cannot be deleted because they are referenced in issue records. Deactivate the account instead."
        )

    user = staff.user

    activity_log.record(
        db,
        user_id=current_user.user_id,
        action="delete",
        entity_type="staff",
        entity_id=staff_id,
        details={"username": user.username, "name": staff.name},
    )

    db.delete(staff)
    db.delete(user)
    db.commit()
    return None
