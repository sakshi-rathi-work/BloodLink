from datetime import date, datetime, time, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.deps import get_db, require_roles
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.schemas.activity_log import ActivityLogListResponse, ActivityLogResponse

router = APIRouter(prefix="/activity-logs", tags=["Activity Logs"])


@router.get("", response_model=ActivityLogListResponse, summary="List activity logs")
def list_activity_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = Query(None),
    entity_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Admin-only: Retrieve system audit activity logs with optional filtering."""
    query = db.query(ActivityLog).join(User)

    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    if entity_type:
        query = query.filter(ActivityLog.entity_type == entity_type)
    if action:
        query = query.filter(ActivityLog.action == action)
    if start_date:
        start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
        query = query.filter(ActivityLog.created_at >= start_dt)
    if end_date:
        end_dt = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
        query = query.filter(ActivityLog.created_at <= end_dt)

    total = query.count()
    items = (
        query.order_by(ActivityLog.created_at.desc(), ActivityLog.log_id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    response_items = [
        ActivityLogResponse(
            log_id=log.log_id,
            user_id=log.user_id,
            username=log.user.username,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            details=log.details,
            created_at=log.created_at,
        )
        for log in items
    ]

    return ActivityLogListResponse(
        items=response_items,
        total=total,
        page=page,
        page_size=page_size,
    )
