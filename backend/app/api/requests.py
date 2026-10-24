from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core import clock, errors
from app.core.constants import BLOOD_GROUPS, REQUEST_STATUSES, REQUEST_URGENCIES
from app.core.deps import get_db, require_roles
from app.models.blood_request import BloodRequest
from app.models.blood_unit import BloodUnit
from app.models.issue_record import IssueRecord
from app.models.requester import Requester
from app.models.staff import Staff
from app.models.user import User
from app.schemas.request import (
    CandidateUnitResponse,
    IssuedUnitResponse,
    RequestCreate,
    RequestDetailResponse,
    RequestListResponse,
    RequestMatchesResponse,
    RequestResponse,
)
from app.services import activity_log
from app.services.compatibility import COMPATIBILITY
from app.services.issuing import approve_request, issue_request, reject_request
from app.services.matching import get_compatible_units

router = APIRouter(prefix="/requests", tags=["Blood Requests"])


def build_request_detail(db: Session, request: BloodRequest) -> RequestDetailResponse:
    """Build full detail response including issued units with staff and donor unit info."""
    records = (
        db.query(IssueRecord, BloodUnit.blood_group, Staff.name)
        .join(BloodUnit, IssueRecord.unit_id == BloodUnit.unit_id)
        .join(Staff, IssueRecord.issued_by == Staff.staff_id)
        .filter(IssueRecord.request_id == request.request_id)
        .order_by(IssueRecord.issue_id.asc())
        .all()
    )

    issued_units = [
        IssuedUnitResponse(
            issue_id=record.IssueRecord.issue_id,
            unit_id=record.IssueRecord.unit_id,
            blood_group=record.blood_group,
            issue_date=record.IssueRecord.issue_date,
            issued_by=record.IssueRecord.issued_by,
            issued_by_name=record.name,
        )
        for record in records
    ]

    requester_name = request.requester.name if request.requester else ""

    return RequestDetailResponse(
        request_id=request.request_id,
        requester_id=request.requester_id,
        requester_name=requester_name,
        blood_group=request.blood_group,
        quantity=request.quantity,
        urgency=request.urgency,
        status=request.status,
        request_date=request.request_date,
        issued_count=len(issued_units),
        issued_units=issued_units,
    )


@router.post("", response_model=RequestResponse, status_code=status.HTTP_201_CREATED, summary="Submit blood request")
def create_request(
    payload: RequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("requester")),
):
    """Requester only: Create a new blood request in 'pending' status."""
    requester = current_user.requester_profile
    if not requester:
        raise errors.not_found("Requester profile not found for current user.")

    today = clock.today()
    request = BloodRequest(
        requester_id=requester.requester_id,
        blood_group=payload.blood_group,
        quantity=payload.quantity,
        urgency=payload.urgency,
        status="pending",
        request_date=today,
    )
    db.add(request)
    db.flush()

    activity_log.record(
        db,
        user_id=current_user.user_id,
        action="create",
        entity_type="blood_request",
        entity_id=request.request_id,
        details={
            "blood_group": request.blood_group,
            "quantity": request.quantity,
            "urgency": request.urgency,
            "status": "pending",
        },
    )

    db.commit()
    db.refresh(request)

    return RequestResponse(
        request_id=request.request_id,
        requester_id=request.requester_id,
        requester_name=requester.name,
        blood_group=request.blood_group,
        quantity=request.quantity,
        urgency=request.urgency,
        status=request.status,
        request_date=request.request_date,
        issued_count=0,
    )


@router.get("", response_model=RequestListResponse, summary="List blood requests")
def list_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    urgency: Optional[str] = Query(None),
    blood_group: Optional[str] = Query(None),
    requester_id: Optional[int] = Query(None),
    sort: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff", "requester")),
):
    """List blood requests with role-dependent scoping, filtering, and sorting."""
    # Input validation — use alias so query param is still called 'status'
    if status_filter is not None and status_filter not in REQUEST_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status '{status_filter}'. Allowed values: {', '.join(REQUEST_STATUSES)}",
        )
    if urgency is not None and urgency not in REQUEST_URGENCIES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid urgency '{urgency}'. Allowed values: {', '.join(REQUEST_URGENCIES)}",
        )
    if blood_group is not None and blood_group not in BLOOD_GROUPS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid blood group '{blood_group}'. Allowed values: {', '.join(BLOOD_GROUPS)}",
        )
    if sort is not None and sort not in ("priority", "newest"):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid sort '{sort}'. Allowed values: 'priority', 'newest'",
        )

    # Determine default sort and role scope
    if current_user.role == "requester":
        effective_requester_id = (
            current_user.requester_profile.requester_id if current_user.requester_profile else None
        )
        if effective_requester_id is None:
            raise errors.not_found("Requester profile not found for current user.")
        effective_sort = sort or "newest"
    else:
        effective_requester_id = requester_id
        effective_sort = sort or "priority"

    # Base query joined with Requester and IssueRecord count (no N+1)
    query = (
        db.query(
            BloodRequest,
            Requester.name.label("requester_name"),
            func.count(IssueRecord.issue_id).label("issued_count"),
        )
        .join(Requester, BloodRequest.requester_id == Requester.requester_id)
        .outerjoin(IssueRecord, BloodRequest.request_id == IssueRecord.request_id)
        .group_by(BloodRequest.request_id, Requester.name)
    )

    if effective_requester_id:
        query = query.filter(BloodRequest.requester_id == effective_requester_id)
    if status_filter:
        query = query.filter(BloodRequest.status == status_filter)
    if urgency:
        query = query.filter(BloodRequest.urgency == urgency)
    if blood_group:
        query = query.filter(BloodRequest.blood_group == blood_group)

    # Count total matching rows
    count_query = db.query(BloodRequest).filter(
        BloodRequest.requester_id == effective_requester_id if effective_requester_id else True,
        BloodRequest.status == status_filter if status_filter else True,
        BloodRequest.urgency == urgency if urgency else True,
        BloodRequest.blood_group == blood_group if blood_group else True,
    )
    total = count_query.count()

    # Apply sorting
    if effective_sort == "priority":
        # Emergency first, then earliest request_date ASC, tie breaker request_id ASC
        query = query.order_by(
            case((BloodRequest.urgency == "emergency", 0), else_=1).asc(),
            BloodRequest.request_date.asc(),
            BloodRequest.request_id.asc(),
        )
    else:
        # Newest request_date DESC, tie breaker request_id DESC
        query = query.order_by(
            BloodRequest.request_date.desc(),
            BloodRequest.request_id.desc(),
        )

    results = query.offset((page - 1) * page_size).limit(page_size).all()

    items = [
        RequestResponse(
            request_id=row.BloodRequest.request_id,
            requester_id=row.BloodRequest.requester_id,
            requester_name=row.requester_name,
            blood_group=row.BloodRequest.blood_group,
            quantity=row.BloodRequest.quantity,
            urgency=row.BloodRequest.urgency,
            status=row.BloodRequest.status,
            request_date=row.BloodRequest.request_date,
            issued_count=row.issued_count,
        )
        for row in results
    ]

    return RequestListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{request_id}", response_model=RequestDetailResponse, summary="Get blood request detail")
def get_request_detail(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff", "requester")),
):
    """Retrieve full details of a blood request. Requesters can only access their own (returns 404 otherwise)."""
    request = db.query(BloodRequest).filter(BloodRequest.request_id == request_id).first()
    if not request:
        raise errors.not_found(f"Blood request with ID {request_id} not found.")

    # Isolation check: Requester accessing another requester's request returns 404 (never 403)
    if current_user.role == "requester":
        my_req_id = current_user.requester_profile.requester_id if current_user.requester_profile else None
        if request.requester_id != my_req_id:
            raise errors.not_found(f"Blood request with ID {request_id} not found.")

    return build_request_detail(db, request)


@router.get("/{request_id}/matches", response_model=RequestMatchesResponse, summary="Get matching compatible units")
def get_request_matches(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff/Admin only: Inspect candidate compatible units ranked nearest-expiry-first (read-only)."""
    request = db.query(BloodRequest).filter(BloodRequest.request_id == request_id).first()
    if not request:
        raise errors.not_found(f"Blood request with ID {request_id} not found.")

    today = clock.today()
    compatible_groups = COMPATIBILITY.get(request.blood_group, [])

    # Fetch all candidate units without taking locks
    all_units = get_compatible_units(
        db,
        requested_group=request.blood_group,
        today_date=today,
        for_update=False,
    )

    available_count = len(all_units)
    sufficient = available_count >= request.quantity
    preview_ids = [u.unit_id for u in all_units[: request.quantity]]

    candidate_items = [
        CandidateUnitResponse(
            unit_id=u.unit_id,
            blood_group=u.blood_group,
            collection_date=u.collection_date,
            expiry_date=u.expiry_date,
            days_to_expiry=(u.expiry_date - today).days,
        )
        for u in all_units
    ]

    return RequestMatchesResponse(
        request_id=request.request_id,
        requested_group=request.blood_group,
        quantity=request.quantity,
        compatible_groups=compatible_groups,
        available_compatible_count=available_count,
        sufficient=sufficient,
        allocation_preview_unit_ids=preview_ids,
        units=candidate_items,
    )


@router.post("/{request_id}/approve", response_model=RequestDetailResponse, summary="Approve blood request")
def approve_blood_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff/Admin only: Transition pending blood request to approved."""
    request = approve_request(db, request_id, current_user)
    return build_request_detail(db, request)


@router.post("/{request_id}/reject", response_model=RequestDetailResponse, summary="Reject blood request")
def reject_blood_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff/Admin only: Transition pending or approved blood request to rejected."""
    request = reject_request(db, request_id, current_user)
    return build_request_detail(db, request)


@router.post("/{request_id}/issue", response_model=RequestDetailResponse, summary="Issue blood units for request")
def issue_blood_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """Staff/Admin only: Atomically issue blood units nearest-expiry-first for an approved request."""
    request = issue_request(db, request_id, current_user)
    return build_request_detail(db, request)


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete blood request")
def delete_blood_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Admin only: Delete blood request. Blocked with 409 if status is 'issued' or referenced."""
    request = db.query(BloodRequest).filter(BloodRequest.request_id == request_id).first()
    if not request:
        raise errors.not_found(f"Blood request with ID {request_id} not found.")

    if request.status == "issued":
        raise errors.referenced_record("Cannot delete a blood request that has already been issued.")

    req_bg = request.blood_group
    req_qty = request.quantity
    req_status = request.status

    try:
        db.delete(request)
        db.flush()

        activity_log.record(
            db,
            user_id=current_user.user_id,
            action="delete",
            entity_type="blood_request",
            entity_id=request_id,
            details={"blood_group": req_bg, "quantity": req_qty, "status": req_status},
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise errors.referenced_record(
            f"Blood request {request_id} cannot be deleted because it is referenced by other records."
        )

    return None
