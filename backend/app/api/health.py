from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.deps import get_db

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", summary="System and database health check")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint that queries the database to verify connectivity."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
