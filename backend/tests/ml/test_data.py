from datetime import date, timedelta
from unittest.mock import MagicMock
import numpy as np
import pandas as pd
import pytest
from ml.config import BLOOD_GROUPS
from ml.data import prepare_stock_series


def test_prepare_stock_series_empty_db():
    mock_conn = MagicMock()
    # Mocking read_sql returning empty df
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(pd, "read_sql", lambda sql, conn: pd.DataFrame(columns=["transaction_type", "blood_group", "transaction_date"]))
        res = prepare_stock_series(mock_conn, today=date(2026, 10, 23))

    assert len(res) == len(BLOOD_GROUPS)
    for bg in BLOOD_GROUPS:
        assert res[bg]["status"] == "insufficient_data"
        assert res[bg]["series"] is None


def test_prepare_stock_series_with_history():
    today = date(2026, 10, 23)
    start_date = today - timedelta(days=100)

    rows = []
    # 100 days of transactions for A+ and B+
    cur = start_date
    while cur < today:
        rows.append({"transaction_type": "donation", "blood_group": "A+", "transaction_date": cur})
        rows.append({"transaction_type": "donation", "blood_group": "B+", "transaction_date": cur})
        if cur.day % 2 == 0:
            rows.append({"transaction_type": "issue", "blood_group": "A+", "transaction_date": cur})
        cur += timedelta(days=1)

    df = pd.DataFrame(rows)

    mock_conn = MagicMock()
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(pd, "read_sql", lambda sql, conn: df)
        res = prepare_stock_series(mock_conn, today=today, min_history_days=90)

    assert res["A+"]["status"] == "ok"
    assert res["A+"]["history_days"] >= 90
    assert res["A+"]["series"] is not None
    assert np.all(res["A+"]["series"] >= 0.0)

    # AB- had no transactions
    assert res["AB-"]["status"] == "insufficient_data"
