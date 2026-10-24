import pytest
from app.models.shortage_prediction import ShortagePrediction
from ml.pipeline import run_prediction


@pytest.mark.postgres
def test_pipeline_run_prediction(db):
    # Execute prediction pipeline using db connection
    conn = db.connection()
    result = run_prediction(
        engine_or_conn=conn,
        horizon_days=14,
        min_history_days=30,  # lower threshold so test DB passes
        holdout_days=7,
    )

    assert result.run_id is not None
    assert result.horizon_days == 14
    assert isinstance(result.groups_predicted, int)

    # If predictions were generated, verify rows in DB
    if result.groups_predicted > 0:
        rows = db.query(ShortagePrediction).filter_by(run_id=result.run_id).all()
        assert len(rows) == result.groups_predicted * 14
        for r in rows:
            assert float(r.predicted_stock) >= 0.0
