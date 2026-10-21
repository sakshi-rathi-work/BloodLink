from datetime import date
from app.services.eligibility import check_donor_eligibility


def test_eligibility_age_boundaries():
    today = date(2026, 10, 21)

    # Age 17: born 2009-10-22 (not yet 18) -> fails
    res_17 = check_donor_eligibility(
        dob=date(2009, 10, 22),
        weight=55.0,
        current_date=today,
    )
    assert res_17["eligible"] is False
    assert "AGE_BELOW_MIN" in res_17["reasons"]

    # Age 18: born 2008-10-21 (exactly 18 today) -> passes
    res_18 = check_donor_eligibility(
        dob=date(2008, 10, 21),
        weight=55.0,
        current_date=today,
    )
    assert res_18["eligible"] is True
    assert res_18["age"] == 18

    # Age 65: born 1961-10-21 (exactly 65 today) -> passes
    res_65 = check_donor_eligibility(
        dob=date(1961, 10, 21),
        weight=60.0,
        current_date=today,
    )
    assert res_65["eligible"] is True
    assert res_65["age"] == 65

    # Age 66: born 1960-10-20 -> fails
    res_66 = check_donor_eligibility(
        dob=date(1960, 10, 20),
        weight=60.0,
        current_date=today,
    )
    assert res_66["eligible"] is False
    assert "AGE_ABOVE_MAX" in res_66["reasons"]


def test_eligibility_weight_boundaries():
    today = date(2026, 10, 21)
    dob = date(1995, 5, 10)  # age ~31

    # Weight 49.9 kg -> fails
    res_under = check_donor_eligibility(
        dob=dob,
        weight=49.9,
        current_date=today,
    )
    assert res_under["eligible"] is False
    assert "WEIGHT_BELOW_MIN" in res_under["reasons"]

    # Weight 50.0 kg -> passes
    res_min = check_donor_eligibility(
        dob=dob,
        weight=50.0,
        current_date=today,
    )
    assert res_min["eligible"] is True


def test_eligibility_donation_gap():
    today = date(2026, 10, 21)
    dob = date(1995, 5, 10)

    # Never donated (last_donation_date = None) -> passes
    res_never = check_donor_eligibility(
        dob=dob,
        weight=55.0,
        last_donation_date=None,
        current_date=today,
    )
    assert res_never["eligible"] is True
    assert res_never["next_eligible_date"] is None

    # Donated 89 days ago (2026-07-24) -> fails
    res_89 = check_donor_eligibility(
        dob=dob,
        weight=55.0,
        last_donation_date=date(2026, 7, 24),
        current_date=today,
    )
    assert res_89["eligible"] is False
    assert "DONATION_GAP_NOT_MET" in res_89["reasons"]
    assert res_89["next_eligible_date"] == date(2026, 10, 22)

    # Donated 90 days ago (2026-07-23) -> passes
    res_90 = check_donor_eligibility(
        dob=dob,
        weight=55.0,
        last_donation_date=date(2026, 7, 23),
        current_date=today,
    )
    assert res_90["eligible"] is True
    assert res_90["next_eligible_date"] == date(2026, 10, 21)


def test_eligibility_multiple_reasons():
    today = date(2026, 10, 21)

    # Age 16, weight 45kg, donated 10 days ago
    res = check_donor_eligibility(
        dob=date(2010, 1, 1),
        weight=45.0,
        last_donation_date=date(2026, 10, 11),
        current_date=today,
    )
    assert res["eligible"] is False
    assert set(res["reasons"]) == {"AGE_BELOW_MIN", "WEIGHT_BELOW_MIN", "DONATION_GAP_NOT_MET"}
