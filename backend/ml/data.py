from datetime import date, timedelta
from typing import Any, Dict, Optional
import pandas as pd
from sqlalchemy import text
from ml.config import BLOOD_GROUPS, MIN_HISTORY_DAYS


def load_transactions_df(engine_or_conn: Any) -> pd.DataFrame:
    """
    Read transaction records from v_transactions view.
    Columns expected: transaction_type, blood_group, transaction_date
    """
    query = text(
        "SELECT transaction_type, blood_group, transaction_date "
        "FROM v_transactions"
    )
    if hasattr(engine_or_conn, "connect"):
        with engine_or_conn.connect() as conn:
            df = pd.read_sql(query, conn)
    else:
        df = pd.read_sql(query, engine_or_conn)

    if not df.empty:
        df["transaction_date"] = pd.to_datetime(df["transaction_date"]).dt.date
    return df


def prepare_stock_series(
    engine_or_conn: Any,
    today: Optional[date] = None,
    min_history_days: int = MIN_HISTORY_DAYS,
) -> Dict[str, Dict[str, Any]]:
    """
    Build daily cumulative stock series for each of the 8 blood groups.
    Returns:
    {
        blood_group: {
            "status": "ok" | "insufficient_data",
            "series": pd.Series (index: pd.DatetimeIndex, values: stock) or None,
            "history_days": int,
            "reason": str or None,
        }
    }
    """
    if today is None:
        today = date.today()

    history_end = today - timedelta(days=1)
    df = load_transactions_df(engine_or_conn)

    result: Dict[str, Dict[str, Any]] = {}

    if df.empty:
        for bg in BLOOD_GROUPS:
            result[bg] = {
                "status": "insufficient_data",
                "series": None,
                "history_days": 0,
                "reason": "no_transactions",
            }
        return result

    # 1. Global first_date across all blood groups
    first_date = df["transaction_date"].min()
    if pd.isna(first_date) or first_date > history_end:
        for bg in BLOOD_GROUPS:
            result[bg] = {
                "status": "insufficient_data",
                "series": None,
                "history_days": 0,
                "reason": "invalid_date_range",
            }
        return result

    # Full continuous daily date range from first_date to history_end
    full_date_index = pd.date_range(start=first_date, end=history_end, freq="D")
    total_days = len(full_date_index)

    # Check minimum history threshold globally
    global_insufficient = total_days < min_history_days

    for bg in BLOOD_GROUPS:
        bg_df = df[df["blood_group"] == bg]

        # If the blood group has 0 transactions across history, mark insufficient_data
        if bg_df.empty or global_insufficient:
            result[bg] = {
                "status": "insufficient_data",
                "series": None,
                "history_days": total_days if not bg_df.empty else 0,
                "reason": "insufficient_data",
            }
            continue

        # Aggregate counts per transaction_type per date
        # Filter transactions up to history_end
        bg_df = bg_df[bg_df["transaction_date"] <= history_end]

        daily_counts = (
            bg_df.groupby(["transaction_date", "transaction_type"])
            .size()
            .unstack(fill_value=0)
        )

        daily_counts.index = pd.to_datetime(daily_counts.index)
        daily_counts = daily_counts.reindex(full_date_index, fill_value=0)

        donations = daily_counts.get("donation", pd.Series(0, index=full_date_index))
        issues = daily_counts.get("issue", pd.Series(0, index=full_date_index))
        wastage = daily_counts.get("wastage", pd.Series(0, index=full_date_index))

        # Cumulative daily stock: stock(d) = cumsum(donations) - cumsum(issues) - cumsum(wastage)
        stock_series = (donations.cumsum() - issues.cumsum() - wastage.cumsum()).astype(float)
        # Stock cannot be negative; clip at >= 0 for safety
        stock_series = stock_series.clip(lower=0.0)

        result[bg] = {
            "status": "ok",
            "series": stock_series,
            "history_days": total_days,
            "reason": None,
        }

    return result
