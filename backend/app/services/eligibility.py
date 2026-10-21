from datetime import date, timedelta
from typing import Any, Dict, List, Optional
from app.core import clock
from app.core.config import settings


def calculate_age(dob: date, current_date: date) -> int:
    """Calculate full years between date of birth and current date."""
    age = current_date.year - dob.year
    if (current_date.month, current_date.day) < (dob.month, dob.day):
        age -= 1
    return age


def check_donor_eligibility(
    dob: date,
    weight: float,
    last_donation_date: Optional[date] = None,
    current_date: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Evaluate donor eligibility against business rules (Section 6.2).
    
    Rules:
    - MIN_DONOR_AGE <= age <= MAX_DONOR_AGE (inclusive: 18-65)
    - weight >= MIN_DONOR_WEIGHT_KG (50 kg)
    - last_donation_date is None OR today - last_donation_date >= MIN_DONATION_GAP_DAYS (90 days)
    """
    if current_date is None:
        current_date = clock.today()

    age = calculate_age(dob, current_date)
    reasons: List[str] = []

    if age < settings.MIN_DONOR_AGE:
        reasons.append("AGE_BELOW_MIN")
    elif age > settings.MAX_DONOR_AGE:
        reasons.append("AGE_ABOVE_MAX")

    if float(weight) < float(settings.MIN_DONOR_WEIGHT_KG):
        reasons.append("WEIGHT_BELOW_MIN")

    next_eligible_date: Optional[date] = None
    if last_donation_date is not None:
        next_eligible_date = last_donation_date + timedelta(days=settings.MIN_DONATION_GAP_DAYS)
        days_since = (current_date - last_donation_date).days
        if days_since < settings.MIN_DONATION_GAP_DAYS:
            reasons.append("DONATION_GAP_NOT_MET")

    is_eligible = len(reasons) == 0

    return {
        "eligible": is_eligible,
        "reasons": reasons,
        "age": age,
        "weight": float(weight),
        "last_donation_date": last_donation_date,
        "next_eligible_date": next_eligible_date,
    }
