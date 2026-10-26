from datetime import date
from typing import Literal, Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.core import clock, errors
from app.core.deps import get_db, require_roles
from app.models.user import User
from app.services.reports.csv_writer import generate_csv
from app.services.reports.definitions import REPORT_METADATA, query_report_data
from app.services.reports.pdf_writer import generate_pdf

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/{report_type}", summary="Download exportable report")
def download_report(
    report_type: str,
    format: Literal["csv", "pdf"] = Query(..., description="Report format: csv or pdf"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    """
    Staff & Admin: Download system operational report in CSV or ReportLab PDF format.
    Supported report types: stock, donations, issues, wastage, donors, requests, predictions.
    """
    if report_type not in REPORT_METADATA:
        raise errors.not_found(
            f"Report type '{report_type}' not found. Supported types: {', '.join(REPORT_METADATA.keys())}"
        )

    meta = REPORT_METADATA[report_type]
    rows = query_report_data(report_type, db, start_date=start_date, end_date=end_date)

    today = clock.today()
    today_str = today.strftime("%Y%m%d")
    filename = f"bloodlink_{report_type}_{today_str}.{format}"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Content-Type-Options": "nosniff",
    }

    if format == "csv":
        content = generate_csv(meta["columns"], rows)
        return Response(content=content, media_type="text/csv; charset=utf-8", headers=headers)
    else:  # pdf
        generated_at = today.strftime("%Y-%m-%d")
        content = generate_pdf(meta["title"], meta["columns"], rows, generated_at)
        return Response(content=content, media_type="application/pdf", headers=headers)
