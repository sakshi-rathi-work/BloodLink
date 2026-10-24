import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.activity_log import ActivityLog


def test_predictions_endpoints_rbac(client: TestClient, requester_client: TestClient):
    """Requesters get 403 and unauthenticated gets 401 on prediction endpoints."""
    endpoints = [
        ("POST", "/api/predictions/run", {"horizon_days": 30}),
        ("GET", "/api/predictions/latest", None),
        ("GET", "/api/predictions/alerts", None),
        ("GET", "/api/predictions/evaluation", None),
    ]

    for method, path, body in endpoints:
        if method == "POST":
            # Unauth
            res = client.post(path, json=body)
            assert res.status_code == 401
            # Requester
            res_req = requester_client.post(path, json=body)
            assert res_req.status_code == 403
        else:
            # Unauth
            res = client.get(path)
            assert res.status_code == 401
            # Requester
            res_req = requester_client.get(path)
            assert res_req.status_code == 403


def test_prediction_run_horizon_validation(staff_client: TestClient):
    """Horizon days must be between 7 and 30."""
    res_low = staff_client.post("/api/predictions/run", json={"horizon_days": 5})
    assert res_low.status_code == 422

    res_high = staff_client.post("/api/predictions/run", json={"horizon_days": 45})
    assert res_high.status_code == 422


@pytest.mark.postgres
def test_prediction_run_and_retrieve_flow(staff_client: TestClient, db: Session):
    """Test full prediction flow: run -> latest -> alerts -> evaluation."""
    # 1. Trigger prediction run
    res = staff_client.post("/api/predictions/run", json={"horizon_days": 14})
    assert res.status_code == 200
    data = res.json()
    assert "run_id" in data
    assert data["horizon_days"] == 14
    assert isinstance(data["groups_predicted"], int)

    # Verify activity log
    log = db.query(ActivityLog).filter_by(entity_type="prediction_run", action="create").first()
    assert log is not None

    # 2. Get latest predictions
    res_latest = staff_client.get("/api/predictions/latest")
    assert res_latest.status_code == 200
    latest_data = res_latest.json()
    if data["groups_predicted"] > 0:
        assert latest_data["run_id"] == data["run_id"]
        assert "predictions" in latest_data
        assert "skipped_groups" in latest_data
    else:
        assert latest_data["run_id"] is None
        assert latest_data["predictions"] == []

    # 3. Get alerts
    res_alerts = staff_client.get("/api/predictions/alerts?within_days=14")
    assert res_alerts.status_code == 200
    alerts = res_alerts.json()
    assert isinstance(alerts, list)

    # 4. Get evaluation
    res_eval = staff_client.get("/api/predictions/evaluation")
    assert res_eval.status_code == 200
    eval_dict = res_eval.json()
    assert "groups" in eval_dict


@pytest.mark.postgres
def test_predictions_with_populated_predictions(staff_client: TestClient, db: Session):
    """Test GET /latest and GET /alerts when shortage_predictions table has rows."""
    import uuid
    from datetime import datetime, timezone, timedelta
    from app.core import clock
    from app.models.shortage_prediction import ShortagePrediction

    test_run_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    today = clock.today()

    pred = ShortagePrediction(
        run_id=test_run_id,
        generated_at=now,
        blood_group="A+",
        forecast_date=today + timedelta(days=2),
        predicted_stock=5.0,
        safe_minimum=15,
        is_below_minimum=True,
        model_name="linear_regression",
    )
    db.add(pred)
    db.commit()

    # Test latest
    res_latest = staff_client.get("/api/predictions/latest")
    assert res_latest.status_code == 200
    latest = res_latest.json()
    assert latest["run_id"] == str(test_run_id)
    assert len(latest["predictions"]) >= 1

    # Test alerts
    res_alerts = staff_client.get("/api/predictions/alerts?within_days=7")
    assert res_alerts.status_code == 200
    alerts = res_alerts.json()
    assert any(a["blood_group"] == "A+" for a in alerts)

