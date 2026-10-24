from datetime import date, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core import clock
from app.models.blood_unit import BloodUnit
from app.models.shortage_prediction import ShortagePrediction


def get_shortage_alerts(
    db: Session,
    within_days: int = 30,
    current_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Compute blood shortage alerts from the latest prediction run.
    A group is alerted if any forecast day within `within_days` of the run's
    first forecast date has `is_below_minimum = True`.
    Sorted by days_until_shortage ascending.
    """
    if current_date is None:
        current_date = clock.today()

    # 1. Find latest run_id ordered by generated_at DESC
    latest_run = (
        db.query(ShortagePrediction.run_id)
        .order_by(ShortagePrediction.generated_at.desc())
        .first()
    )

    if not latest_run:
        return []

    run_id = latest_run[0]

    # 2. Get first forecast date for this run
    first_forecast_date = (
        db.query(func.min(ShortagePrediction.forecast_date))
        .filter(ShortagePrediction.run_id == run_id)
        .scalar()
    )

    if not first_forecast_date:
        return []

    max_forecast_date = first_forecast_date + timedelta(days=within_days)

    # 3. Fetch predictions for this run within the cutoff where is_below_minimum is True
    shortage_rows = (
        db.query(ShortagePrediction)
        .filter(
            ShortagePrediction.run_id == run_id,
            ShortagePrediction.forecast_date <= max_forecast_date,
            ShortagePrediction.is_below_minimum == True,  # noqa: E712
        )
        .order_by(ShortagePrediction.forecast_date.asc())
        .all()
    )

    if not shortage_rows:
        return []

    # 4. Group by blood group
    groups_dict: Dict[str, Dict[str, Any]] = {}
    for row in shortage_rows:
        bg = row.blood_group
        if bg not in groups_dict:
            days_until = max(0, (row.forecast_date - current_date).days)
            groups_dict[bg] = {
                "blood_group": bg,
                "first_shortage_date": row.forecast_date.isoformat(),
                "days_until_shortage": days_until,
                "min_predicted_stock": float(row.predicted_stock),
                "safe_minimum": row.safe_minimum,
            }
        else:
            if float(row.predicted_stock) < groups_dict[bg]["min_predicted_stock"]:
                groups_dict[bg]["min_predicted_stock"] = float(row.predicted_stock)

    # 5. Populate current_stock (available unexpired units now)
    results: List[Dict[str, Any]] = []
    for bg, alert_data in groups_dict.items():
        curr_stock = (
            db.query(func.count(BloodUnit.unit_id))
            .filter(
                BloodUnit.blood_group == bg,
                BloodUnit.status == "available",
                BloodUnit.expiry_date >= current_date,
            )
            .scalar()
            or 0
        )
        alert_data["current_stock"] = curr_stock
        results.append(alert_data)

    # 6. Sort by days_until_shortage ascending, then blood_group
    results.sort(key=lambda x: (x["days_until_shortage"], x["blood_group"]))
    return results


def get_predicted_alert_count(db: Session) -> Optional[int]:
    """
    Return count of shortage alerts from the latest prediction run,
    or None if no prediction run exists (for Dashboard summary).
    """
    latest_run = (
        db.query(ShortagePrediction.run_id)
        .order_by(ShortagePrediction.generated_at.desc())
        .first()
    )
    if not latest_run:
        return None

    alerts = get_shortage_alerts(db, within_days=30)
    return len(alerts)
