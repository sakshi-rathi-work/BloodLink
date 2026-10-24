from datetime import date
from typing import Any, Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.constants import BLOOD_GROUPS
from app.models.blood_request import BloodRequest
from app.models.blood_unit import BloodUnit
from app.models.donor import Donor
from app.models.issue_record import IssueRecord
from app.models.requester import Requester
from app.models.shortage_prediction import ShortagePrediction
from app.models.staff import Staff
from app.services.inventory import get_stock_by_blood_group

REPORT_METADATA = {
    "stock": {
        "title": "Inventory Stock Summary",
        "columns": ["blood_group", "available_units", "safe_minimum", "status"],
        "date_filtered": False,
    },
    "donations": {
        "title": "Donation Collections Log",
        "columns": [
            "unit_id",
            "donor_id",
            "donor_name",
            "blood_group",
            "collection_date",
            "expiry_date",
            "status",
        ],
        "date_filtered": True,
    },
    "issues": {
        "title": "Blood Issuance Log",
        "columns": [
            "issue_id",
            "request_id",
            "requester_name",
            "unit_id",
            "blood_group",
            "issue_date",
            "issued_by_name",
        ],
        "date_filtered": True,
    },
    "wastage": {
        "title": "Expired Units Wastage Audit",
        "columns": ["unit_id", "blood_group", "collection_date", "expiry_date"],
        "date_filtered": True,
    },
    "donors": {
        "title": "Registered Donors Directory",
        "columns": [
            "donor_id",
            "name",
            "blood_group",
            "phone",
            "address",
            "last_donation_date",
            "donation_count",
            "is_regular",
        ],
        "date_filtered": False,
    },
    "requests": {
        "title": "Blood Requests & Fulfillment Log",
        "columns": [
            "request_id",
            "requester_name",
            "blood_group",
            "quantity",
            "urgency",
            "status",
            "request_date",
        ],
        "date_filtered": True,
    },
    "predictions": {
        "title": "Shortage Prediction Forecast",
        "columns": [
            "blood_group",
            "model_name",
            "forecast_date",
            "predicted_stock",
            "safe_minimum",
            "is_below_minimum",
        ],
        "date_filtered": False,
    },
}


def query_report_data(
    report_type: str,
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[List[Any]]:
    """Query and return tabular data rows for a given report type."""
    rows: List[List[Any]] = []

    if report_type == "stock":
        stock_map = get_stock_by_blood_group(db)
        for bg in BLOOD_GROUPS:
            avail = stock_map.get(bg, 0)
            safe_min = settings.get_safe_minimum(bg)
            status = "LOW" if avail < safe_min else "OK"
            rows.append([bg, avail, safe_min, status])

    elif report_type == "donations":
        query = db.query(BloodUnit, Donor.name).join(
            Donor, BloodUnit.donor_id == Donor.donor_id
        )
        if start_date:
            query = query.filter(BloodUnit.collection_date >= start_date)
        if end_date:
            query = query.filter(BloodUnit.collection_date <= end_date)
        units = query.order_by(
            BloodUnit.collection_date.desc(), BloodUnit.unit_id.desc()
        ).all()
        for unit, donor_name in units:
            rows.append(
                [
                    unit.unit_id,
                    unit.donor_id,
                    donor_name,
                    unit.blood_group,
                    unit.collection_date.isoformat(),
                    unit.expiry_date.isoformat(),
                    unit.status,
                ]
            )

    elif report_type == "issues":
        query = (
            db.query(
                IssueRecord,
                Requester.name.label("requester_name"),
                BloodUnit.blood_group,
                Staff.name.label("staff_name"),
            )
            .join(BloodRequest, IssueRecord.request_id == BloodRequest.request_id)
            .join(Requester, BloodRequest.requester_id == Requester.requester_id)
            .join(BloodUnit, IssueRecord.unit_id == BloodUnit.unit_id)
            .join(Staff, IssueRecord.issued_by == Staff.staff_id)
        )
        if start_date:
            query = query.filter(IssueRecord.issue_date >= start_date)
        if end_date:
            query = query.filter(IssueRecord.issue_date <= end_date)
        issues = query.order_by(
            IssueRecord.issue_date.desc(), IssueRecord.issue_id.desc()
        ).all()
        for issue, req_name, bg, staff_name in issues:
            rows.append(
                [
                    issue.issue_id,
                    issue.request_id,
                    req_name,
                    issue.unit_id,
                    bg,
                    issue.issue_date.isoformat(),
                    staff_name,
                ]
            )

    elif report_type == "wastage":
        query = db.query(BloodUnit).filter(BloodUnit.status == "expired")
        if start_date:
            query = query.filter(BloodUnit.expiry_date >= start_date)
        if end_date:
            query = query.filter(BloodUnit.expiry_date <= end_date)
        expired_units = query.order_by(
            BloodUnit.expiry_date.desc(), BloodUnit.unit_id.desc()
        ).all()
        for u in expired_units:
            rows.append(
                [
                    u.unit_id,
                    u.blood_group,
                    u.collection_date.isoformat(),
                    u.expiry_date.isoformat(),
                ]
            )

    elif report_type == "donors":
        donors = db.query(Donor).order_by(Donor.donor_id.asc()).all()
        for d in donors:
            donation_count = (
                db.query(func.count(BloodUnit.unit_id))
                .filter(BloodUnit.donor_id == d.donor_id)
                .scalar()
                or 0
            )
            is_regular = donation_count >= settings.REGULAR_DONOR_MIN_DONATIONS
            rows.append(
                [
                    d.donor_id,
                    d.name,
                    d.blood_group,
                    d.phone,
                    d.address,
                    d.last_donation_date.isoformat() if d.last_donation_date else "—",
                    donation_count,
                    "Yes" if is_regular else "No",
                ]
            )

    elif report_type == "requests":
        query = db.query(BloodRequest, Requester.name).join(
            Requester, BloodRequest.requester_id == Requester.requester_id
        )
        if start_date:
            query = query.filter(BloodRequest.request_date >= start_date)
        if end_date:
            query = query.filter(BloodRequest.request_date <= end_date)
        requests = query.order_by(
            BloodRequest.request_date.desc(), BloodRequest.request_id.desc()
        ).all()
        for req, req_name in requests:
            rows.append(
                [
                    req.request_id,
                    req_name,
                    req.blood_group,
                    req.quantity,
                    req.urgency,
                    req.status,
                    req.request_date.isoformat(),
                ]
            )

    elif report_type == "predictions":
        latest_run = (
            db.query(ShortagePrediction.run_id)
            .order_by(ShortagePrediction.generated_at.desc())
            .first()
        )
        if latest_run:
            preds = (
                db.query(ShortagePrediction)
                .filter(ShortagePrediction.run_id == latest_run[0])
                .order_by(
                    ShortagePrediction.forecast_date.asc(),
                    ShortagePrediction.blood_group.asc(),
                )
                .all()
            )
            for p in preds:
                rows.append(
                    [
                        p.blood_group,
                        p.model_name,
                        p.forecast_date.isoformat(),
                        float(p.predicted_stock),
                        p.safe_minimum,
                        "YES" if p.is_below_minimum else "NO",
                    ]
                )

    return rows
