from typing import List
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core import clock, errors
from app.models.blood_request import BloodRequest
from app.models.issue_record import IssueRecord
from app.models.user import User
from app.services import activity_log
from app.services.inventory import expire_overdue_units
from app.services.matching import get_compatible_units


def approve_request(db: Session, request_id: int, current_user: User) -> BloodRequest:
    """
    Transition request from 'pending' to 'approved' using row-level locking.
    
    Raises 404 if request not found.
    Raises 409 INVALID_STATUS_TRANSITION if request status is not 'pending'.
    """
    request = (
        db.query(BloodRequest)
        .filter(BloodRequest.request_id == request_id)
        .with_for_update()
        .first()
    )
    if not request:
        raise errors.not_found(f"Blood request with ID {request_id} not found.")

    if request.status != "pending":
        raise errors.invalid_status_transition(
            f"Cannot approve request with status '{request.status}'. Only pending requests can be approved."
        )

    request.status = "approved"

    activity_log.record(
        db,
        user_id=current_user.user_id,
        action="approve",
        entity_type="blood_request",
        entity_id=request.request_id,
        details={
            "previous_status": "pending",
            "new_status": "approved",
            "blood_group": request.blood_group,
            "quantity": request.quantity,
        },
    )

    db.commit()
    db.refresh(request)
    return request


def reject_request(db: Session, request_id: int, current_user: User) -> BloodRequest:
    """
    Transition request from 'pending' or 'approved' to 'rejected' using row-level locking.
    
    Raises 404 if request not found.
    Raises 409 INVALID_STATUS_TRANSITION if request status is already terminal ('rejected' or 'issued').
    """
    request = (
        db.query(BloodRequest)
        .filter(BloodRequest.request_id == request_id)
        .with_for_update()
        .first()
    )
    if not request:
        raise errors.not_found(f"Blood request with ID {request_id} not found.")

    if request.status not in ("pending", "approved"):
        raise errors.invalid_status_transition(
            f"Cannot reject request with status '{request.status}'. Only pending or approved requests can be rejected."
        )

    previous_status = request.status
    request.status = "rejected"

    activity_log.record(
        db,
        user_id=current_user.user_id,
        action="reject",
        entity_type="blood_request",
        entity_id=request.request_id,
        details={
            "previous_status": previous_status,
            "new_status": "rejected",
            "blood_group": request.blood_group,
            "quantity": request.quantity,
        },
    )

    db.commit()
    db.refresh(request)
    return request


def _execute_issue_transaction(
    db: Session,
    request: BloodRequest,
    current_user: User,
    staff_id: int,
) -> BloodRequest:
    """Internal helper executing the row-locked issue statements."""
    candidates = get_compatible_units(
        db,
        requested_group=request.blood_group,
        limit=request.quantity,
        today_date=clock.today(),
        for_update=True,
    )

    if len(candidates) < request.quantity:
        db.rollback()
        raise errors.insufficient_stock(
            requested=request.quantity,
            available=len(candidates),
            message=(
                f"Insufficient compatible stock for blood group {request.blood_group}. "
                f"Requested: {request.quantity}, Available: {len(candidates)}."
            ),
        )

    today = clock.today()
    allocated_ids: List[int] = []
    for unit in candidates:
        issue_record = IssueRecord(
            request_id=request.request_id,
            unit_id=unit.unit_id,
            issue_date=today,
            issued_by=staff_id,
        )
        db.add(issue_record)
        unit.status = "issued"
        allocated_ids.append(unit.unit_id)

    request.status = "issued"

    activity_log.record(
        db,
        user_id=current_user.user_id,
        action="issue",
        entity_type="blood_request",
        entity_id=request.request_id,
        details={
            "allocated_unit_ids": allocated_ids,
            "quantity": request.quantity,
            "blood_group": request.blood_group,
            "issued_by": staff_id,
        },
    )

    db.commit()
    db.refresh(request)
    return request


def issue_request(db: Session, request_id: int, current_user: User) -> BloodRequest:
    """
    Atomically issue blood units for an approved request in a single transaction.
    
    Steps (Section 6.7):
    1. Run expire_overdue_units(db, commit=False) in same transaction.
    2. Lock blood_requests row FOR UPDATE; assert status == 'approved'.
    3. Select quantity compatible candidates ordered by expiry_date ASC, unit_id ASC with FOR UPDATE.
    4. If fewer than quantity candidates, abort with 409 INSUFFICIENT_STOCK (rolls back all changes).
    5. For each candidate: create issue_records row, set unit status='issued'.
    6. Set request status='issued'.
    7. Write activity log inside the transaction.
    8. Commit transaction.
    """
    if not current_user.staff_profile:
        raise errors.AppException(
            status_code=400,
            code="STAFF_PROFILE_REQUIRED",
            message="Current user does not have an active staff profile to issue blood units.",
        )
    staff_id = current_user.staff_profile.staff_id

    # 1. Sweep overdue units without committing
    expire_overdue_units(db, commit=False)

    # 2. Lock request row
    request = (
        db.query(BloodRequest)
        .filter(BloodRequest.request_id == request_id)
        .with_for_update()
        .first()
    )
    if not request:
        raise errors.not_found(f"Blood request with ID {request_id} not found.")

    if request.status != "approved":
        raise errors.invalid_status_transition(
            f"Cannot issue request with status '{request.status}'. Only approved requests can be issued."
        )

    # Attempt allocation with one automatic retry if unique constraint race occurs on unit_id
    try:
        return _execute_issue_transaction(db, request, current_user, staff_id)
    except IntegrityError:
        db.rollback()
        # Retry once from clean state
        try:
            expire_overdue_units(db, commit=False)
            req = (
                db.query(BloodRequest)
                .filter(BloodRequest.request_id == request_id)
                .with_for_update()
                .first()
            )
            if not req or req.status != "approved":
                raise errors.invalid_status_transition(
                    f"Request is no longer in approved status during retry."
                )
            return _execute_issue_transaction(db, req, current_user, staff_id)
        except IntegrityError:
            db.rollback()
            raise errors.AppException(
                status_code=409,
                code="CONCURRENT_ALLOCATION_CONFLICT",
                message="A concurrent conflict occurred while allocating blood units. Please retry.",
            )
        except Exception:
            db.rollback()
            raise
    except Exception:
        db.rollback()
        raise
