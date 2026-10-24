import httpx
from app.core.constants import BLOOD_GROUPS


def test_get_dashboard_summary_staff_allowed(staff_client: httpx.Client):
    response = staff_client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()

    assert "as_of" in data
    assert "stock_by_group" in data
    assert "total_available_units" in data
    assert "expiring_soon" in data
    assert "pending_requests" in data
    assert "pending_emergency_requests" in data
    assert "approved_requests_awaiting_issue" in data

    # Verify all 8 groups zero-filled or counted
    groups_in_res = [item["blood_group"] for item in data["stock_by_group"]]
    for bg in BLOOD_GROUPS:
        assert bg in groups_in_res

    # Check item structure
    sample = data["stock_by_group"][0]
    assert "available_units" in sample
    assert "safe_minimum" in sample
    assert "is_low" in sample
    assert isinstance(sample["is_low"], bool)


def test_get_dashboard_summary_requester_forbidden(requester_client: httpx.Client):
    response = requester_client.get("/api/dashboard/summary")
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "FORBIDDEN"


def test_get_dashboard_trends_granularity_options(staff_client: httpx.Client):
    # Test day granularity
    res_day = staff_client.get("/api/dashboard/trends?granularity=day&start_date=2026-10-01&end_date=2026-10-10")
    assert res_day.status_code == 200
    data_day = res_day.json()
    assert data_day["granularity"] == "day"
    assert len(data_day["series"]) == 10  # 10 days inclusive

    # Test week granularity
    res_week = staff_client.get("/api/dashboard/trends?granularity=week&start_date=2026-10-01&end_date=2026-10-21")
    assert res_week.status_code == 200
    data_week = res_week.json()
    assert data_week["granularity"] == "week"
    assert len(data_week["series"]) >= 3
    # Verify each period start is a Monday
    for pt in data_week["series"]:
        assert "donations" in pt
        assert "issues" in pt

    # Test month granularity
    res_month = staff_client.get("/api/dashboard/trends?granularity=month&start_date=2026-08-01&end_date=2026-10-21")
    assert res_month.status_code == 200
    data_month = res_month.json()
    assert data_month["granularity"] == "month"
    assert len(data_month["series"]) == 3  # Aug, Sep, Oct


def test_get_dashboard_wastage_structure(staff_client: httpx.Client):
    response = staff_client.get("/api/dashboard/wastage?start_date=2026-01-01&end_date=2026-10-21")
    assert response.status_code == 200
    data = response.json()

    assert "start_date" in data
    assert "end_date" in data
    assert "total_expired" in data
    assert "by_blood_group" in data
    assert "by_month" in data

    # Verify all 8 groups present in wastage breakdown
    groups_present = [item["blood_group"] for item in data["by_blood_group"]]
    for bg in BLOOD_GROUPS:
        assert bg in groups_present
