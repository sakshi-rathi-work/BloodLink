from typing import Any, Dict, List
from sqlalchemy import text


def persist_predictions(
    engine_or_conn: Any,
    rows: List[Dict[str, Any]],
) -> None:
    """
    Append prediction rows to shortage_predictions table.
    Supports both SQLAlchemy Engine and Connection.
    Per Decision D6: if Connection is passed, do NOT commit (allows caller to manage transaction / SAVEPOINT).
    If Engine is passed, manage own connection and commit.
    """
    if not rows:
        return

    insert_sql = text("""
        INSERT INTO shortage_predictions (
            run_id, generated_at, blood_group, forecast_date,
            predicted_stock, safe_minimum, is_below_minimum, model_name
        ) VALUES (
            :run_id, :generated_at, :blood_group, :forecast_date,
            :predicted_stock, :safe_minimum, :is_below_minimum, :model_name
        )
    """)

    is_engine = hasattr(engine_or_conn, "connect") and not hasattr(engine_or_conn, "in_transaction")

    if is_engine:
        with engine_or_conn.begin() as conn:
            conn.execute(insert_sql, rows)
    else:
        # Connection passed
        engine_or_conn.execute(insert_sql, rows)
