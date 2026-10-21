from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.models.activity_log import ActivityLog


def record(
    db: Session,
    user_id: int,
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
) -> ActivityLog:
    """Record an audit trail entry in activity_logs within the current database transaction."""
    log = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.add(log)
    return log
